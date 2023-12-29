from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from yt_dlp import YoutubeDL
from pathlib import Path
from shutil import move
from pydub import AudioSegment
from pydantic import BaseModel
from math import log10
import demucs.separate
import os
import uuid
import re

app = FastAPI()

downloads_dir = "downloads"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)
app.mount("/downloads", StaticFiles(directory=downloads_dir), name="downloads")
templates = Jinja2Templates(directory="templates")
MODEL = "htdemucs_6s"


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    filename = filename.replace(' ', '_')

    return filename


def download_audio(url, start_time="0", end_time="0"):
    def progress_hook(d):
        if d["status"] == "finished":
            print(f"\nDownloaded to  {d['filename']}")

    ydl_options = {
        "format": "mp3/bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        ],
        "postprocessor_args": [
            "-ss", start_time,
            "-to", end_time,
        ],
        "outtmpl": "%(id)s.%(ext)s",
        "progress_hooks": [progress_hook],
    }

    with YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url=url, download=False)
        video_title = info.get("id", None)
        ext = "mp3"

        output_filename = f"{video_title}.{ext}" if video_title else None

        error_code = ydl.download(url)

        return output_filename if error_code == 0 else None


def separate_audio(file_name):
    downloads_dir = "downloads"

    demucs.separate.main(["--mp3", "-n", MODEL, "-o", downloads_dir, file_name])

    path = "/".join([downloads_dir, MODEL, Path(file_name).stem])
    return list_files(file_name, path)


def list_files(original_file, downloads_path):
    main_audio = f'<label class="song-label">{Path(original_file).stem}<br><audio class="synced-audio main-audio w-full" controls><source src="/{downloads_path}/{original_file}" type="audio/mp3">Your browser does not support the audio element.</audio>'

    files = os.listdir(f"./{downloads_path}")
    stem_audios = [
        f'<label class="stem-label">{Path(file).stem}</label><br><audio id="{file}" class="synced-audio stem-audio w-full"><source src="/{downloads_path}/{file}" type="audio/mp3">Your browser does not support the audio element.</audio><input type="range" min="0" max="1" step="0.05" class="volume-slider w-full" data-audio="{file}" value="1">'
        for file in files if file != original_file
    ]

    return "<div>" + "<br>".join([main_audio] + stem_audios) + "</div>"


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process")
async def process(url: str = Form(...), start_time: str = Form(...), end_time: str = Form(...)):
    file_name = download_audio(url, start_time, end_time)
    separated_files = separate_audio(file_name)
    # move original audio file to the same directory as the splitted audio files
    move(f"./{file_name}", f"./downloads/{MODEL}/{Path(file_name).stem}/{file_name}")
    return {"file_name": Path(file_name).stem, "separated_files": separated_files}


class VolumeInfo(BaseModel):
    filename: str
    gain: float


@app.post("/download")
async def download(volumes: str = Form(...)):
    volumes = eval(volumes)
    combined = None

    for stem in volumes:
        for file, gain in stem.items():
            audio = AudioSegment.from_file(file, format="mp3")

            gain_db = -1000 if gain == 0 else 20 * log10(gain)
            audio = audio.apply_gain(gain_db)

            combined = audio if combined is None else combined.overlay(audio)
    if combined is not None:
        targer_dir = "./downloads/mixes"
        random_filename = f"{targer_dir}/{str(uuid.uuid4())}.mp3"
        Path(targer_dir).mkdir(parents=True, exist_ok=True)
        combined.export(f"{random_filename}", format="mp3")
        return FileResponse(random_filename,
                            headers={"Content-Disposition": f"attachment; filename={Path(random_filename).name}"})
