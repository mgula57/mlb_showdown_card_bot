"""Socials deliverable for the week's live Team Challenges: one 1080x1350 slide (2-3 key-player
cards fanned out up top, then the challenge menu), rendered through
`SocialSheetReport`. Driven by `showdown_bot challenges social` - see CHALLENGES.md.
"""

import re
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

from PIL import Image
from pydantic import BaseModel

from ..card.images import DEFAULT_RENDER_FILE_FORMAT
from ..database.postgres_db import PostgresDB
from .challenge_generator import ERA_LOCK_YEARS_KEY, REQUIRED_PLAYERS_KEY, BeatTarget, ChallengeCategory, GoalType
from .social_report import SocialSheetReport
from .takeover import TakeoverOptions

# MIRRORS THE FRONTEND'S `challengeCategory.ts` (LABEL + DISPLAY ORDER) AND THE LIGHT-THEME
# `--challenge-*` TOKENS IN frontend/src/index.css.
_CATEGORY_META = {
    ChallengeCategory.LEGENDARY.value: ("Legendary", "#c8962b"),
    ChallengeCategory.BUDGET_CAP.value: ("Budget Cap", "#2f6bd6"),
    ChallengeCategory.SUPERTEAM.value: ("Superteam", "#7c4dd0"),
    ChallengeCategory.THEMED.value: ("Themed", "#e0654f"),
}
_CATEGORY_ORDER = list(_CATEGORY_META)

_FIELDING_GROUP_LABELS = {'if': 'IF', 'of': 'OF', 'ca': 'C'}
_SCOPE_LABELS = {'hitters': 'Hitters', 'catchers': 'Catchers'}
_SCOPED_FILTER_PATTERN = re.compile(r'^(min|max)_(.+)_(hitters|catchers)$')

# CARD ART IS EMBEDDED IN THE PAGE AT 2x ITS 220px DISPLAY WIDTH - SHARP ON A SCREENSHOT
# WITHOUT CARRYING THREE FULL 1500x2100 RENDERS AS BASE64.
_EMBED_CARD_WIDTH = 440


