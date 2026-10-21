"""Posting to X via tweepy (OAuth 1.0a user context)."""
import os
from pathlib import Path

import tweepy

REQUIRED_ENV_VARS = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]


class XPoster:
    """Uploads an image with alt text and creates a post referencing it.

    Media upload and alt text use the v1.1 media endpoints (tweepy 4.x has no v2 media upload);
    the post itself is created with v2 `POST /2/tweets`. Swap `upload_image` if v1.1 media is retired.
    """

    def __init__(self) -> None:
        missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Missing X credentials: {', '.join(missing)}")
        credentials = dict(
            consumer_key=os.environ["X_API_KEY"],
            consumer_secret=os.environ["X_API_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
        )
        self.client = tweepy.Client(**credentials)
        self.api_v1 = tweepy.API(tweepy.OAuth1UserHandler(**credentials))

    def upload_image(self, image_path: Path, alt_text: str) -> str:
        media = self.api_v1.media_upload(filename=str(image_path))
        media_id = media.media_id_string
        try:
            self.api_v1.create_media_metadata(media_id, alt_text)
        except tweepy.TweepyException as e:
            # Alt text is an accessibility nicety; don't lose the post over it, but surface it in the Actions log.
            print(f"::warning::Alt text failed for media {media_id}: {e}")
        return media_id

    def post(self, text: str, image_path: Path, alt_text: str) -> str:
        """Returns the new post's id."""
        media_id = self.upload_image(image_path, alt_text)
        response = self.client.create_tweet(text=text, media_ids=[media_id])
        return str(response.data["id"])
