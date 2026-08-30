"""Simulate a single real MLB game with Showdown cards.

Two entry points into the same machinery:

  - PRE-GAME. MLB publishes probable starters days ahead and the batting orders roughly two hours
    before first pitch. Whichever is available is used; before lineups are posted the sim picks
    its own nine from the active roster, the same way a season game does.
  - TAKEOVER. A game already in progress is frozen (`GameStartState`) and the rest of it is
    simulated - inning, outs, baserunners, score, batting order spot, and every arm already used
    carried across.

Everything here is I/O and translation. The actual game is played by `Game`/`SimTeam`, unchanged
from the season path apart from the resume seam `Game.setup(start_state=...)` provides.
"""

from datetime import date, datetime
from enum import Enum
from random import Random
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..card.sets import Set
from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.stats.datasource import Datasource
from ..card.stats.stats_period import StatsPeriod, StatsPeriodType
from ..data.replacement_season_averages import build_replacement_level_stats_for_card
from ..database.postgres_db import PostgresDB
from ..mlb_stats_api import MLBStatsAPI
from ..mlb_stats_api.models.teams.roster import RosterTypeEnum
from ..shared.player_position import Position
from ..shared.team import Team as ShowdownTeam
from .game import Game
from .models import (
    CompletedHalfInning,
    GameResult,
    GameStartState,
    ManagerPreference,
    PitcherAppearance,
    SimTeamIdentity,
    TeamStartState,
)
from .runners import Runner, Runners
from .team import FIELD_POSITION_TO_SLOT, SimTeam

SIDES = ("away", "home")

# MLB REPORTS A BATTING ORDER AS "300" FOR THE SLOT-3 STARTER, "301" FOR THE FIRST SUB IN THAT
# SLOT, AND SO ON.
_BATTING_ORDER_SLOT_DIVISOR = 100

# STATES IN WHICH THE GAME HAS NOT STARTED / IS OVER. EVERYTHING ELSE IS LIVE.
_PREVIEW_STATES = {"P", "S", "PW"}
_FINAL_STATES = {"F", "O"}

# THE HALF-INNING IS OVER, NOT IN PROGRESS - RESUME FROM THE NEXT ONE.
_BETWEEN_HALVES = {"middle", "end"}

# FALLBACK SPEED FOR AN INHERITED RUNNER WHOSE CARD COULDN'T BE RESOLVED. MID-RANGE ON EVERY SET.
_DEFAULT_RUNNER_SPEED = 12


class CardOrigin(str, Enum):
    """Where a player's card came from. Surfaced so the UI can flag a made-up card as such."""

    PREBUILT = "PREBUILT"        # internal.dim_card
    GENERATED = "GENERATED"      # BUILT ON THE FLY FROM SEASON-TO-DATE MLB STATS
    REPLACEMENT = "REPLACEMENT"  # NO STATS AT ALL - A SYNTHETIC REPLACEMENT-LEVEL CARD


def _ip_to_innings(innings_pitched: str) -> float:
    """MLB's "5.2" (five and two thirds) to a real number of innings."""
    try:
        whole, _, thirds = str(innings_pitched).partition(".")
        return int(whole or 0) + (int(thirds or 0) / 3.0)
    except (TypeError, ValueError):
        return 0.0


def _half_index(inning: int, is_top: bool) -> int:
    """Sortable position of a half-inning, so 'before the takeover point' is a plain comparison."""
    return inning * 2 + (0 if is_top else 1)


# ----------------------------------------------------------
# MARK: - CARDS
# ----------------------------------------------------------

