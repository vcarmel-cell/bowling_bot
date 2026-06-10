"""
video_processor.py
מוריד סרטון מ-GitHub, מחליף את הסאונד במוזיקה חופשית, ומעלה לאחסון זמני.
"""

import os
import random
import subprocess
import tempfile
import requests
import cloudinary
import cloudinary.uploader
from pathlib import Path

FFMPEG = r"C:\Users\Next1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"

# מוזיקה ספורטיבית/אנרגטית חינמית (SoundHelix — Public Domain)
MUSIC_TRACKS = [f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{i}.mp3" for i in range(1, 18)]

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


def is_video_url(url: str) -> bool:
    return any(url.lower().split("?")[0].endswith(ext) for ext in VIDEO_EXTENSIONS)


def _download(url: str, suffix: str) -> Path:
    """מוריד קובץ לתיקיית temp ומחזיר את הנתיב."""
    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    for chunk in resp.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()
    return Path(tmp.name)


def _upload_video(file_path: Path) -> str:
    """מעלה סרטון ל-Cloudinary ומחזיר URL ציבורי."""
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
    )
    result = cloudinary.uploader.upload(
        str(file_path),
        resource_type="video",
        folder="bowling_bot",
    )
    return result["secure_url"]


def process_video(video_url: str) -> str:
    """
    מוריד סרטון, מחליף סאונד במוזיקה חופשית, ומחזיר URL ציבורי לסרטון המעובד.
    """
    music_url = random.choice(MUSIC_TRACKS)

    video_path = _download(video_url, ".mp4")
    music_path = _download(music_url, ".mp3")
    output_path = Path(tempfile.mktemp(suffix="_processed.mp4"))

    try:
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-i", str(video_path),
                "-i", str(music_path),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )

        public_url = _upload_video(output_path)
        return public_url

    finally:
        for p in (video_path, music_path, output_path):
            try:
                p.unlink()
            except Exception:
                pass
