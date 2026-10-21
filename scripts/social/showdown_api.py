"""Thin client for the public showdownbot.com API - all card data and image rendering stays server-side."""
import os
from pathlib import Path
from urllib.parse import quote

import requests

DEFAULT_SITE_URL = "https://www.showdownbot.com"


class ShowdownApiClient:
    """Fetches random cards, full card payloads and rendered card images from the Flask API.

    Args:
      site_url: Root of the site. The API lives under `/api` and rendered images under `/static/output`.
      timeout: Per-request timeout in seconds. Image rendering is the slow call (~5-15s).
    """

    def __init__(self, site_url: str | None = None, timeout: int = 90) -> None:
        self.site_url = (site_url or os.getenv("SHOWDOWN_SITE_URL") or DEFAULT_SITE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "showdownbot-social-poster"

    def random_cards(self, showdown_set: str, limit: int = 50) -> list[dict]:
        """Random sample of `card_bot` rows for a set, excluding small-sample seasons.

        The search endpoint caches by payload for ~2h, so repeat calls inside one run return the
        same sample - callers should pick from this list rather than re-query for each retry.
        """
        payload = {
            "sort_by": "random()",
            "limit": limit,
            "showdown_set": showdown_set,
            "include_small_sample_size": ["false"],
        }
        response = self.session.post(f"{self.site_url}/api/cards/search", json=payload, timeout=self.timeout)
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list):
            raise RuntimeError(f"Unexpected /cards/search response: {rows}")
        return rows

    def fetch_card(self, card_id: str) -> dict:
        """Full serialized `ShowdownPlayerCard` for a stored card id."""
        response = self.session.get(
            f"{self.site_url}/api/cards/card",
            params={"id": card_id, "src": "social"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        card = response.json().get("card")
        if not card:
            raise RuntimeError(f"Card {card_id} not found")
        return card

    def render_image(self, card: dict, output_dir: Path) -> Path:
        """Render the card on the server, then download the image into `output_dir`.

        Heroku's filesystem is ephemeral, so the image is downloaded immediately after rendering.
        """
        response = self.session.post(
            f"{self.site_url}/api/build_image_for_card",
            json={"card": card},
            timeout=self.timeout,
        )
        response.raise_for_status()
        image = (response.json().get("card") or {}).get("image") or {}
        folder, file_name = image.get("output_folder_path"), image.get("output_file_name")
        if not folder or not file_name:
            raise RuntimeError(f"Image render returned no file: {image.get('error') or response.text[:300]}")

        download = self.session.get(f"{self.site_url}/{folder.strip('/')}/{quote(file_name)}", timeout=self.timeout)
        download.raise_for_status()

        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / file_name
        image_path.write_bytes(download.content)
        return image_path
