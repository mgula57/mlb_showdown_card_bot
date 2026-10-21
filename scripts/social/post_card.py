"""Post a random ShowdownBot card to X.

Dry run by default: picks a card, builds the caption, downloads the image and prints everything
without posting or writing to the log. Pass `--live` to post.

    python scripts/social/post_card.py               # dry run
    python scripts/social/post_card.py --live        # post + log
"""
import argparse
import sys
from pathlib import Path

from caption import CaptionBuilder
from pick_card import CardPicker
from post_log import PostLog, SocialPost
from showdown_api import ShowdownApiClient

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="Actually post and write the log row (default: dry run)")
    parser.add_argument("--days", type=int, default=60, help="Don't repeat a card posted within this many days")
    parser.add_argument("--env", choices=["dev", "prod"], default="prod", help="Database holding the post log")
    parser.add_argument("--site-url", default=None, help="Override the site/API root (default: SHOWDOWN_SITE_URL or showdownbot.com)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Where the card image is saved")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "LIVE" if args.live else "DRY RUN"
    print(f"== Social card post ({mode}, log env={args.env}, exclusion={args.days}d) ==")

    # A dry run without DB credentials still works, it just can't exclude recent posts.
    post_log: PostLog | None = None
    try:
        post_log = PostLog(env=args.env)
    except Exception as e:
        if args.live:
            raise
        print(f"⚠️  Post log unavailable, not excluding recent posts: {e}")

    try:
        excluded_keys = post_log.recent_card_keys(args.days) if post_log else set()
        print(f"Excluding {len(excluded_keys)} recently posted card(s)")

        api = ShowdownApiClient(site_url=args.site_url)
        picked = CardPicker(api=api, excluded_keys=excluded_keys, output_dir=args.output_dir).pick()

        builder = CaptionBuilder(row=picked.row, card=picked.card)
        caption, alt_text = builder.caption(), builder.alt_text()

        print(f"\nCard:     {picked.row['name']} {picked.row['year']} ({picked.row['showdown_set']}) - {picked.row['card_id']}")
        print(f"Key:      {picked.card_key}")
        print(f"Image:    {picked.image_path}")
        print(f"Alt text: {alt_text}")
        print(f"Caption ({len(caption)} chars):\n{caption}\n")

        if not args.live:
            print("Dry run - nothing posted or logged.")
            return 0

        from x_poster import XPoster  # Only needed (and credentials only required) for live runs
        post_id = XPoster().post(text=caption, image_path=picked.image_path, alt_text=alt_text)
        print(f"✅ Posted: https://x.com/i/web/status/{post_id}")

        try:
            post_log.record(SocialPost(
                card_key=picked.card_key,
                card_id=picked.row["card_id"],
                showdown_set=str(picked.row["showdown_set"]),
                year=int(picked.row["year"]),
                name=picked.row["name"],
                post_id=post_id,
                caption=caption,
            ))
        except Exception as e:
            print(f"::error::Post {post_id} succeeded but logging it failed - card {picked.card_key} may repeat: {e}")
            raise
        print("✅ Logged to internal.social_post_log")
        return 0
    finally:
        if post_log:
            post_log.close()


if __name__ == "__main__":
    sys.exit(main())
