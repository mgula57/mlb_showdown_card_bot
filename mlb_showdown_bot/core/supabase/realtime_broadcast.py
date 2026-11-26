"""
Supabase Realtime Broadcast pings: tell open pages that something changed so they refetch it.

Messages carry no data, only a nudge - pages always reload through the API, which keeps every
permission check server side. Sending is fire-and-forget on a background thread so a slow or
down Realtime never delays (or fails) the request that triggered it; pages keep a slow poll as
the backstop.
"""

import hashlib
import hmac
import logging
import os
import threading
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class RealtimeBroadcaster:
    """Sends Broadcast messages through Supabase Realtime's REST endpoint."""

    TIMEOUT_SECONDS = 3

    def __init__(self) -> None:
        self.url = os.getenv('SUPABASE_URL', '').rstrip('/')
        self.key = os.getenv('SUPABASE_KEY', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def send(self, topic: str, event: str, payload: Optional[dict] = None) -> None:
        """Broadcast `event` on `topic` without waiting for it to land."""
        self.send_many([topic], event, payload)

    def send_many(self, topics: list[str], event: str, payload: Optional[dict] = None) -> None:
        """Broadcast `event` on each of `topics` in one request, without waiting for it to land."""
        if not self.is_configured or not topics:
            return
        messages = [{'topic': topic, 'event': event, 'payload': payload or {}, 'private': False} for topic in topics]
        threading.Thread(target=self._post, args=(messages,), name='realtime-broadcast', daemon=True).start()

    def _post(self, messages: list[dict]) -> None:
        try:
            response = requests.post(
                f'{self.url}/realtime/v1/api/broadcast',
                headers={'apikey': self.key, 'Authorization': f'Bearer {self.key}', 'Content-Type': 'application/json'},
                json={'messages': messages},
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning(f"Realtime broadcast to {', '.join(m['topic'] for m in messages)} failed: {exc}")

    # ----------------------------------------------------------
    # MARK: - TOPICS
    # ----------------------------------------------------------

    @staticmethod
    def league_draft_topic(league_id: str, season_number: int) -> str:
        """Matches `leagueDraftTopic` in frontend/src/api/leagues.ts."""
        return f'league-draft:{league_id}:{season_number}'

    def league_draft_changed(self, league_id: str, season_number: int) -> None:
        self.send(self.league_draft_topic(league_id, season_number), 'draft_changed')

    @staticmethod
    def notifications_topic(user_id: str) -> Optional[str]:
        """A user's notifications channel, or None when `NOTIFICATIONS_TOPIC_SECRET` isn't set (the bell
        then only polls). Public channels can be joined by anyone who knows the name, so the name is an
        HMAC of the user id that only the server can work out, and the ping says nothing but "look again"."""
        secret = os.getenv('NOTIFICATIONS_TOPIC_SECRET', '')
        if not secret:
            return None
        digest = hmac.new(secret.encode(), user_id.encode(), hashlib.sha256).hexdigest()[:40]
        return f'notifications:{digest}'

    def notifications_changed(self, user_ids: list[str]) -> None:
        """Matches `NOTIFICATIONS_EVENT` in frontend/src/api/notifications.ts."""
        self.send_many([topic for topic in map(self.notifications_topic, user_ids) if topic], 'notifications_changed')
