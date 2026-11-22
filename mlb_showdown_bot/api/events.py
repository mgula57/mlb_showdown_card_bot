"""Product events from the web app (`POST /api/events`), stored in `internal.log_event`.

The frontend batches events through `frontend/src/analytics/track.ts`. Anyone can post (most
visitors aren't signed in), so the payload is treated as untrusted: only events and property keys
listed in `ClientEventSchema.EVENTS` are kept, values must be scalars, strings are truncated,
and batches are capped. The user comes from the verified JWT, never the body, and the visitor ids
from the same headers every logged request carries (see `ClientContext`).
"""

from typing import Any, ClassVar, Optional

from flask import Blueprint, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.utils.client_context import ClientContext
from .user_settings import optional_user_id

events_bp = Blueprint('events', __name__)


class ClientEventSchema:
    """The events the app reports and the properties each may carry."""

    EVENTS: ClassVar[dict[str, frozenset[str]]] = {
        # Every route change; `route` holds the path
        'page_view': frozenset(),
        # First event in a browser tab's session: where the visit came from and on what
        'session_start': frozenset({'referrer_host', 'utm_source', 'utm_medium', 'utm_campaign', 'device', 'standalone', 'screen_width'}),
        # Supabase sign-in (password, Google, Discord). Once per session per account
        'sign_in': frozenset({'provider'}),
        # A card handed to the Custom Card Builder from a card's detail view
        'open_in_builder': frozenset({'set', 'is_wotc'}),
        # A Card Builder request that never got a response (network error, server crash, timeout)
        'builder_client_error': frozenset({'message', 'status', 'generation_source'}),
        # A Release Builder edition downloaded as a zip of card images
        'release_zip_download': frozenset({'card_count'}),
    }
    MAX_EVENTS: ClassVar[int] = 25
    MAX_STRING_LENGTH: ClassVar[int] = 300
    MAX_ROUTE_LENGTH: ClassVar[int] = 256

    @classmethod
    def _clean_value(cls, value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            return value[:cls.MAX_STRING_LENGTH]
        return None

    @classmethod
    def _clean_route(cls, route: Any) -> Optional[str]:
        if not isinstance(route, str) or not route.startswith('/'):
            return None
        return route.split('?', 1)[0].split('#', 1)[0][:cls.MAX_ROUTE_LENGTH]

    @classmethod
    def parse(cls, payload: Any, user_id: Optional[str], client: ClientContext) -> list[dict]:
        """Rows for `PostgresDB.log_events`; anything not in the schema is dropped."""
        raw_events = payload.get('events') if isinstance(payload, dict) else None
        if not isinstance(raw_events, list):
            return []
        rows = []
        for raw in raw_events[:cls.MAX_EVENTS]:
            if not isinstance(raw, dict):
                continue
            allowed_properties = cls.EVENTS.get(raw.get('event'))
            if allowed_properties is None:
                continue
            raw_properties = raw.get('properties') if isinstance(raw.get('properties'), dict) else {}
            properties = {
                key: cls._clean_value(value)
                for key, value in raw_properties.items()
                if key in allowed_properties and cls._clean_value(value) is not None
            }
            rows.append({
                'event': raw['event'],
                'user_id': user_id,
                **client.as_columns(),
                'route': cls._clean_route(raw.get('route')),
                'properties': properties or None,
            })
        return rows


@events_bp.route('/events', methods=['POST'])
def log_client_events():
    rows = ClientEventSchema.parse(
        request.get_json(silent=True),
        user_id=optional_user_id(),
        client=ClientContext.from_headers(request.headers),
    )
    if rows:
        with PostgresDB() as db:
            db.log_events(rows)
    return jsonify({'logged': len(rows)}), 202
