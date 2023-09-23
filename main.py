from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from yt_dlp import YoutubeDL
from pathlib import Path
from shutil import move
import demucs.separate
import os

app = FastAPI()
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")
templates = Jinja2Templates(directory="templates")
MODEL = "htdemucs_ft"


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
        "outtmpl": "%(title)s.%(ext)s",
        "progress_hooks": [progress_hook],
    }

    with YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url=url, download=False)
        video_title = info.get("title", None)
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
    main_audio = f'{original_file}<br><audio class="synced-audio main-audio" controls><source src="/{downloads_path}/{original_file}" type="audio/mp3">Your browser does not support the audio element.</audio>'

    files = os.listdir(f"./{downloads_path}")
    stem_audios = [
        f'{file}<br><audio id="{file}" class="synced-audio stem-audio"><source src="/{downloads_path}/{file}" type="audio/mp3">Your browser does not support the audio element.</audio><input type="range" min="0" max="1" step="0.05" class="volume-slider" data-audio="{file}" value="1">'
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
    return {"file_name": file_name, "separated_files": separated_files}
