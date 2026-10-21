"""Read/write access to `internal.social_post_log` (built by `showdown_bot database build_social_post_log_table`)."""
import os
from dataclasses import dataclass

import psycopg2

# SAME ENV CONVENTION AS THE `showdown_bot database` CLI: dev -> LOGS DB, prod -> ARCHIVE DB
ENV_DATABASE_URLS = {"dev": "DATABASE_URL_LOGS", "prod": "DATABASE_URL_ARCHIVE"}


@dataclass
class SocialPost:
    """One post to record in the log."""
    card_key: str
    card_id: str
    showdown_set: str
    year: int | None
    name: str
    post_id: str
    caption: str
    platform: str = "x"


class PostLog:
    """Recently posted card keys and the insert after a successful post.

    Args:
      env: `dev` or `prod`, selecting the database URL env var.
      platform: Platform whose posts to read/write.
    """

    def __init__(self, env: str = "prod", platform: str = "x") -> None:
        env_var = ENV_DATABASE_URLS[env]
        url = os.getenv(env_var)
        if not url:
            raise RuntimeError(f"{env_var} is not set - needed to read/write the social post log ({env}).")
        self.platform = platform
        self.connection = psycopg2.connect(url, sslmode="require")
        self.connection.autocommit = True

    def recent_card_keys(self, days: int) -> set[str]:
        """Card keys posted to this platform within the last `days` days."""
        with self.connection.cursor() as cur:
            cur.execute(
                """
                SELECT card_key FROM internal.social_post_log
                WHERE platform = %s AND posted_at > NOW() - make_interval(days => %s)
                """,
                (self.platform, days),
            )
            return {row[0] for row in cur.fetchall()}

    def record(self, post: SocialPost) -> None:
        """Insert the post. A card reposted after the exclusion window replaces its old row."""
        with self.connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO internal.social_post_log
                    (platform, card_key, card_id, showdown_set, year, name, post_id, caption, posted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (platform, card_key) DO UPDATE SET
                    card_id = EXCLUDED.card_id,
                    showdown_set = EXCLUDED.showdown_set,
                    year = EXCLUDED.year,
                    name = EXCLUDED.name,
                    post_id = EXCLUDED.post_id,
                    caption = EXCLUDED.caption,
                    posted_at = EXCLUDED.posted_at
                """,
                (post.platform, post.card_key, post.card_id, post.showdown_set, post.year,
                 post.name, post.post_id, post.caption),
            )

    def close(self) -> None:
        self.connection.close()