class MLBGameCardPool:
    """Showdown cards for every player who could appear in one real game.

    Three tiers, cheapest first:
      1. Pre-built cards from `internal.dim_card` - one query for the whole game.
      2. Cards generated from season-to-date MLB stats, for anyone the archive hasn't built yet.
         Deliberately uses the same DATES stats period the game page's own card fetch uses, so a
         card in the simulated play-by-play is the same card already rendered on screen.
      3. A synthetic replacement-level card, for a player with no stats to build from at all (a
         first-day callup). Mirrors the fallback in `add_showdown_cards_to_mlb_api_roster`.
    """

    def __init__(self, season: int, showdown_set: Set, official_date: str, db: Optional[PostgresDB] = None) -> None:
        self.season = season
        self.showdown_set = showdown_set
        self.official_date = official_date
        self.db = db
        self.cards: dict[str, ShowdownPlayerCard] = {}
        self.origins: dict[str, CardOrigin] = {}
        self.warnings: list[str] = []

    @property
    def card_year(self) -> int:
        """The season the cards are built from.

        Before May the current season is a few weeks of noise, so cards roll back a year - the
        same rule `add_showdown_cards_to_mlb_api_roster` and the game page both apply, and the
        reason the sim's cards line up with the ones already on screen.
        """
        today = datetime.now().date()
        if self.season == today.year and today < date(self.season, 5, 1):
            return self.season - 1
        return self.season

    def resolve(self, players: dict[str, dict[str, Any]]) -> dict[str, ShowdownPlayerCard]:
        """Resolve every player at once.

        Args:
          players: mlb player id (as a string) -> {'name', 'is_pitcher', 'position', 'team'}.

        Returns:
          The subset that resolved, keyed by player id. A player is only ever missing here if
          even the replacement-level fallback raised, which is logged into `warnings`.
        """

        pending = {pid: info for pid, info in players.items() if pid not in self.cards}
        if not pending:
            return self.cards

        self._load_prebuilt(pending)
        self._generate_missing({pid: info for pid, info in pending.items() if pid not in self.cards})
        self._fill_replacements({pid: info for pid, info in pending.items() if pid not in self.cards})
        return self.cards

    def _load_prebuilt(self, pending: dict[str, dict]) -> None:
        year = self.card_year
        try:
            with (self.db or PostgresDB()) as db:
                found = db.fetch_cards_for_player_ids(
                    player_ids=[f"{year}-{pid}" for pid in pending],
                    showdown_set=self.showdown_set.value,
                    source=Datasource.MLB_API,
                )
        except Exception as exc:
            self.warnings.append(f"Could not read pre-built cards: {exc}")
            return

        resolved = 0
        for player_id in pending:
            card = found.get(f"{year}-{player_id}")
            if card is not None:
                self._store(player_id, card, CardOrigin.PREBUILT, pending[player_id])
                resolved += 1

        # `fetch_cards_for_player_ids` SWALLOWS ITS OWN ERRORS AND RETURNS AN EMPTY DICT, WHICH IS
        # INDISTINGUISHABLE FROM "NOBODY HAS A CARD" - AND WOULD OTHERWISE SEND A WHOLE GAME DOWN
        # THE SLOW REBUILD PATH WITHOUT SAYING SO. ONLY WORTH FLAGGING FOR A *COMPLETED* SEASON:
        # THE ARCHIVE BUILDS CARDS AFTER A SEASON ENDS, SO A FULL MISS ON THE CURRENT ONE IS THE
        # ORDINARY CASE, NOT A FAULT.
        if resolved == 0 and len(pending) > 10 and year < datetime.now().year:
            self.warnings.append(
                f"No pre-built {year} cards were returned for any of the {len(pending)} players in this game. "
                "Cards were rebuilt from stats instead, which is slower and may not match the game page."
            )

    def _generate_missing(self, pending: dict[str, dict]) -> None:
        if not pending:
            return

        # IMPORTED LAZILY: `card_generation` PULLS IN THE WHOLE SCRAPING/IMAGE STACK, AND THE
        # PRE-BUILT TIER COVERS ALMOST EVERY GAME, SO MOST REQUESTS NEVER NEED IT.
        from ..card.card_generation import generate_cards

        year = self.card_year
        try:
            generated = generate_cards(
                player_ids=list(pending.keys()),
                years=[year],
                keep_as_py_objects=True,
                # `year` IS PASSED THROUGH TO `StatsPeriod` AND IS REQUIRED THERE - `years` ONLY
                # DRIVES THE OUTER LOOP.
                year=str(year),
                set=self.showdown_set.value,
                stats_period_type="DATES",
                # FROM THE START OF THE SEASON SO AN EARLY-SEASON GAME STILL HAS A SAMPLE, WHICH
                # MATCHES THE SETTINGS THE GAME PAGE FETCHES ITS OWN CARDS WITH.
                start_date=f"{year}-03-01",
                end_date=self.official_date or f"{year}-12-31",
            )
        except Exception as exc:
            self.warnings.append(f"Could not build cards for {len(pending)} player(s): {exc}")
            return

        for entry in (generated or []):
            card = entry.get('card') if isinstance(entry, dict) else entry
            if not isinstance(card, ShowdownPlayerCard) or card.mlb_id is None:
                continue
            player_id = str(card.mlb_id)
            if player_id in pending:
                self._store(player_id, card, CardOrigin.GENERATED, pending[player_id])

    def _fill_replacements(self, pending: dict[str, dict]) -> None:
        for player_id, info in pending.items():
            try:
                self._store(player_id, self._replacement_card(info), CardOrigin.REPLACEMENT, info)
            except Exception as exc:
                self.warnings.append(f"No card could be built for {info.get('name') or player_id}: {exc}")

    def _replacement_card(self, info: dict) -> ShowdownPlayerCard:
        """A synthetic card for a player with no stats anywhere - a debutant, or someone the
        archive simply hasn't seen. Better than dropping them from the roster, which would leave
        the sim short a position."""

        year = self.card_year
        is_pitcher = bool(info.get('is_pitcher'))
        try:
            showdown_position = Position((info.get('position') or '').upper())
        except ValueError:
            # NOTE THE MEMBER NAMES DIVERGE FROM THE VALUES HERE - `Position.SP` IS "STARTER".
            showdown_position = Position.SP if is_pitcher else None

        stats = build_replacement_level_stats_for_card(
            year=year,
            player_type="PITCHER" if is_pitcher else "HITTER",
            positions=[showdown_position] if showdown_position else None,
        )
        stats['name'] = info.get('name') or 'Unknown'
        stats['team'] = info.get('team') or 'MLB'

        card = ShowdownPlayerCard(
            name=stats['name'],
            year=str(year),
            set=self.showdown_set,
            era="DYNAMIC",
            stats_period=StatsPeriod(year=str(year), type=StatsPeriodType.REPLACEMENT),
            stats=stats,
        )
        card.warnings.append(f"No {year} Showdown card exists for this player. A replacement level card was used.")
        return card

    def _store(self, player_id: str, card: ShowdownPlayerCard, origin: CardOrigin, info: dict) -> None:
        # THE CARD MAY BELONG TO THE CLUB THE PLAYER USED TO PLAY FOR. THE SIM REPORTS THE TEAM THEY
        # ARE SUITING UP FOR TONIGHT, WHICH `SimPlayer.team_override` HANDLES - BUT THE MLB ID IS
        # NEEDED HERE BECAUSE A PRE-BUILT CARD IS KEYED ON THE BREF ID.
        if card.mlb_id is None:
            try:
                card.mlb_id = int(player_id)
            except (TypeError, ValueError):
                pass
        self.cards[player_id] = card
        self.origins[player_id] = origin


