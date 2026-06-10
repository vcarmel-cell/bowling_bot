"""
Bowling Instagram Bot
שימוש: python main.py --slot <0|1|2> [--dry-run]
  slot 0 = בוקר (09:00)
  slot 1 = צהריים (13:00)
  slot 2 = ערב (19:00)
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from content_gen import generate_caption
from image_source import get_bowling_image_url
from instagram import InstagramAPI
from video_processor import is_video_url, process_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)),
        logging.FileHandler(Path(__file__).parent / "bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Bowling Instagram Bot")
    parser.add_argument("--slot", type=int, choices=[0, 1, 2], required=True,
                        help="0=בוקר, 1=צהריים, 2=ערב")
    parser.add_argument("--dry-run", action="store_true",
                        help="הצג את הפוסט בלי לפרסם")
    args = parser.parse_args()

    log.info(f"Starting slot {args.slot} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    try:
        log.info("Fetching media...")
        media_url = get_bowling_image_url()
        log.info(f"Media URL: {media_url}")

        if is_video_url(media_url):
            log.info("Video detected — replacing audio with royalty-free music...")
            media_url = process_video(media_url)
            log.info(f"Processed video URL: {media_url}")

        log.info("Generating caption...")
        caption = generate_caption(args.slot, media_url)
        log.info(f"Caption:\n{caption}")

        if args.dry_run:
            print("\n=== DRY RUN — לא פורסם ===")
            print(f"מדיה: {media_url}")
            print(f"כיתוב:\n{caption}")
            return

        api = InstagramAPI()
        post_id = api.post(media_url, caption)
        log.info(f"Published successfully! Post ID: {post_id}")

    except Exception as e:
        log.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
