"""
image_source.py
סדר עדיפות לתמונות:
  1. תמונות אישיות מ-media/images/ (מועלות ל-Imgur לקבלת URL ציבורי)
  2. Pexels API (אם קיים PEXELS_API_KEY)
  3. תמונות ברירת מחדל
"""

import base64
import os
import random
import requests
from pathlib import Path

MEDIA_DIR = Path(__file__).parent / "media" / "images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

FALLBACK_IMAGES = [
    "https://images.pexels.com/photos/163452/bowling-game-fun-alley-163452.jpeg?w=1080&h=1080&fit=crop",
    "https://images.pexels.com/photos/1040160/pexels-photo-1040160.jpeg?w=1080&h=1080&fit=crop",
    "https://images.pexels.com/photos/3637795/pexels-photo-3637795.jpeg?w=1080&h=1080&fit=crop",
]


def _upload_to_imgur(image_path: Path) -> str:
    """מעלה תמונה מקומית ל-Imgur ומחזיר URL ציבורי."""
    client_id = os.environ.get("IMGUR_CLIENT_ID", "")
    if not client_id:
        raise EnvironmentError("IMGUR_CLIENT_ID לא מוגדר — נדרש להעלאת תמונות מקומיות")

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    resp = requests.post(
        "https://api.imgur.com/3/image",
        headers={"Authorization": f"Client-ID {client_id}"},
        data={"image": image_data, "type": "base64"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]["link"]


def _get_local_image_url() -> str | None:
    """מחזיר URL של תמונה אישית אקראית אם קיימת בתיקייה."""
    if not MEDIA_DIR.exists():
        return None
    images = [f for f in MEDIA_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    if not images:
        return None
    chosen = random.choice(images)
    return _upload_to_imgur(chosen)


def _get_pexels_image_url() -> str | None:
    """שולף תמונת באולינג אקראית מ-Pexels."""
    api_key = os.environ.get("PEXELS_API_KEY", "")
    if not api_key:
        return None
    headers = {"Authorization": api_key}
    page = random.randint(1, 5)
    resp = requests.get(
        "https://api.pexels.com/v1/search",
        headers=headers,
        params={"query": "bowling", "per_page": 10, "page": page, "orientation": "square"},
        timeout=10,
    )
    resp.raise_for_status()
    photos = resp.json().get("photos", [])
    if not photos:
        return None
    return random.choice(photos)["src"]["large"]


def get_bowling_image_url() -> str:
    """מחזיר URL לתמונה — לפי סדר עדיפות: אישית → Pexels → ברירת מחדל."""
    for source in (_get_local_image_url, _get_pexels_image_url):
        try:
            url = source()
            if url:
                return url
        except Exception:
            pass
    return random.choice(FALLBACK_IMAGES)
