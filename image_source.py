"""
image_source.py
סדר עדיפות לתמונות:
  1. תמונות אישיות מ-GitHub (media/images/)
  2. Pexels API (אם קיים PEXELS_API_KEY)
  3. תמונות ברירת מחדל
"""

import os
import random
import requests

GITHUB_REPO = "vcarmel-cell/bowling_bot"
GITHUB_IMAGES_PATH = "media/images"
GITHUB_BRANCH = "main"

FALLBACK_IMAGES = [
    "https://images.pexels.com/photos/163452/bowling-game-fun-alley-163452.jpeg?w=1080&h=1080&fit=crop",
    "https://images.pexels.com/photos/1040160/pexels-photo-1040160.jpeg?w=1080&h=1080&fit=crop",
    "https://images.pexels.com/photos/3637795/pexels-photo-3637795.jpeg?w=1080&h=1080&fit=crop",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _get_github_image_url() -> str | None:
    """שולף URL אקראי של תמונה מה-GitHub repo."""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_IMAGES_PATH}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"token {token}"

    resp = requests.get(api_url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None

    files = [
        f for f in resp.json()
        if isinstance(f, dict)
        and any(f.get("name", "").lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
    ]
    if not files:
        return None

    chosen = random.choice(files)
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_IMAGES_PATH}/{chosen['name']}"


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
    """מחזיר URL לתמונה — לפי סדר עדיפות: GitHub → Pexels → ברירת מחדל."""
    for source in (_get_github_image_url, _get_pexels_image_url):
        try:
            url = source()
            if url:
                return url
        except Exception:
            pass
    return random.choice(FALLBACK_IMAGES)
