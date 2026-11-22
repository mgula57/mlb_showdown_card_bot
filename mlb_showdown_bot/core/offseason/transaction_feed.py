import logging
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from ..card.minor_league_cards import MinorLeagueCardBuilder
from ..card.sets import Set
from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.stats.normalized_player_stats import Datasource
from ..database.postgres_db import PostgresDB, CARD_DATA_DIAGNOSTIC_KEYS
from ..mlb_stats_api import MLBStatsAPI, Transaction, TransactionTypeEnum
from ..mlb_stats_api.models.teams.team import TeamWithColors
from .window import OffseasonWindow

logger = logging.getLogger(__name__)


class MoveKind(str, Enum):
    TRADE = 'trade'
    SIGNING = 'signing'
    FREE_AGENT = 'free_agent'      # elected free agency: left a club, not signed anywhere yet
    WAIVER_CLAIM = 'waiver_claim'


class FeedTeam(BaseModel):
    id: int
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class FeedPlayer(BaseModel):
    """One player in a move. `card` is the player's card from the season before, in the requested set.

    A player with no big-league card that year may get a minor-league one instead
    (`is_minor_league`). Its points stay off `points`, so a prospect never counts toward a move's
    total or a club's net change - those are about the cards the sim plays with.
    """

    mlb_id: int
    name: Optional[str] = None
    from_team_id: Optional[int] = None
    to_team_id: Optional[int] = None
    points: Optional[int] = None
    card: Optional[dict] = None
    # Id of a stored big-league card. `card` is slimmed for the feed, so the detail view fetches
    # the full card by this id. None for a minor-league card, which is built on the fly.
    card_id: Optional[str] = None
    is_minor_league: bool = False


class FeedMove(BaseModel):
    id: str
    kind: MoveKind
    date: Optional[str] = None
    description: Optional[str] = None
    team_ids: list[int]
    players: list[FeedPlayer]
    # A signing back with the club the player's card is on.
    is_re_signing: bool = False

    @property
    def total_points(self) -> int:
        return sum(player.points or 0 for player in self.players)

    @property
    def has_cards(self) -> bool:
        return any(player.card for player in self.players)

    @property
    def has_mlb_cards(self) -> bool:
        return any(player.card and not player.is_minor_league for player in self.players)


class TeamNetChange(BaseModel):
    """Card points a club has gained and lost over the window, by where each player started and ended."""

    team_id: int
    points_in: int = 0
    points_out: int = 0
    players_in: int = 0
    players_out: int = 0

    @property
    def net(self) -> int:
        return self.points_in - self.points_out


class TransactionFeed(BaseModel):
    season: int
    card_year: int
    showdown_set: str
    window_start: Optional[date] = None
    window_end: Optional[date] = None
    # Moves with at least one carded player, newest first.
    moves: list[FeedMove] = []
    # Major-league moves where nobody has a card (international signings, players who missed the
    # card year). Kept so a notable signing doesn't vanish just because there's no card for him.
    other_moves: list[FeedMove] = []
    team_changes: list[TeamNetChange] = []
    teams: dict[int, FeedTeam] = {}

    def filtered(self, team_id: Optional[int] = None, since: Optional[date] = None, sort: str = 'date', limit: Optional[int] = None) -> 'TransactionFeed':
        """A narrowed copy of the feed.

        Args:
            team_id: Only moves involving this club, and only its net change.
            since: Only moves on or after this date. `team_changes` still covers the whole window.
            sort: 'date' (newest first, the default) or 'points' (biggest card points first).
            limit: Cap on `moves`. Applies after sorting; `other_moves` is capped the same way.
        """
        def keep(move: FeedMove) -> bool:
            if team_id is not None and team_id not in move.team_ids:
                return False
            return since is None or (move.date or '') >= since.isoformat()

        def arrange(moves: list[FeedMove]) -> list[FeedMove]:
            moves = [m for m in moves if keep(m)]
            if sort == 'points':
                moves = sorted(moves, key=lambda m: (m.total_points, m.date or ''), reverse=True)
            return moves[:limit] if limit is not None else moves

        return self.model_copy(update={
            'moves': arrange(self.moves),
            'other_moves': arrange(self.other_moves),
            'team_changes': [c for c in self.team_changes if team_id is None or c.team_id == team_id],
        })

    def as_json(self) -> dict:
        def move_json(move: FeedMove) -> dict:
            return {**move.model_dump(mode='json'), 'total_points': move.total_points}

        return {
            'season': self.season,
            'card_year': self.card_year,
            'showdown_set': self.showdown_set,
            'window_start': self.window_start.isoformat() if self.window_start else None,
            'window_end': self.window_end.isoformat() if self.window_end else None,
            'moves': [move_json(m) for m in self.moves],
            'other_moves': [move_json(m) for m in self.other_moves],
            'team_changes': [{**c.model_dump(), 'net': c.net} for c in self.team_changes],
            'teams': {str(team_id): team.model_dump() for team_id, team in self.teams.items()},
        }