# ----------------------------------------------------------
# MARK: - SETUP MODELS
# ----------------------------------------------------------

class MLBGameLineupSlot(BaseModel):
    batting_order: int   # 1-9
    player_id: str
    name: str = ""
    position: str = ""


class MLBGamePlayerOption(BaseModel):
    """One available player, with just enough of the card for the setup UI to rank and swap."""

    player_id: str
    name: str = ""
    position: str = ""
    is_pitcher: bool = False
    points: int = 0
    command: int = 0
    ip: Optional[int] = None
    positions_and_defense: str = ""
    card_origin: CardOrigin = CardOrigin.PREBUILT
    # TRUE ONCE THE PLAYER HAS BEEN SUBSTITUTED OUT OF A GAME IN PROGRESS - THEY CANNOT RETURN.
    is_unavailable: bool = False


class MLBGameTeamSetup(BaseModel):
    side: str                     # "away" | "home"
    team_id: Optional[int] = None
    identity: SimTeamIdentity
    lineup: list[MLBGameLineupSlot] = []
    starting_pitcher_id: str = ""
    position_players: list[MLBGamePlayerOption] = []
    bullpen: list[MLBGamePlayerOption] = []
    # PER-SIDE MANAGER TENDENCIES. NEUTRAL BY DEFAULT; THE CLIENT SUPPLIES A CUSTOM ONE THROUGH
    # THE SAME OVERRIDE PATH AS A LINEUP EDIT (SEE `_apply_lineup_overrides`).
    manager: ManagerPreference = Field(default_factory=ManagerPreference)


class LineupSource(str, Enum):
    ANNOUNCED = "ANNOUNCED"   # MLB PUBLISHED THE BATTING ORDER
    AUTO = "AUTO"             # NOT POSTED YET - THE SIM PICKS ITS OWN NINE


class MLBGameSetup(BaseModel):
    """Everything the simulation will run with, handed to the client before it commits so a
    lineup can be reviewed or changed first."""

    game_pk: int
    season: int
    showdown_set: str
    official_date: str = ""
    detailed_state: str = ""
    is_takeover: bool = False
    is_final: bool = False
    lineup_source: LineupSource = LineupSource.AUTO
    away: MLBGameTeamSetup
    home: MLBGameTeamSetup
    start_state: Optional[GameStartState] = None
    warnings: list[str] = []


class MLBGameSimResult(BaseModel):
    game_pk: int
    season: int
    showdown_set: str
    seed: Optional[int] = None
    is_takeover: bool = False
    setup: MLBGameSetup
    game: GameResult
    # THE REAL PLATE APPEARANCES THAT HAPPENED BEFORE THE TAKEOVER, VERBATIM FROM THE MLB FEED, SO
    # THE CLIENT CAN RENDER ONE CONTINUOUS PLAY LOG WITHOUT A SECOND FETCH.
    real_plays: list[dict] = []


