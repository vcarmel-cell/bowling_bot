"""
image_source.py
סדר עדיפות לתמונות:
  1. תמונות אישיות מ-GitHub (media/images/) — עם רוטציה (כל תמונה נבחרת פעם אחת לפני חזרה)
  2. Pexels API (אם קיים PEXELS_API_KEY)
  3. תמונות ברירת מחדל
"""

import json
import os
import random
import requests
from pathlib import Path

GITHUB_REPO = "vcarmel-cell/bowling_bot"
GITHUB_IMAGES_PATH = "media/images"
GITHUB_BRANCH = "main"
USED_IMAGES_FILE = Path(__file__).parent / "media" / "used_images.json"

FALLBACK_IMAGES = [
    "https://images.pexels.com/photos/163452/bowling-game-fun-alley-163452.jpeg?w=1080&h=1080&fit=crop",
    "https://images.pexels.com/photos/1040160/pexels-photo-1040160.jpeg?w=1080&h=1080&fit=crop",
    "https://images.pexels.com/photos/3637795/pexels-photo-3637795.jpeg?w=1080&h=1080&fit=crop",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _load_used() -> set:
    if USED_IMAGES_FILE.exists():
        return set(json.loads(USED_IMAGES_FILE.read_text(encoding="utf-8")))
    return set()


def _save_used(used: set) -> None:
    USED_IMAGES_FILE.parent.mkdir(parents=True, exist_ok=True)
    USED_IMAGES_FILE.write_text(json.dumps(sorted(used)), encoding="utf-8")


def _pick_unused(names: list[str]) -> str:
    """בוחר שם תמונה שלא שומשה. כשנגמרות — מאפס ומתחיל סבב חדש."""
    used = _load_used()
    available = [n for n in names if n not in used]
    if not available:
        used = set()
        available = names
    chosen = random.choice(available)
    used.add(chosen)
    _save_used(used)
    return chosen


def _get_github_image_url() -> str | None:
    """שולף URL של תמונה לא-משומשת מה-GitHub repo."""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_IMAGES_PATH}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"token {token}"

    resp = requests.get(api_url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None

    names = [
        f["name"] for f in resp.json()
        if isinstance(f, dict)
        and any(f.get("name", "").lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
    ]
    if not names:
        return None

    chosen = _pick_unused(names)
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_IMAGES_PATH}/{chosen}"


def _get_pexels_image_url() -> str | None:
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
    """מחזיר URL לתמונה — לפי סדר עדיפות: GitHub → Pexels → ברירת מחדל."""
    for source in (_get_github_image_url, _get_pexels_image_url):
        try:
            url = source()
            if url:
                return url
        except Exception:
            pass
    return random.choice(FALLBACK_IMAGES)
