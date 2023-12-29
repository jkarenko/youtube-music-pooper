# Youtube Audio Pooper

This application allows you to download audio from YouTube videos, separate the audio into stems, and adjust the volume of each stem to create a custom mix.
Installation

## Requirements

You need Python (tested on 3.11) and additionally Poetry for dependency management.

```bash
pip install poetry
```

ffmpeg is also required for audio processing. On macOS, you can install it with Homebrew.

```bash
brew install ffmpeg
```

On Windows, you can download it from the [official website](https://ffmpeg.org/download.html).

## Setup

Clone the repository and install the dependencies.

```bash
poetry install
```

## Run

### Without Docker

```bash
poetry run uvicorn youtube_music_pooper.main:app --reload
```

### With Docker

```bash
docker build -t youtube_music_pooper .
docker run --rm -p 8000:8000 youtube_music_pooper
```


The application will be available at http://localhost:8000.


## Usage

1. Open the application in your web browser.
2. Paste the URL of a YouTube video into the "Paste YouTube URL" field.
3. Click the "Set Start" and "Set End" buttons to select the portion of the video you want to use.
4. Click the "Process" button. The application will download the audio, separate it into stems, and display audio players for each stem.
5. Adjust the volume of each stem using the sliders.
6. Click the "Download Mix" button to download your custom mix.
API Endpoints

- GET /: Returns the main page of the application.
- POST /process: Accepts a form with url, start_time, and end_time fields. Returns the separated audio files.
- POST /download: Accepts a form with a volumes field, which should be a JSON string representing a list of dictionaries. Each dictionary should have a file path as the key and a volume level as the value. Returns the combined audio file.
