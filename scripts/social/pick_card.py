"""Random card selection for social posts."""
import random
from dataclasses import dataclass
from pathlib import Path

from showdown_api import ShowdownApiClient

SHOWDOWN_SETS = ["2000", "2001", "2002", "2003", "2004", "2005", "CLASSIC", "EXPANDED"]


@dataclass
class PickedCard:
    """A selected card with its rendered image on disk."""
    card_key: str
    row: dict    # `card_bot` row from /cards/search - flattened card attributes + real stats
    card: dict   # full serialized ShowdownPlayerCard
    image_path: Path


def card_key_for_row(row: dict) -> str:
    """Player-season key, e.g. `bondsba01-2001`. Two-way players get one key per side."""
    player = row.get("bref_id") or f"mlb{row.get('mlb_id')}"
    key = f"{player}-{row.get('year')}"
    if row.get("player_type_override"):
        key += f"-{str(row['player_type_override']).strip('()')}"
    return key.lower()


def candidate_weight(row: dict) -> float:
    """Light bias toward recognizable cards: Hall of Famers, award winners and higher point values."""
    weight = 1.0 + max(row.get("points") or 0, 0) / 250
    if row.get("is_hof"):
        weight += 1
    if row.get("awards_list"):
        weight += 1
    return weight


class CardPicker:
    """Picks a random eligible card that hasn't been posted recently and renders its image.

    Args:
      api: API client.
      excluded_keys: Card keys posted inside the exclusion window.
      output_dir: Where downloaded images are saved.
      max_attempts: Cards to try before giving up (a render failure moves on to the next card).
    """

    def __init__(self, api: ShowdownApiClient, excluded_keys: set[str], output_dir: Path, max_attempts: int = 5) -> None:
        self.api = api
        self.excluded_keys = excluded_keys
        self.output_dir = output_dir
        self.max_attempts = max_attempts

    def eligible_candidates(self, rows: list[dict]) -> list[dict]:
        """Rows that can be posted, ordered by weighted random draw (Efraimidis-Spirakis)."""
        eligible = [
            row for row in rows
            if row.get("card_id") and row.get("name") and row.get("year")
            and not row.get("team_override")
            and card_key_for_row(row) not in self.excluded_keys
        ]
        return sorted(eligible, key=lambda row: random.random() ** (1 / candidate_weight(row)), reverse=True)

    def pick(self) -> PickedCard:
        attempts = 0
        errors: list[str] = []
        sets = random.sample(SHOWDOWN_SETS, len(SHOWDOWN_SETS))
        for showdown_set in sets:
            for row in self.eligible_candidates(self.api.random_cards(showdown_set)):
                if attempts >= self.max_attempts:
                    break
                attempts += 1
                try:
                    card = self.api.fetch_card(row["card_id"])
                    image_path = self.api.render_image(card, self.output_dir)
                    return PickedCard(card_key=card_key_for_row(row), row=row, card=card, image_path=image_path)
                except Exception as e:
                    errors.append(f"{row['card_id']}: {e}")
                    print(f"⚠️  Skipping {row['card_id']}: {e}")
            if attempts >= self.max_attempts:
                break
        raise RuntimeError(f"No card could be picked after {attempts} attempts: {errors}")