class ChallengeSpotlight(BaseModel):
    """One live challenge instance, flattened into display-ready strings."""
    instance_id: str
    slug: str
    title: str
    description: str
    category: str
    category_label: str
    accent: str
    year: int
    replaces_abbr: str
    takeover_label: str
    goal_label: str
    pts_limit: Optional[int] = None
    roster_size: int
    restrictions: list[str] = []
    expires_at: datetime
    player_filters: dict = {}

    @property
    def year_range(self) -> tuple[int, int]:
        return self.player_filters.get('min_year') or self.year, self.player_filters.get('max_year') or self.year

    @staticmethod
    def _record(wins: int, losses: int) -> str:
        """W-L with a non-breaking hyphen, so a wrapped line never splits "(109-" from "53)"."""
        return f"{wins}\u2011{losses}"

    @classmethod
    def _goal_label(cls, row: dict) -> str:
        """Python twin of the frontend's `challengeGoalLabel`."""
        goal_value = row.get('goal_value') or {}
        match row.get('goal_type'):
            case GoalType.MADE_PLAYOFFS.value: return 'Make the playoffs'
            case GoalType.WIN_DIVISION.value: return 'Win the division'
            case GoalType.WIN_PENNANT.value: return 'Win the pennant'
            case GoalType.WIN_WORLD_SERIES.value: return 'Win the World Series'
            case GoalType.MIN_WINS.value: return f"Win at least {goal_value.get('min_wins', '?')} games"
            case GoalType.BEAT_TEAM_RECORD.value:
                target = goal_value.get('target_abbr')
                if target == BeatTarget.BEST_RECORD.value:
                    return "Beat that season's best record"
                if target == BeatTarget.WORST_RECORD.value:
                    return "Beat that season's worst record"
                record = row.get('beat_team_record') or {}
                if record.get('name'):
                    return f"Out-win the {row['year']} {record['name']} ({cls._record(record['wins'], record['losses'])})"
                return f"Beat the {row['year']} {target}'s record"
        return 'Clear the bar'

    @staticmethod
    def _restrictions(player_filters: dict, year: int) -> list[str]:
        """Python twin of the frontend's `challengeRestrictionsLabel`, one rule per entry. A
        single-season year lock matching the instance year is dropped - the graphic already leads
        with the year."""
        pf = player_filters
        parts: list[str] = []
        if pf.get('team'):
            parts.append(f"{'/'.join(pf['team'])} players only")
        if pf.get('hand'):
            parts.append(f"{'/'.join(pf['hand'])} bats only")
        min_year, max_year = pf.get('min_year'), pf.get('max_year')
        if not (min_year == max_year == year) and (min_year is not None or max_year is not None):
            parts.append(str(min_year) if min_year == max_year else f"{min_year or 'Any'}–{max_year or 'Any'} players")
        if pf.get('organization'):
            parts.append(f"{'/'.join(pf['organization'])} only")
        if pf.get('league'):
            parts.append(f"{'/'.join(pf['league'])} players only")
        for key, value in pf.items():
            match = _SCOPED_FILTER_PATTERN.match(key)
            if not match or value is None:
                continue
            bound, base, scope = match.groups()
            amount = f"{value}+" if bound == 'min' else f"≤{value}"
            if base == 'speed':
                stat = 'SPD'
            elif base == 'fielding' or base.startswith('fielding_'):
                group = _FIELDING_GROUP_LABELS.get(base.removeprefix('fielding_'))
                stat = f"{group} fielding" if group else 'fielding'
            elif base.startswith('chart_'):
                stat = f"{base.removeprefix('chart_').upper()} chart slots"
            else:
                stat = base.upper()
            parts.append(f"{_SCOPE_LABELS[scope]} {amount} {stat}")
        required = pf.get(REQUIRED_PLAYERS_KEY) or []
        if required:
            parts.append(f"Must roster {' & '.join(p.get('name') or p['bref_id'] for p in required)}")
        return parts

    @classmethod
    def from_instance(cls, row: dict, takeover: Optional[TakeoverOptions] = None) -> 'ChallengeSpotlight':
        category_label, accent = _CATEGORY_META.get(row.get('category'), _CATEGORY_META[ChallengeCategory.THEMED.value])
        club = None
        if takeover is not None:
            try:
                club = next((c for c in takeover.clubs if c.abbreviation == row['replaces_abbr']), None)
            except Exception:
                club = None
        takeover_label = f"{row['year']} {club.name} ({cls._record(club.wins, club.losses)})" if club else f"{row['year']} {row['replaces_abbr']}"
        player_filters = row.get('player_filters') or {}
        return cls(
            instance_id=row['instance_id'], slug=row['slug'], title=row['title'], description=row['description'],
            category=row.get('category') or ChallengeCategory.THEMED.value, category_label=category_label, accent=accent,
            year=row['year'], replaces_abbr=row['replaces_abbr'], takeover_label=takeover_label,
            goal_label=cls._goal_label(row), pts_limit=row.get('pts_limit'), roster_size=row.get('roster_size') or 25,
            restrictions=cls._restrictions(player_filters, row['year']), expires_at=row['expires_at'],
            player_filters=player_filters,
        )


class KeyPlayerCard(BaseModel):
    """One spotlighted card in the hero stack, tied to the challenge it fits."""
    card_id: str
    name: str
    year: str
    team: str
    points: int
    image_path: Path
    image_src: str = ""
    challenge: Optional[ChallengeSpotlight] = None


class ChallengeWeekReport(SocialSheetReport):
    """One 1080x1350 sheet: the key-player cards fanned out over the week's challenge menu."""

    SHEET_COUNT = 1
    TEMPLATE_NAME = "challenge_week_summary.html.j2"

    def __init__(self, challenges: list[ChallengeSpotlight], cards: list[KeyPlayerCard], headline: str, subhead: str, showdown_set: str, week_of: date) -> None:
        super().__init__()
        self.challenges = challenges
        self.cards = cards
        self.headline = headline
        self.subhead = subhead
        self.showdown_set = showdown_set
        self.week_of = week_of

    def context(self) -> dict:
        return dict(
            challenges=self.challenges,
            cards=self.cards,
            headline=self.headline,
            subhead=self.subhead,
            showdown_set=self.showdown_set,
            week_of=self.week_of,
            expires_at=min((c.expires_at for c in self.challenges), default=None),
        )


