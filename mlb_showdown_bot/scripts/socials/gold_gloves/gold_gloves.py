"""2026 Gold Glove winners through the Showdown Bot (2005 set) -> two 1080x1350 social slides (AL, NL).

Run from the repo root (after `uv sync`):
    .venv/bin/python mlb_showdown_bot/scripts/socials/gold_gloves/gold_gloves.py [--out DIR] [--placeholders]

Needs statsapi.mlb.com reachable. For player photos, GOOGLE_CREDENTIALS must be set and
oauth2.googleapis.com / www.googleapis.com reachable; otherwise cards fall back to silhouettes.
Slides are screenshotted with Node Playwright (shoot.js). Output defaults to
mlb_showdown_bot/scripts/output/gold_gloves/ (gitignored).
"""
import argparse
import sys
import time
import unicodedata
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader

from mlb_showdown_bot.core.card.card_generation import generate_card
from mlb_showdown_bot.core.simulation.challenge_week_report import ChallengeWeek
from mlb_showdown_bot.core.simulation.social_report import SocialSheetReport

HERE = Path(__file__).resolve().parent
YEAR = "2026"
SHOWDOWN_SET = "2005"
POSITIONS = {"P": "Pitcher", "C": "Catcher", "1B": "First Base", "2B": "Second Base", "3B": "Third Base",
             "SS": "Shortstop", "LF": "Left Field", "CF": "Center Field", "RF": "Right Field", "UT": "Utility"}

# 2026 RAWLINGS GOLD GLOVE WINNERS (ANNOUNCED NOV 1, 2026)
WINNERS = {
    "American League": [
        ("P", "Tanner Bibee", "CLE"), ("C", "Dillon Dingler", "DET"), ("1B", "Christian Walker", "HOU"),
        ("2B", "Cole Young", "SEA"), ("3B", "Caleb Durbin", "BOS"), ("SS", "Taylor Walls", "TB"),
        ("LF", "Cody Bellinger", "NYY"), ("CF", "Ceddanne Rafaela", "BOS"), ("RF", "Wilyer Abreu", "BOS"),
        ("UT", "Ezequiel Duran", "TEX"),
    ],
    "National League": [
        ("P", "Nolan McLean", "NYM"), ("C", "Gabriel Moreno", "ARI"), ("1B", "Matt Olson", "ATL"),
        ("2B", "Brice Turang", "MIL"), ("3B", "Alex Bregman", "CHC"), ("SS", "Geraldo Perdomo", "ARI"),
        ("LF", "Jackson Chourio", "MIL"), ("CF", "Pete Crow-Armstrong", "CHC"), ("RF", "Corbin Carroll", "ARI"),
        ("UT", "Mauricio Dubón", "ATL"),
    ],
}


class GoldGloveReport(SocialSheetReport):
    SHEET_COUNT = 2
    TEMPLATE_NAME = "gold_gloves.html.j2"

    def __init__(self, leagues: list[dict]) -> None:
        super().__init__()
        self.env.loader = ChoiceLoader([FileSystemLoader(HERE), self.env.loader])
        self.leagues = leagues

    def context(self) -> dict:
        return dict(leagues=self.leagues, year=YEAR, showdown_set=SHOWDOWN_SET)


def build_card(name: str, cards_dir: Path, retries: int = 2) -> tuple[dict | None, Path | None, str | None]:
    file_name = f"{YEAR}-{SHOWDOWN_SET}-{name.replace(' ', '_')}.png"
    error = None
    for attempt in range(retries + 1):
        result = generate_card(name=name, year=YEAR, set=SHOWDOWN_SET, datasource="MLB_API",
                               output_folder_path=str(cards_dir), output_file_name=file_name)
        error = result.get("error")
        if not error and result.get("card"):
            path = cards_dir / file_name
            return result["card"], (path if path.exists() else None), None
        time.sleep(2 * (attempt + 1))
    return None, None, error


def _plain(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower().replace(".", "")


class ArchiveCards:
    """Pulls the stored 2026/2005 card for each winner from the archive DB (internal.dim_card) and renders it."""

    def __init__(self, env_var: str) -> None:
        from mlb_showdown_bot.core.database.postgres_db import PostgresDB
        self.db = PostgresDB(is_archive=env_var == "DATABASE_URL_ARCHIVE")

    def card_id(self, name: str) -> str | None:
        last = _plain(name).split()[-1]
        rows = self.db.fetch_card_list(filters=dict(
            search=last[:4], min_year=int(YEAR), max_year=int(YEAR), showdown_set=SHOWDOWN_SET,
            sort_by="points", sort_direction="desc", limit=25)) or []
        exact = [r for r in rows if _plain(r.get("name", "")) == _plain(name)]
        return exact[0]["card_id"] if exact else None

    def build(self, name: str, cards_dir: Path) -> tuple[dict | None, Path | None, str | None]:
        card_id = self.card_id(name)
        if not card_id:
            return None, None, f"no {YEAR} {SHOWDOWN_SET} card found in the DB"
        card = self.db.fetch_cards_by_ids([card_id]).get(card_id)
        if card is None:
            return None, None, f"{card_id} listed but card_data missing"
        card.image.output_folder_path = str(cards_dir)
        card.image.output_file_name = f"{card_id}.png"
        card.generate_card_image()
        path = cards_dir / card.image.output_file_name
        return card.as_json(), (path if path.exists() else None), None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE.parents[1] / "output" / "gold_gloves"))
    parser.add_argument("--placeholders", action="store_true", help="skip card generation (layout check only)")
    parser.add_argument("--from-db", choices=["DATABASE_URL_ARCHIVE", "DATABASE_URL_LOGS"], help="use stored cards instead of the MLB API")
    args = parser.parse_args()
    out = Path(args.out)
    cards_dir = out / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    archive = ArchiveCards(args.from_db) if args.from_db else None

    leagues, failures = [], []
    for league, winners in WINNERS.items():
        rows = []
        for pos, name, team in winners:
            if args.placeholders:
                card, path, error = None, None, "placeholder"
            elif archive:
                card, path, error = archive.build(name, cards_dir)
            else:
                card, path, error = build_card(name, cards_dir)
            if error and not args.placeholders:
                failures.append(f"{name}: {error}")
            print(("OK  " if path else "FAIL") + f" {'AL' if league.startswith('Am') else 'NL'} {pos:<2} {name}" + (f" ({card.get('points')} PT, {card.get('positions_and_defense_string')})" if card else ""), flush=True)
            rows.append(dict(
                name=name, team=team, position_label=POSITIONS[pos],
                points=card.get("points") if card else None,
                image_src=ChallengeWeek._embed_src(path) if path else "",
            ))
        leagues.append(dict(name=league, winners=rows))

    html_path = out / "gold_gloves.html"
    html_path.write_text(GoldGloveReport(leagues).render())

    # 2x CAPTURE (2160x2700) SO THE SMALL CARDS STAY CRISP WHEN THE PLATFORM DOWNSCALES.
    import subprocess
    subprocess.run(["node", str(HERE / "shoot.js"), str(html_path), str(out)], check=True)

    print(f"\nWrote {out}")
    if failures:
        print("FAILURES:\n  " + "\n  ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