# ----------------------------------------------------------
# MARK: - SIMULATOR
# ----------------------------------------------------------

class MLBGameSimulator:
    """Reads a real game off the MLB Stats API and plays it out with Showdown cards."""

    def __init__(
        self, game_pk: int, showdown_set: Set = Set._2000,
        mlb_stats_api: Optional[MLBStatsAPI] = None, db: Optional[PostgresDB] = None,
    ) -> None:
        self.game_pk = game_pk
        self.showdown_set = showdown_set
        self.mlb_stats_api = mlb_stats_api or MLBStatsAPI()
        self.db = db
        self._boxscore: Optional[dict] = None
        # BUILT BY `build_setup` AND REUSED BY `simulate`. THE POOL IS BY FAR THE EXPENSIVE PART OF
        # A GAME, SO THE COMMON FLOW (BUILD A SETUP, THEN RUN IT) MUST NOT PAY FOR IT TWICE.
        self._pool: Optional[MLBGameCardPool] = None

    # ------------------------------------------------------------------
    # SOURCE DATA
    # ------------------------------------------------------------------

    @property
    def boxscore(self) -> dict:
        if self._boxscore is None:
            self._boxscore = self.mlb_stats_api.games.get_game_boxscore(self.game_pk)
        return self._boxscore

    @property
    def season(self) -> int:
        official_date = self.boxscore.get('datetime', {}).get('official_date') or ''
        try:
            return int(official_date[:4])
        except ValueError:
            return datetime.now().year

    @property
    def game_date(self) -> date:
        official_date = self.boxscore.get('datetime', {}).get('official_date') or ''
        try:
            return date.fromisoformat(official_date)
        except ValueError:
            return datetime.now().date()

    @property
    def coded_state(self) -> str:
        return (self.boxscore.get('status') or {}).get('coded_game_state') or ''

    @property
    def is_final(self) -> bool:
        return self.coded_state in _FINAL_STATES

    @property
    def is_live(self) -> bool:
        return not self.is_final and self.coded_state not in _PREVIEW_STATES

    # ------------------------------------------------------------------
    # SETUP
    # ------------------------------------------------------------------

    def build_setup(self) -> MLBGameSetup:
        box = self.boxscore
        official_date = (box.get('datetime') or {}).get('official_date') or ''

        rosters = {side: self._roster_ids(side) for side in SIDES}
        lineups = {side: self._announced_lineup(side) for side in SIDES}
        starters = {side: self._starting_pitcher_id(side) for side in SIDES}
        removed = {side: self._removed_player_ids(side) for side in SIDES}

        # A LINEUP IS ONLY "ANNOUNCED" WHEN BOTH SIDES HAVE A FULL NINE. A HALF-POSTED ONE WOULD
        # LEAVE THE TWO TEAMS BUILT ON DIFFERENT RULES.
        lineup_source = (
            LineupSource.ANNOUNCED
            if all(len(lineups[side]) == 9 for side in SIDES)
            else LineupSource.AUTO
        )
        if lineup_source == LineupSource.AUTO:
            lineups = {side: [] for side in SIDES}

        pool = self._resolve_cards(rosters=rosters, lineups=lineups, starters=starters)

        teams = {
            side: self._team_setup(
                side=side, pool=pool, roster=rosters[side], lineup=lineups[side],
                starting_pitcher_id=starters[side], removed_ids=removed[side],
            )
            for side in SIDES
        }

        return MLBGameSetup(
            game_pk=self.game_pk,
            season=self.season,
            showdown_set=self.showdown_set.value,
            official_date=official_date,
            detailed_state=(box.get('status') or {}).get('detailed_state') or '',
            is_takeover=self.is_live,
            is_final=self.is_final,
            lineup_source=lineup_source,
            away=teams['away'],
            home=teams['home'],
            start_state=self._build_start_state(teams) if self.is_live else None,
            warnings=pool.warnings,
        )

    # -- SOURCE DATA HELPERS ------------------------------------------------

    def _team_node(self, side: str) -> dict:
        return (self.boxscore.get('teams') or {}).get(side) or {}

    def _identity(self, side: str) -> SimTeamIdentity:
        team = self._team_node(side).get('team') or {}
        abbreviation = team.get('abbreviation') or side.upper()
        # NORMALIZE THROUGH THE SHOWDOWN TEAM ENUM SO THE ABBREVIATION MATCHES THE ONE CARDS USE.
        showdown_team = ShowdownTeam.map_from_mlb_api_team(abbreviation)
        if showdown_team is not None and showdown_team != ShowdownTeam.MLB:
            abbreviation = showdown_team.value
        return SimTeamIdentity(
            abbreviation=abbreviation,
            name=team.get('name') or abbreviation,
            primary_color=team.get('primary_color'),
            secondary_color=team.get('secondary_color'),
        )

    def _roster_ids(self, side: str) -> dict[str, dict]:
        """Every player available to a side: the active roster, plus anyone already in the game.

        The roster call is not optional - the boxscore never lists an unused reliever (its pitcher
        rows are dropped when there are no pitching stats), so without it the sim would go into
        the 7th with an empty bullpen.
        """

        players: dict[str, dict] = {}
        team = self._team_node(side).get('team') or {}
        team_id = team.get('id')
        abbreviation = team.get('abbreviation') or ''

        if team_id:
            try:
                # THE DATE IS LOAD-BEARING: WITHOUT IT THE ACTIVE ROSTER IS EVERYONE WHO WAS ACTIVE
                # AT ANY POINT IN THE SEASON (70+ PLAYERS), NOT THE 26 AVAILABLE TONIGHT.
                roster = self.mlb_stats_api.teams.get_team_roster(
                    team_id=int(team_id), season=str(self.season), date=self.game_date.isoformat(),
                    roster_type=RosterTypeEnum.ACTIVE,
                )
                for slot in roster.roster:
                    players[str(slot.person.id)] = {
                        'name': slot.person.full_name or '',
                        'is_pitcher': slot.is_pitcher,
                        'position': (slot.position.abbreviation or '').upper(),
                        'team': abbreviation,
                    }
            except Exception:
                pass  # A ROSTER THAT WON'T LOAD STILL LEAVES EVERYONE IN THE BOXSCORE BELOW

        # ANYONE IN THE BOXSCORE IS PLAYING TONIGHT WHETHER OR NOT THE ACTIVE ROSTER AGREES.
        node = self._team_node(side)
        for row in (node.get('batting') or []):
            players.setdefault(str(row.get('id')), {
                'name': row.get('name') or '', 'is_pitcher': False,
                'position': self._current_position(row.get('position')), 'team': abbreviation,
            })
        for row in (node.get('pitching') or []):
            players[str(row.get('id'))] = {
                'name': row.get('name') or '', 'is_pitcher': True,
                'position': 'RP', 'team': abbreviation,
            }

        probable = ((self.boxscore.get('probable_pitchers') or {}).get(side) or {})
        if probable.get('id') is not None:
            players[str(probable['id'])] = {
                'name': probable.get('full_name') or '', 'is_pitcher': True,
                'position': 'SP', 'team': abbreviation,
            }

        players.pop('None', None)
        return players

    @staticmethod
    def _current_position(position: Optional[str]) -> str:
        """The boxscore joins every position a player has held tonight, oldest first ("1B-PH").

        Walks back from the most recent for the first real fielding position, because the chain
        often ends in a non-fielding role ("PH", "PR") that names no defensive slot - taking the
        last entry blindly would leave a pinch-hitter who then took the field unplaceable.
        """

        parts = [part.strip().upper() for part in (position or '').split('-') if part.strip()]
        if not parts:
            return ''
        return next((part for part in reversed(parts) if part in FIELD_POSITION_TO_SLOT), parts[-1])

    def _announced_lineup(self, side: str) -> list[MLBGameLineupSlot]:
        """The nine currently in the batting order, or empty if MLB hasn't posted one.

        `is_in_lineup` tracks MLB's own `battingOrder` array, which holds the *current* occupant
        of each spot - so mid-game this returns whoever is batting there now, not the starter.
        """

        by_slot: dict[int, tuple[int, dict]] = {}
        for row in (self._team_node(side).get('batting') or []):
            if not row.get('is_in_lineup'):
                continue
            try:
                raw_order = int(row.get('batting_order') or 0)
            except (TypeError, ValueError):
                continue
            slot = raw_order // _BATTING_ORDER_SLOT_DIVISOR
            if not 1 <= slot <= 9:
                continue
            # THE SUFFIX COUNTS SUBSTITUTIONS IN THAT SPOT; THE HIGHEST IS THE CURRENT OCCUPANT.
            if slot not in by_slot or raw_order > by_slot[slot][0]:
                by_slot[slot] = (raw_order, row)

        return [
            MLBGameLineupSlot(
                batting_order=slot,
                player_id=str(by_slot[slot][1].get('id')),
                name=by_slot[slot][1].get('name') or '',
                position=self._current_position(by_slot[slot][1].get('position')),
            )
            for slot in sorted(by_slot)
        ]

    def _starting_pitcher_id(self, side: str) -> str:
        """The arm the sim starts with: whoever is actually pitching, else the game's starter,
        else the probable."""

        if self.is_live:
            current = ((self.boxscore.get('linescore') or {}).get('defense') or {}).get('pitcher')
            # THE DEFENSE IS THE SIDE *NOT* BATTING, SO IT ONLY NAMES THIS TEAM'S PITCHER HALF THE TIME.
            pitching_ids = [str(row.get('id')) for row in (self._team_node(side).get('pitching') or [])]
            if current and str(current.get('id')) in pitching_ids:
                return str(current['id'])
            if pitching_ids:
                return pitching_ids[-1]

        pitching = self._team_node(side).get('pitching') or []
        if pitching:
            return str(pitching[0].get('id'))

        probable = ((self.boxscore.get('probable_pitchers') or {}).get(side) or {})
        return str(probable['id']) if probable.get('id') is not None else ''

    def _removed_player_ids(self, side: str) -> set[str]:
        """Position players who appeared and have since been substituted out. They cannot return,
        so they're kept out of the sim's bench."""

        if not self.is_live:
            return set()
        return {
            str(row.get('id'))
            for row in (self._team_node(side).get('batting') or [])
            if not row.get('is_in_lineup')
        }

    # -- ASSEMBLY -----------------------------------------------------------

    def _resolve_cards(self, rosters: dict, lineups: dict, starters: dict) -> MLBGameCardPool:
        pool = self._card_pool(
            season=self.season, showdown_set=self.showdown_set,
            official_date=(self.boxscore.get('datetime') or {}).get('official_date') or '',
        )
        everyone: dict[str, dict] = {}
        for side in SIDES:
            everyone.update(rosters[side])
            # THE ANNOUNCED LINEUP AND THE STARTER MUST RESOLVE EVEN IF THE ROSTER CALL FAILED.
            for slot in lineups[side]:
                everyone.setdefault(slot.player_id, {
                    'name': slot.name, 'is_pitcher': False, 'position': slot.position,
                    'team': self._identity(side).abbreviation,
                })
            if starters[side]:
                everyone.setdefault(starters[side], {
                    'name': '', 'is_pitcher': True, 'position': 'SP',
                    'team': self._identity(side).abbreviation,
                })
        pool.resolve(everyone)
        return pool

    def _card_pool(self, season: int, showdown_set: Set, official_date: str) -> MLBGameCardPool:
        """The pool for this game, created once. `resolve` skips anyone already in it, so calling
        this again after `build_setup` costs nothing."""

        if self._pool is None:
            self._pool = MLBGameCardPool(
                season=season, showdown_set=showdown_set, official_date=official_date, db=self.db,
            )
        return self._pool

    def _option(self, player_id: str, info: dict, pool: MLBGameCardPool, is_unavailable: bool) -> Optional[MLBGamePlayerOption]:
        card = pool.cards.get(player_id)
        if card is None:
            return None
        return MLBGamePlayerOption(
            player_id=player_id,
            name=card.name or info.get('name') or '',
            position=info.get('position') or '',
            is_pitcher=card.is_pitcher,
            points=card.points,
            command=card.chart.command,
            ip=card.ip if card.is_pitcher else None,
            positions_and_defense=card.positions_and_defense_string or '',
            card_origin=pool.origins.get(player_id, CardOrigin.PREBUILT),
            is_unavailable=is_unavailable,
        )

    def _team_setup(
        self, side: str, pool: MLBGameCardPool, roster: dict[str, dict],
        lineup: list[MLBGameLineupSlot], starting_pitcher_id: str, removed_ids: set[str],
    ) -> MLBGameTeamSetup:

        lineup_ids = {slot.player_id for slot in lineup}
        position_players: list[MLBGamePlayerOption] = []
        bullpen: list[MLBGamePlayerOption] = []

        for player_id, info in roster.items():
            # THE CARD DECIDES WHETHER SOMEONE IS AN ARM. THE ROSTER'S OWN FLAG DISAGREES FOR A
            # TWO-WAY PLAYER, WHOSE HITTER CARD IS THE ONE THAT RESOLVED.
            option = self._option(
                player_id, info, pool,
                is_unavailable=player_id in removed_ids and player_id not in lineup_ids,
            )
            if option is None:
                continue
            if option.is_pitcher:
                bullpen.append(option)
            elif not option.is_unavailable:
                position_players.append(option)

        position_players.sort(key=lambda option: option.points, reverse=True)
        bullpen.sort(key=lambda option: option.points, reverse=True)

        return MLBGameTeamSetup(
            side=side,
            team_id=(self._team_node(side).get('team') or {}).get('id'),
            identity=self._identity(side),
            lineup=lineup,
            starting_pitcher_id=starting_pitcher_id,
            position_players=position_players,
            bullpen=bullpen,
        )

    # -- MID-GAME STATE -----------------------------------------------------

    def _build_start_state(self, teams: dict[str, MLBGameTeamSetup]) -> GameStartState:
        linescore = self.boxscore.get('linescore') or {}

        inning = int(linescore.get('current_inning') or 1)
        is_top = bool(linescore.get('is_top_inning', True))
        outs = int(linescore.get('outs') or 0)

        # BETWEEN HALF-INNINGS THE FEED STILL REPORTS THE ONE THAT JUST ENDED. ROLL FORWARD TO THE
        # ONE ABOUT TO BE PLAYED, WHICH IS THE ONLY STATE THE ENGINE CAN RESUME FROM.
        inning_state = str(linescore.get('inning_state') or '').lower()
        if inning_state in _BETWEEN_HALVES or outs >= 3:
            if is_top:
                is_top = False
            else:
                is_top, inning = True, inning + 1
            outs = 0
            runners = Runners()
        else:
            runners = self._inherited_runners(linescore, teams, is_top)

        resume_index = _half_index(inning, is_top)
        completed: list[CompletedHalfInning] = []
        current_half_runs = 0
        for frame in (linescore.get('innings') or []):
            num = int(frame.get('num') or 0)
            if num <= 0:
                continue
            for half_is_top, runs in ((True, (frame.get('away') or {}).get('runs')),
                                      (False, (frame.get('home') or {}).get('runs'))):
                if runs is None:
                    continue
                index = _half_index(num, half_is_top)
                if index < resume_index:
                    completed.append(CompletedHalfInning(inning=num, is_top=half_is_top, runs=int(runs)))
                elif index == resume_index:
                    current_half_runs = int(runs)

        team_totals = linescore.get('teams') or {}
        return GameStartState(
            inning=inning,
            is_top=is_top,
            outs=outs,
            runs=current_half_runs,
            runners=runners,
            completed_innings=completed,
            away=self._team_start_state('away', teams['away'], team_totals.get('away') or {}, inning, outs),
            home=self._team_start_state('home', teams['home'], team_totals.get('home') or {}, inning, outs),
        )

    def _inherited_runners(self, linescore: dict, teams: dict[str, MLBGameTeamSetup], is_top: bool) -> Runners:
        """Runners on base at the takeover.

        The feed does not say which pitcher is charged with an inherited runner, so all of them
        are charged to whoever is on the mound now. That can shift an earned run or two between
        the two pitchers' lines; nothing else in the game is affected.
        """

        offense = linescore.get('offense') or {}
        pitching_side = 'home' if is_top else 'away'
        responsible_pitcher_id = teams[pitching_side].starting_pitcher_id

        # SPEED COMES OFF THE RUNNER'S OWN CARD WHERE IT RESOLVED.
        batting_side = 'away' if is_top else 'home'
        speed_by_id = {option.player_id: option for option in teams[batting_side].position_players}

        runners: list[Runner] = []
        for base, key in ((1, 'first'), (2, 'second'), (3, 'third')):
            person = offense.get(key)
            if not person or person.get('id') is None:
                continue
            player_id = str(person['id'])
            option = speed_by_id.get(player_id)
            runners.append(Runner(
                id=player_id,
                name=person.get('full_name') or (option.name if option else ''),
                base=base,
                speed=_DEFAULT_RUNNER_SPEED,
                pitcher_id=responsible_pitcher_id,
            ))
        return Runners(runners=runners)

    def _team_start_state(
        self, side: str, setup: MLBGameTeamSetup, totals: dict, inning: int, outs: int,
    ) -> TeamStartState:

        current_inning_full = inning + (outs / 3.0)

        # PITCHERS IN ORDER OF ENTRY. THE LAST ONE IS STILL IN THE GAME; THE REST GET AN
        # `end_inning` SO THEY CAN'T BE BROUGHT BACK. WINDOWS ARE RECONSTRUCTED BY WALKING THEIR
        # REAL INNINGS FORWARD - THE FEED NEVER SAYS WHEN EACH ONE ENTERED, AND WHAT THE SIM
        # ACTUALLY READS IS THE WORKLOAD (`end - start`), NOT THE ENTRY POINT.
        rows = self._team_node(side).get('pitching') or []
        appearances: list[PitcherAppearance] = []
        cursor = 1.0
        for index, row in enumerate(rows):
            innings = _ip_to_innings((row.get('stats') or {}).get('innings_pitched'))
            is_current = index == len(rows) - 1
            start = max(1.0, current_inning_full - innings) if is_current else cursor
            appearances.append(PitcherAppearance(
                player_id=str(row.get('id')),
                start_inning=start,
                end_inning=None if is_current else start + innings,
                runs_allowed=int((row.get('stats') or {}).get('earned_runs') or 0),
            ))
            cursor = start + innings

        return TeamStartState(
            runs_scored=int(totals.get('runs') or 0),
            hits=int(totals.get('hits') or 0),
            lineup_index=self._lineup_index(side, setup),
            pitchers_used=appearances,
        )

    def _lineup_index(self, side: str, setup: MLBGameTeamSetup) -> int:
        """Where in the order this side picks back up, as a 0-based index.

        Three sources, most reliable first:
          1. The batting side's current hitter, named outright by the linescore.
          2. The last completed plate appearance this side took, from the play log - the next
             spot is simply the one after it. This is what covers the *fielding* side, whose next
             batter the linescore says nothing about.
          3. Plate appearances counted off the box score, modulo nine. Only a fallback: the box
             score reports no HBP or sacrifices, so it drifts by one per such event.
        """

        linescore = self.boxscore.get('linescore') or {}
        is_batting = bool(linescore.get('is_top_inning', True)) == (side == 'away')
        order_by_id = {slot.player_id: slot.batting_order for slot in setup.lineup}

        if is_batting:
            batter = (linescore.get('offense') or {}).get('batter') or {}
            spot = order_by_id.get(str(batter.get('id')))
            if spot:
                return spot - 1

        for play in reversed(self.boxscore.get('plays') or []):
            about = play.get('about') or {}
            if not (play.get('result') or {}).get('event'):
                continue  # THE AT-BAT IN PROGRESS - NOT YET A COMPLETED TURN
            if bool(about.get('isTopInning')) != (side == 'away'):
                continue
            batter_id = str(((play.get('matchup') or {}).get('batter') or {}).get('id'))
            spot = order_by_id.get(batter_id)
            if spot:
                return spot % 9   # THE SPOT AFTER, WRAPPING 9 -> 0
            break  # THE LAST BATTER ISN'T IN THE CURRENT NINE (PINCH HIT FOR) - FALL THROUGH

        plate_appearances = sum(
            int((row.get('stats') or {}).get('at_bats') or 0) + int((row.get('stats') or {}).get('base_on_balls') or 0)
            for row in (self._team_node(side).get('batting') or [])
        )
        return plate_appearances % 9

    # ------------------------------------------------------------------
    # SIMULATION
    # ------------------------------------------------------------------

    def simulate(self, setup: MLBGameSetup, seed: Optional[int] = None) -> MLBGameSimResult:
        """Play the game out. `setup` is passed in rather than rebuilt so a client can edit a
        lineup between reviewing it and committing to it."""

        if setup.is_final:
            raise ValueError("This game is already over - there is nothing left to simulate.")

        # NORMALLY ALREADY POPULATED BY `build_setup`. RESOLVING AGAINST THE SETUP RATHER THAN
        # TRUSTING IT COVERS THE CASE WHERE THE SETUP MADE A ROUND TRIP THROUGH A CLIENT AND CAME
        # BACK TO A FRESH SIMULATOR.
        pool = self._card_pool(
            season=setup.season, showdown_set=Set(setup.showdown_set), official_date=setup.official_date,
        )
        pool.resolve({
            option.player_id: {
                'name': option.name, 'is_pitcher': option.is_pitcher,
                'position': option.position, 'team': team.identity.abbreviation,
            }
            for team in (setup.away, setup.home)
            for option in (team.position_players + team.bullpen)
        })

        teams = {
            side: self._build_sim_team(getattr(setup, side), pool, setup.season)
            for side in SIDES
        }

        game = Game(
            index=setup.game_pk,
            date=self.game_date,
            home_team_name=setup.home.identity.abbreviation,
            away_team_name=setup.away.identity.abbreviation,
            home_team_game_number=1,
            away_team_game_number=1,
        )
        game.setup(home_team=teams['home'], away_team=teams['away'], start_state=setup.start_state)
        game.simulate(rng=Random(seed), collect_log=True, collect_box_score=True)

        return MLBGameSimResult(
            game_pk=setup.game_pk,
            season=setup.season,
            showdown_set=setup.showdown_set,
            seed=seed,
            is_takeover=setup.is_takeover,
            setup=setup,
            game=game.as_result(),
            real_plays=(self.boxscore.get('plays') or []) if setup.is_takeover else [],
        )

    @staticmethod
    def _build_sim_team(setup: MLBGameTeamSetup, pool: MLBGameCardPool, season: int) -> SimTeam:
        return SimTeam.from_mlb_game_roster(
            year=season,
            cards=pool.cards,
            identity=setup.identity,
            lineup=[(slot.player_id, slot.position) for slot in setup.lineup],
            starting_pitcher_id=setup.starting_pitcher_id,
            position_player_ids=[
                option.player_id for option in setup.position_players if not option.is_unavailable
            ],
            bullpen_ids=[option.player_id for option in setup.bullpen],
            manager=setup.manager,
        )