class ChallengeWeek:
    """Loads the live challenge instances from one DB, picks 2-3 key-player cards for them (hand
    picked via `card_ids`, or auto-picked: required players first, then each challenge's
    top-points eligible card), renders those cards, and writes the socials deliverable."""

    HTML_FILE = "challenges.html"
    PDF_FILE = "challenges.pdf"
    IMAGE_STEM = "challenges"
    CARDS_DIR = "cards"
    MAX_CARDS = 3

    def __init__(
        self, db: PostgresDB, showdown_set: str, out_dir: Path, slugs: Optional[list[str]] = None,
        card_ids: Optional[list[str]] = None, headline: Optional[str] = None, subhead: Optional[str] = None,
        start_date: Optional[date] = None,
    ) -> None:
        self.db = db
        self.showdown_set = showdown_set
        self.out_dir = Path(out_dir)
        self.slugs = slugs or []
        self.card_ids = [self._full_card_id(card_id) for card_id in (card_ids or [])][:self.MAX_CARDS]
        self.headline = headline or "This week's challenges"
        self.subhead = subhead or "Take over a real club, draft under the rules, sim the season."
        # THE "WEEK OF" DATE ON THE SLIDE - DEFAULTS TO TODAY, SET IT TO POST AHEAD OF (OR AFTER) LAUNCH.
        self.start_date = start_date or date.today()

    def _full_card_id(self, card_id: str) -> str:
        """Accepts `{year}-{bref_id}` or the full `{year}-{bref_id}-{set}` (bref ids never contain
        a dash), appending this run's set to the short form."""
        return card_id if card_id.count('-') >= 2 else f"{card_id}-{self.showdown_set}"

    def load_challenges(self) -> list[ChallengeSpotlight]:
        rows = self.db.fetch_active_challenges()
        if self.slugs:
            rows = [r for r in rows if r['slug'] in self.slugs]
        rows.sort(key=lambda r: _CATEGORY_ORDER.index(r['category']) if r.get('category') in _CATEGORY_ORDER else len(_CATEGORY_ORDER))
        takeovers: dict[int, TakeoverOptions] = {}
        return [ChallengeSpotlight.from_instance(r, takeovers.setdefault(r['year'], TakeoverOptions(year=r['year']))) for r in rows]

    def _candidate_ids(self, challenge: ChallengeSpotlight) -> list[str]:
        """Best-first card ids for one challenge: its required players, then the top-points cards
        that pass its player filters in its season. Small-sample cards are skipped - a cameo
        season can price like a star (e.g. 1965 Satchel Paige) but isn't who you'd build around."""
        required = challenge.player_filters.get(REQUIRED_PLAYERS_KEY) or []
        ids = [f"{challenge.year}-{p['bref_id']}-{self.showdown_set}" for p in required]
        filters = {k: v for k, v in challenge.player_filters.items() if k not in (REQUIRED_PLAYERS_KEY, ERA_LOCK_YEARS_KEY)}
        min_year, max_year = challenge.year_range
        filters.update(min_year=min_year, max_year=max_year, showdown_set=self.showdown_set, sort_by='points', sort_direction='desc', limit=25)
        ids += [r['card_id'] for r in (self.db.fetch_card_list(filters=filters) or []) if not r.get('is_small_sample_size')]
        return ids

    def pick_card_ids(self, challenges: list[ChallengeSpotlight]) -> list[tuple[str, Optional[ChallengeSpotlight]]]:
        """`card_ids` when given (each tagged with the first challenge whose season it fits),
        otherwise one auto-pick per challenge, round-robin in category order, unique players."""
        if self.card_ids:
            def fits(card_id: str) -> Optional[ChallengeSpotlight]:
                year = int(card_id.split('-')[0]) if card_id.split('-')[0].isdigit() else None
                return next((c for c in challenges if year is not None and c.year_range[0] <= year <= c.year_range[1]), None)
            return [(card_id, fits(card_id)) for card_id in self.card_ids]

        queues = [(challenge, self._candidate_ids(challenge)) for challenge in challenges]
        picks: list[tuple[str, Optional[ChallengeSpotlight]]] = []
        used_players: set[str] = set()
        while len(picks) < self.MAX_CARDS and any(ids for _, ids in queues):
            for challenge, ids in queues:
                while ids:
                    card_id = ids.pop(0)
                    player = card_id.split('-')[1]
                    if player not in used_players:
                        used_players.add(player)
                        picks.append((card_id, challenge))
                        break
                if len(picks) >= self.MAX_CARDS:
                    break
        return picks

    def render_cards(self, picks: list[tuple[str, Optional[ChallengeSpotlight]]], status_callback: Optional[Callable[[str], None]] = None) -> list[KeyPlayerCard]:
        """Render each picked card's full-size image into `out_dir/cards/` and a downscaled copy
        for the page. Ids missing from the archive are skipped with a status message."""
        cards_dir = self.out_dir / self.CARDS_DIR
        cards_dir.mkdir(parents=True, exist_ok=True)
        found = self.db.fetch_cards_by_ids([card_id for card_id, _ in picks])
        key_cards: list[KeyPlayerCard] = []
        for card_id, challenge in picks:
            card = found.get(card_id)
            if card is None:
                if status_callback:
                    status_callback(f"SKIPPED CARD: {card_id} not found in the archive")
                continue
            card.image.output_folder_path = str(cards_dir)
            card.image.file_format = DEFAULT_RENDER_FILE_FORMAT
            card.image.output_file_name = f"{card_id}.{card.image.file_format.extension}"
            card.generate_card_image()
            image_path = cards_dir / card.image.output_file_name
            key_cards.append(KeyPlayerCard(
                card_id=card_id, name=card.name, year=str(card.year), team=card.team.value, points=card.points,
                image_path=image_path, image_src=self._embed_src(image_path), challenge=challenge,
            ))
            if status_callback:
                status_callback(f"Rendered {card.name} ({card_id})")
        return key_cards

    @staticmethod
    def _embed_src(image_path: Path) -> str:
        with Image.open(image_path) as image:
            image = image.convert('RGB')
            image.thumbnail((_EMBED_CARD_WIDTH, _EMBED_CARD_WIDTH * 2))
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=88)
        return SocialSheetReport.bytes_data_uri(buffer.getvalue(), 'image/jpeg')

    def write_outputs(self, image_format: Optional[str] = "png", status_callback: Optional[Callable[[str], None]] = None) -> Path:
        """Write challenges.html, plus (when Chrome is available) challenges.pdf and the slide image
        (`challenges_1.<ext>`). Returns the HTML path. Raises ValueError when no challenge is live."""
        challenges = self.load_challenges()
        if not challenges:
            raise ValueError("No live challenge instances" + (f" matching {', '.join(self.slugs)}" if self.slugs else ""))
        self.out_dir.mkdir(parents=True, exist_ok=True)
        cards = self.render_cards(self.pick_card_ids(challenges), status_callback=status_callback)

        report = ChallengeWeekReport(challenges=challenges, cards=cards, headline=self.headline, subhead=self.subhead, showdown_set=self.showdown_set, week_of=self.start_date)
        html_path = self.out_dir / self.HTML_FILE
        html_path.write_text(report.render())
        skipped_pdf = ChallengeWeekReport.write_pdf(html_path=html_path, pdf_path=self.out_dir / self.PDF_FILE)
        if skipped_pdf and status_callback:
            status_callback(f"SKIPPED PDF: {skipped_pdf}")
        if image_format:
            image_paths = ChallengeWeekReport.image_paths(out_dir=self.out_dir, stem=self.IMAGE_STEM, image_format=image_format)
            skipped_images = ChallengeWeekReport.write_images(html_path=html_path, image_paths=image_paths)
            if skipped_images and status_callback:
                status_callback(f"SKIPPED IMAGES: {skipped_images}")
        return html_path
