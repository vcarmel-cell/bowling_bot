import base64
import os
import subprocess
import tempfile
import requests
import anthropic
from datetime import datetime
from pathlib import Path

FFMPEG = r"C:\Users\Next1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}

SYSTEM_PROMPT = """אתה מנהל תוכן מקצועי לחשבון אינסטגרם בנושא באולינג בעברית.
הפוסטים שלך:
- כתובים בעברית תקנית וקולחת
- אנרגטיים, מעוררי עניין ומתחברים לקהל
- כתובים בטקסט רגיל בלבד — ללא כוכביות, ללא hashtag בתוך הטקסט, ללא markdown
- מסתיימים תמיד ב-6 עד 8 האשטאגים רלוונטיים בשורה נפרדת (מיקס עברית ואנגלית)
- לא יותר מ-250 מילים — חובה לסיים את הטקסט לפני ה-hashtags"""

PROMPTS = {
    "tip": """המשפט הראשון חייב להתייחס ישירות למה שרואים בתמונה.
לאחר מכן כתוב טיפ מקצועי לשיפור משחק באולינג — ספציפי, מעשי וניתן ליישום מיד.
התחל עם ואמוג'י מתאים.""",

    "fact": """המשפט הראשון חייב להתייחס ישירות למה שרואים בתמונה.
לאחר מכן כתוב עובדה מפתיעה ומרתקת על ספורט הבאולינג — משהו שרוב האנשים לא יודעים.
התחל בשאלה רטורית קצרה.""",

    "motivation": """המשפט הראשון חייב להתייחס ישירות למה שרואים בתמונה.
לאחר מכן כתוב פוסט מוטיבציה ועידוד — השתמש בקשר בין הספורט לחיים.
התחל עם משפט כוח קצר.""",

    "question": """המשפט הראשון חייב להתייחס ישירות למה שרואים בתמונה.
לאחר מכן כתוב שאלה כיפית מעוררת אינטראקציה שגורמת לאנשים לתייג חברים.
הוסף הנחיה לתגובה בסוף.""",
}

SLOT_TYPES = {
    0: "tip",
    1: "fact",
    2: "motivation",
}


def get_content_type(slot: int) -> str:
    base_type = SLOT_TYPES.get(slot % 3, "tip")
    types = list(PROMPTS.keys())
    day = datetime.now().timetuple().tm_yday
    index = (types.index(base_type) + day // 4) % len(types)
    return types[index]


def _is_video(url: str) -> bool:
    return any(url.lower().split("?")[0].endswith(ext) for ext in VIDEO_EXTENSIONS)


def _extract_video_thumbnail(video_url: str) -> tuple[str, str]:
    """מוריד סרטון ומחלץ פריים ראשון כ-JPEG."""
    tmp_video = Path(tempfile.mktemp(suffix=".mp4"))
    tmp_thumb = Path(tempfile.mktemp(suffix=".jpg"))
    try:
        resp = requests.get(video_url, timeout=60, stream=True)
        resp.raise_for_status()
        with open(tmp_video, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        subprocess.run(
            [FFMPEG, "-y", "-i", str(tmp_video), "-vframes", "1", "-q:v", "2", str(tmp_thumb)],
            check=True, capture_output=True, timeout=30,
        )
        data = base64.standard_b64encode(tmp_thumb.read_bytes()).decode("utf-8")
        return data, "image/jpeg"
    finally:
        for p in (tmp_video, tmp_thumb):
            try: p.unlink()
            except: pass


def _fetch_image_as_base64(url: str) -> tuple[str, str]:
    """מוריד תמונה (או פריים מסרטון) ומחזיר (base64_data, media_type)."""
    if _is_video(url):
        return _extract_video_thumbnail(url)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    media_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
    return base64.standard_b64encode(resp.content).decode("utf-8"), media_type


def generate_caption(slot: int, image_url: str) -> str:
    content_type = get_content_type(slot)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    image_data, media_type = _fetch_image_as_base64(image_url)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": PROMPTS[content_type],
                },
            ],
        }],
    )
    return response.content[0].text