class TransactionFeedBuilder:
    """Turns the MLB transactions firehose for an offseason into the moves that matter for Showdown.

    The raw feed is mostly roster churn (~400 rows in the first two weeks of an offseason, most of
    them minor-league deals and assignments). This keeps trades, major-league free-agent signings,
    elected free agency and waiver claims, attaches each player's card from the year before, and
    sorts the result into carded moves and everything else.
    """

    _KEPT_TYPES = {t.value for t in TransactionTypeEnum}
    # Moves that only make the feed when the player has a card. Elected free agency and waiver
    # claims are dominated by fringe 40-man players; a trade or major-league signing is news either way.
    _CARD_REQUIRED_KINDS = {MoveKind.FREE_AGENT, MoveKind.WAIVER_CLAIM}

    # A feed card only has to render a card item and open its detail view: the UI-only diagnostics
    # and per-game logs are ~75% of a full payload, and a feed carries hundreds of cards.
    _GAME_LOGS_EXCLUDE = {'stats': {'game_logs': True, 'postseason_game_logs': True}}
    _CARD_JSON_EXCLUDE = {
        **{key: True for key in CARD_DATA_DIAGNOSTIC_KEYS},
        **_GAME_LOGS_EXCLUDE,
    }

    def __init__(self, mlb_stats_api: MLBStatsAPI, sport_id: int = 1):
        self.api = mlb_stats_api
        self.sport_id = sport_id

    def build(self, season: int, showdown_set: str) -> TransactionFeed:
        # Always the season before, even once `season` has its own cards: an offseason move is
        # judged by the player's last full season.
        card_year = season - 1
        window = OffseasonWindow.for_season(season=season, mlb_stats_api=self.api)
        feed = TransactionFeed(season=season, card_year=card_year, showdown_set=showdown_set)
        if window is None or window.start_date > date.today():
            return feed
        feed.window_start, feed.window_end = window.start_date, window.end_date

        transactions = [
            t for t in self.api.transactions.get_transactions(
                start_date=window.start_date.isoformat(),
                end_date=window.query_end_date.isoformat(),
                sport_id=self.sport_id,
            )
            if t.type_code in self._KEPT_TYPES and not t.is_minor_league_deal
        ]

        cards = self._fetch_cards(transactions, card_year=card_year, showdown_set=showdown_set)
        teams = self._fetch_teams(season=season)
        team_id_by_card_team = {t.abbreviation_bref: t.id for t in teams.values() if t.abbreviation_bref}

        moves = self._group_moves(transactions)
        minor_league_cards = self._fetch_minor_league_cards(moves, cards=cards, card_year=card_year, showdown_set=showdown_set)
        for move in moves:
            self._attach_cards(move, cards=cards, minor_league_cards=minor_league_cards, team_id_by_card_team=team_id_by_card_team)

        kept: list[FeedMove] = []
        other: list[FeedMove] = []
        for move in moves:
            # A minor-league card alone doesn't carry an elected-free-agency or waiver row: those
            # are mostly fringe 40-man arms, and only make the feed with a big-league card.
            if move.has_mlb_cards or (move.has_cards and move.kind not in self._CARD_REQUIRED_KINDS):
                kept.append(move)
            elif move.kind not in self._CARD_REQUIRED_KINDS:
                other.append(move)

        newest_first = lambda m: (m.date or '', m.id)
        feed.moves = sorted(kept, key=newest_first, reverse=True)
        feed.other_moves = sorted(other, key=newest_first, reverse=True)
        feed.team_changes = self._team_changes(kept)
        feed.teams = {team_id: team.feed_team for team_id, team in teams.items()}
        return feed

    # ------------------------------------------------------------------
    # STEPS
    # ------------------------------------------------------------------

    def _fetch_cards(self, transactions: list[Transaction], card_year: int, showdown_set: str) -> dict[int, ShowdownPlayerCard]:
        mlb_ids = sorted({t.person.id for t in transactions if t.person})
        if not mlb_ids:
            return {}
        with PostgresDB() as db:
            by_player_id = db.fetch_cards_for_player_ids(
                player_ids=[f"{card_year}-{mlb_id}" for mlb_id in mlb_ids],
                showdown_set=showdown_set,
                source=Datasource.MLB_API,
            )
        return {
            int(player_id.split('-', 1)[1]): card
            for player_id, card in by_player_id.items()
            if card is not None
        }

    def _fetch_minor_league_cards(self, moves: list[FeedMove], cards: dict[int, ShowdownPlayerCard], card_year: int, showdown_set: str) -> dict[int, ShowdownPlayerCard]:
        """Minor-league cards for the uncarded players in trades and signings - the prospects and
        depth pieces a deal sends along. One batched MLB API call per year tried."""
        mlb_ids = [
            player.mlb_id
            for move in moves if move.kind in (MoveKind.TRADE, MoveKind.SIGNING)
            for player in move.players if player.mlb_id not in cards
        ]
        if not mlb_ids:
            return {}
        try:
            # A PROSPECT'S FULL MINOR-LEAGUE LINE SHOWS AS IT IS; ONLY A THIN SEASON, WHICH RUNS HOT, IS NERFED
            return MinorLeagueCardBuilder(mlb_stats_api=self.api).build_many(mlb_ids=mlb_ids, year=card_year, set=Set(showdown_set), nerf_small_samples_only=True)
        except Exception:
            # A minor-league card is a nice-to-have on the feed; never fail the feed over one.
            logger.exception("Couldn't build minor-league cards for the transaction feed")
            return {}

    def _fetch_teams(self, season: int) -> dict[int, '_ResolvedTeam']:
        teams: dict[int, _ResolvedTeam] = {}
        for api_team in self.api.teams.get_teams(sport_id=self.sport_id, season=season):
            with_colors = TeamWithColors(**api_team.model_dump())
            with_colors.load_colors_from_showdown_team()
            teams[api_team.id] = _ResolvedTeam(
                id=api_team.id,
                abbreviation_bref=api_team.bref_team(year=season),
                feed_team=FeedTeam(
                    id=api_team.id,
                    name=api_team.name,
                    abbreviation=api_team.abbreviation,
                    primary_color=with_colors.primary_color,
                    secondary_color=with_colors.secondary_color,
                ),
            )
        return teams

    def _group_moves(self, transactions: list[Transaction]) -> list[FeedMove]:
        """One move per trade (its legs share an id) and one per every other transaction."""
        trades: dict[int, list[Transaction]] = {}
        moves: list[FeedMove] = []
        for t in transactions:
            if t.type_code == TransactionTypeEnum.TRADE.value:
                trades.setdefault(t.id, []).append(t)
                continue
            if not t.person:
                continue
            match t.type_code:
                case TransactionTypeEnum.SIGNED_FREE_AGENT.value:
                    kind, from_team, to_team = MoveKind.SIGNING, None, t.to_team
                case TransactionTypeEnum.DECLARED_FREE_AGENCY.value:
                    # MLB puts the club the player left in `toTeam` here.
                    kind, from_team, to_team = MoveKind.FREE_AGENT, t.to_team or t.from_team, None
                case _:
                    kind, from_team, to_team = MoveKind.WAIVER_CLAIM, t.from_team, t.to_team
            player = FeedPlayer(
                mlb_id=t.person.id,
                name=t.person.full_name,
                from_team_id=from_team.id if from_team else None,
                to_team_id=to_team.id if to_team else None,
            )
            moves.append(FeedMove(
                id=f"{t.type_code}-{t.id}",
                kind=kind,
                date=t.date,
                description=t.description,
                team_ids=[team_id for team_id in (player.from_team_id, player.to_team_id) if team_id],
                players=[player],
            ))

        for trade_id, legs in trades.items():
            players: dict[int, FeedPlayer] = {}
            team_ids: list[int] = []
            for leg in legs:
                for team in (leg.from_team, leg.to_team):
                    if team and team.id not in team_ids:
                        team_ids.append(team.id)
                if leg.person and leg.person.id not in players:
                    players[leg.person.id] = FeedPlayer(
                        mlb_id=leg.person.id,
                        name=leg.person.full_name,
                        from_team_id=leg.from_team.id if leg.from_team else None,
                        to_team_id=leg.to_team.id if leg.to_team else None,
                    )
            if not players:
                continue
            moves.append(FeedMove(
                id=f"TR-{trade_id}",
                kind=MoveKind.TRADE,
                date=legs[0].date,
                description=legs[0].description,
                team_ids=team_ids,
                players=list(players.values()),
            ))
        return moves

    @classmethod
    def _attach_cards(cls, move: FeedMove, cards: dict[int, ShowdownPlayerCard], minor_league_cards: dict[int, ShowdownPlayerCard],
                      team_id_by_card_team: dict[str, int]) -> None:
        for player in move.players:
            card = cards.get(player.mlb_id)
            if card is None:
                minor_league_card = minor_league_cards.get(player.mlb_id)
                if minor_league_card is not None:
                    # KEEPS ITS DIAGNOSTICS: A MINOR-LEAGUE CARD IS BUILT ON THE FLY, SO THE DETAIL VIEW
                    # CAN'T FETCH IT BY ID LIKE A STORED CARD (`card_id`). A FEED HAS ONLY A DOZEN OR SO.
                    player.card = minor_league_card.as_json(exclude=cls._GAME_LOGS_EXCLUDE)
                    player.is_minor_league = True
                continue
            player.points = card.points
            player.card = card.as_json(exclude=cls._CARD_JSON_EXCLUDE)
            player.card_id = PostgresDB.dim_card_id(card)
            # A free agent's previous club isn't in the signing row - it's the club on his card.
            if move.kind == MoveKind.SIGNING and player.from_team_id is None and card.team:
                player.from_team_id = team_id_by_card_team.get(card.team.value)
                if player.from_team_id and player.from_team_id not in move.team_ids:
                    move.team_ids.insert(0, player.from_team_id)
        if move.kind == MoveKind.SIGNING:
            player = move.players[0]
            move.is_re_signing = player.from_team_id is not None and player.from_team_id == player.to_team_id

    @staticmethod
    def _team_changes(moves: list[FeedMove]) -> list[TeamNetChange]:
        """Net card points per club, from where each carded player started the window to where he is now.

        Walking a player's moves in date order and only comparing the ends keeps a player who
        elected free agency and then signed elsewhere from being counted as two departures, and
        makes a re-signing a no-op.
        """
        journeys: dict[int, tuple[Optional[int], Optional[int], int]] = {}  # mlb_id -> (start club, current club, points)
        for move in sorted(moves, key=lambda m: (m.date or '', m.id)):
            for player in move.players:
                if not player.card or player.is_minor_league:
                    continue
                start, _, _ = journeys.get(player.mlb_id, (player.from_team_id, None, 0))
                journeys[player.mlb_id] = (start, player.to_team_id, player.points or 0)

        changes: dict[int, TeamNetChange] = {}
        for start, end, points in journeys.values():
            if start == end:
                continue
            if start is not None:
                change = changes.setdefault(start, TeamNetChange(team_id=start))
                change.points_out += points
                change.players_out += 1
            if end is not None:
                change = changes.setdefault(end, TeamNetChange(team_id=end))
                change.points_in += points
                change.players_in += 1
        return sorted(changes.values(), key=lambda c: c.net, reverse=True)


class _ResolvedTeam(BaseModel):
    id: int
    abbreviation_bref: Optional[str] = None
    feed_team: FeedTeam
