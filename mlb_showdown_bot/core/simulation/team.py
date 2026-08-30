from datetime import date
from random import Random
from typing import Optional

from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.team_builder.team import BULLPEN_ROLES, ROTATION_ROLES, Team as BuilderTeam
from ..shared.player_position import PlayerType, PositionSlot
from ..shared.team import Team as ShowdownTeam
from .game import Game
from .inning import Inning
from .models import NEUTRAL_MANAGER, ManagerPreference, SimTeamIdentity, TeamRecord, TeamStartState
from .player import SimPitcher, SimPlayer
from .player_group import Bullpen, PositionEligibility, Rotation
from .roster import Roster
from .stats import StatCategory, Stats, StatsGroup

# LINEUP FIELD POSITIONS -> SIM POSITION SLOTS. THE VOCABULARY A LINEUP CAN BE EXPRESSED IN,
# SHARED BY BUILDER TEAMS AND REAL MLB GAMES.
FIELD_POSITION_TO_SLOT = {
    "C": PositionSlot.CA,
    "CA": PositionSlot.CA,
    "1B": PositionSlot._1B,
    "2B": PositionSlot._2B,
    "3B": PositionSlot._3B,
    "SS": PositionSlot.SS,
    "LF": PositionSlot.LF,
    "CF": PositionSlot.CF,
    "RF": PositionSlot.RF,
    "DH": PositionSlot.DH,
}

# BONUS ADDED TO REST RATING FOR PLAYERS IN A BUILDER TEAM'S PRESET LINEUP.
# LARGE ENOUGH THAT PRESET STARTERS ALMOST ALWAYS PLAY, SMALL ENOUGH THAT AN
# EXHAUSTED STARTER EVENTUALLY GIVES WAY TO THE BENCH.
_PRESET_LINEUP_BONUS = 300.0


def _rgb_string(color: tuple) -> str:
    return f"rgb({color[0]}, {color[1]}, {color[2]})"


def _apply_preset_lineup(position_players: list[SimPlayer], lineup_by_id: dict[str, tuple[int, str]]) -> None:
    """Pin players to a chosen batting order and field position.

    `_player_for_slot` adds `_PRESET_LINEUP_BONUS` to anyone whose `preset_position_slot` matches
    the slot being filled, and `generate_batting_order` honors `preset_lineup_spot` outright, so
    setting these is all it takes to make an explicit lineup - a builder team's, or a real game's
    announced one - come out of the ordinary lineup machinery unchanged.

    Args:
      lineup_by_id: player id -> (batting order 1-9, field position abbreviation).
    """

    for player in position_players:
        entry = lineup_by_id.get(player.id)
        if entry is None:
            continue
        batting_order, field_position = entry
        player.preset_lineup_spot = batting_order
        player.preset_position_slot = FIELD_POSITION_TO_SLOT.get(field_position.upper())


class SimTeam:

    def __init__(
        self, year: int, name: str, position_players: list[SimPlayer], rotation: Rotation, bullpen: Bullpen,
        league: str = None, bench_pts_multiplier: float = 1.0, bench_player_ids: Optional[set[str]] = None,
        manager: Optional[ManagerPreference] = None,
    ) -> None:
        self.year = year
        self.name = name
        self.league = league
        self.identity = SimTeamIdentity(abbreviation=name, name=name, league=league)

        # PER-RUN MANAGER TENDENCIES. NEUTRAL FOR EVERY REAL CLUB; SET ONLY FOR A USER'S TAKEOVER
        # TEAM (SEASON/OPEN SIM) OR EITHER SIDE OF A SINGLE-GAME SIM. NEUTRAL IS A NO-OP.
        self.manager = manager or NEUTRAL_MANAGER

        self.position_players = position_players
        self.rotation = rotation
        self.bullpen = bullpen

        # 40-MAN ROSTER / INJURIES. ONLY SET FOR REAL-SEASON TEAMS (`from_player_pool`) - BUILDER/
        # TOURNAMENT TEAMS (`from_builder_team`) LEAVE THIS `None`, WHICH IS THE SCOPE GUARD EVERY
        # ROSTER/INJURY HOOK CHECKS.
        self.roster: Optional[Roster] = None
        self._last_roster_date: Optional[date] = None

        self.points = sum([player.points for player in self.active_players])

        # BENCH DISCOUNT, AS APPLIED AT DRAFT TIME (`Team.bench_pts_multiplier`). ONLY SET FOR
        # BUILDER/TOURNAMENT TEAMS (`from_builder_team`) - REAL-SEASON TEAMS HAVE NO SUCH CONCEPT,
        # SO THE MULTIPLIER STAYS AT ITS 1.0 NO-OP DEFAULT AND `bench_player_ids` STAYS EMPTY.
        self.bench_pts_multiplier = bench_pts_multiplier
        self.bench_player_ids: set[str] = bench_player_ids or set()

        # CURRENT GAME STATE. REBUILT EACH GAME IN `add_new_game` - THE LINEUP IS FIXED FOR A WHOLE
        # GAME (NO DEFENSIVE SUBS), SO POSITION/DEFENSE LOOKUPS ARE COMPUTED ONCE PER GAME.
        self.starting_lineup: list[SimPlayer] = []
        self.batting_order: list[SimPlayer] = []
        self.current_game_stats: Stats = Stats(id="0")
        self.game_player_appearances: set[str] = set()
        self.position_map: dict[PositionSlot, SimPlayer] = {}
        self.infield_defense: int = 0
        self.outfield_defense: int = 0
        self.catcher: Optional[SimPlayer] = None
        self.available_reliever_ids: set[str] = set()

        # GAMES
        self.lineup_index = 0
        self.stats = StatsGroup(year=year)
        self.wins = 0
        self.losses = 0
        # CONSECUTIVE GAMES STARTED PER PLAYER ID, MAINTAINED INCREMENTALLY FOR REST DECISIONS
        self.consecutive_starts: dict[str, int] = {}
        self.playoff_seeding = None
        if len(self.all_players) == 0:
            raise ValueError(f'ERROR: No players for team {self.name}')

    # ------------------------------------------------------------------
    # CONSTRUCTION
    # ------------------------------------------------------------------

    @classmethod
    def from_player_pool(
        cls, year: int, name: str, cards: list[ShowdownPlayerCard], league: str = None,
        card_ids: dict[str, str] = {},
        min_pa: int = 100, min_ip_sp: int = 50, min_ip_rp: int = 30,
        active_roster_size: int = 26, full_roster_size: int = 40, enable_injuries: bool = False,
        games_per_season: int = 162,
    ) -> 'SimTeam':
        """Auto-build a roster from a pool of cards (a real season's team).

        Builds a `full_roster_size`-man pool, of which `active_roster_size` are active (13
        position players, 5 SP, 8 RP by default) and the rest are reserves available for callup.

        Args:
          card_ids: `ShowdownPlayerCard.id -> card_bot.card_id`, from `PlayerLoader.load_season_cards`.
            Lets each player's statline carry the id its real card is actually archived under -
            see `Roster.select`.
        """

        selection = Roster.select(
            cards=cards, card_ids=card_ids, min_pa=min_pa, min_ip_sp=min_ip_sp, min_ip_rp=min_ip_rp,
            active_size=active_roster_size, full_size=full_roster_size, games_per_season=games_per_season,
        )

        team = cls(
            year=year,
            name=name,
            position_players=selection.position_players,
            rotation=Rotation(players=selection.rotation),
            bullpen=Bullpen(players=selection.bullpen),
            league=league,
        )
        team.roster = Roster(team_name=name, selection=selection, enable_injuries=enable_injuries)

        # TEAM BRANDING - YEAR-AWARE SO A HISTORICAL SIM SHOWS THE ERA-APPROPRIATE COLORS, NOT
        # TODAY'S. `Team._missing_` FALLS BACK TO `Team.MLB` FOR AN UNRECOGNIZED ABBREVIATION
        # RATHER THAN RAISING, SO IDENTITY RESOLUTION CAN NEVER FAIL A SIM.
        showdown_team = ShowdownTeam(name)
        team.identity = SimTeamIdentity(
            abbreviation=name,
            name=name,
            primary_color=_rgb_string(showdown_team.color(year=year)),
            secondary_color=_rgb_string(showdown_team.color(year=year, is_secondary=True)),
            league=league,
        )
        return team

    @classmethod
    def from_builder_team(cls, team: BuilderTeam, cards: dict[str, ShowdownPlayerCard], year: int, league: str = None, name_override: str = None, manager: Optional[ManagerPreference] = None) -> 'SimTeam':
        """Build from a user-created team_builder Team, honoring its explicit lineup and pitcher roles.

        Args:
          team: The builder team (roster slots, lineups, rotation assignments).
          cards: Hydrated cards keyed by roster slot card_id.
          year: Sim year (used for stat grouping only).
          league: League/tournament label.
          name_override: Schedule key to run under instead of the team's own abbreviation. Used by
            season takeover, where the team occupies a real club's slot and every schedule,
            standings, and division lookup keys off that club's abbreviation. Display identity
            (name/colors) is unaffected.
        """

        position_players: list[SimPlayer] = []
        sp_players: dict[str, SimPitcher] = {}
        bullpen_players: dict[str, SimPitcher] = {}

        # EVERY STATLINE REPORTS THE BUILDER TEAM RATHER THAN THE CLUB THE CARD REALLY PLAYED FOR.
        # NOTE THIS IS THE TEAM'S OWN ABBREVIATION, NOT `name_override` - A TAKEOVER RUNS UNDER THE
        # REPLACED CLUB'S SCHEDULE KEY, BUT ITS PLAYERS BELONG TO THE USER'S TEAM.
        team_abbreviation = team.abbreviation

        # ROSTER POSITIONS ARE THE CANONICAL SOURCE FOR PITCHER ROLES - `Team.from_db_row` DERIVES
        # `rotation` FROM THEM. THE VOCABULARY IS SP1-SP5 AND RP/CL, NEVER A BARE "SP".
        for slot in team.roster:
            card = cards.get(slot.card_id)
            if card is None:
                continue
            roster_position = slot.roster_position.upper()
            if roster_position in ROTATION_ROLES:
                sp_players[slot.card_id] = SimPitcher(card=card, id=slot.card_id, position_slot=PositionSlot.SP, team_override=team_abbreviation)
            elif roster_position in BULLPEN_ROLES:
                bullpen_players[slot.card_id] = SimPitcher(card=card, id=slot.card_id, position_slot=PositionSlot.BP, team_override=team_abbreviation)
            else:
                position_players.append(SimPlayer(card=card, id=slot.card_id, team_override=team_abbreviation))

        # ROTATION ORDER FROM THE SP1..SP5 SLOT NUMBERS
        sp_slot_by_card_id = {slot.card_id: slot.roster_position.upper() for slot in team.roster if slot.roster_position.upper() in ROTATION_ROLES}
        rotation_players = [sp_players[card_id] for card_id in sorted(sp_players, key=lambda cid: int(sp_slot_by_card_id[cid][2:]))]

        # THE 'CL' SLOT IS THE CLOSER. THE BUILDER HAS NO SETUP/MIDDLE/LONG ROLES, SO THE REST OF
        # THE BULLPEN IS LEFT TO `pitchers_available`'s OPS-BASED LEVERAGE SORT.
        closer_id: Optional[str] = next(
            (slot.card_id for slot in team.roster if slot.roster_position.upper() == 'CL' and slot.card_id in bullpen_players),
            None,
        )

        # PRESET LINEUP (FIRST DEFINED LINEUP)
        if len(team.lineups) > 0:
            _apply_preset_lineup(position_players, {
                slot.card_id: (slot.batting_order, slot.field_position)
                for slot in team.lineups[0].slots
            })

        bench_player_ids = {slot.card_id for slot in team.roster if slot.roster_position.upper() == 'BE'}

        sim_team = cls(
            year=year,
            name=name_override or team.abbreviation,
            position_players=position_players,
            rotation=Rotation(players=rotation_players),
            bullpen=Bullpen(players=list(bullpen_players.values()), closer_id=closer_id),
            league=league,
            bench_pts_multiplier=team.bench_pts_multiplier,
            bench_player_ids=bench_player_ids,
            manager=manager,
        )
        # BUILDER TEAMS CARRY THEIR OWN USER-CHOSEN COLORS - NOT RESOLVED VIA THE ShowdownTeam
        # ENUM, SINCE A BUILDER ABBREVIATION (E.G. "MYTM") ISN'T A MEMBER OF IT.
        sim_team.identity = SimTeamIdentity(
            abbreviation=team.abbreviation,
            name=team.name,
            primary_color=team.primary_color,
            secondary_color=team.secondary_color,
            league=league,
        )
        return sim_team

    @classmethod
    def from_mlb_game_roster(
        cls, year: int, cards: dict[str, ShowdownPlayerCard], identity: SimTeamIdentity,
        lineup: list[tuple[str, str]], starting_pitcher_id: str,
        position_player_ids: list[str], bullpen_ids: list[str], league: str = None,
        manager: Optional[ManagerPreference] = None,
    ) -> 'SimTeam':
        """Build one side of a real MLB game.

        Unlike a season team there is no roster selection to do - the participants are known. The
        lineup, when MLB has published one, is pinned through `_apply_preset_lineup` so it comes
        out of the normal lineup machinery verbatim. Pass an empty `lineup` and the whole position
        pool is up for selection by `fill_starting_position_players`, which is the path taken
        before lineups are announced.

        Args:
          cards: Hydrated cards keyed by MLB player id (as a string).
          identity: Branding, and the club every statline reports.
          lineup: (player_id, field position) in batting order, 1st through 9th. May be empty.
          starting_pitcher_id: The probable/actual starter. Becomes the whole rotation - a single
            game has exactly one turn in it.
          position_player_ids: Every position player available, starters included. The lineup is
            pinned on top of this pool rather than being separate from it, so it may be passed
            whole (a full roster) without pre-subtracting the nine.
          bullpen_ids: Every available arm. The starter is skipped if it appears here too.
        """

        lineup_ids = [player_id for player_id, _ in lineup]
        abbreviation = identity.abbreviation

        def build(player_id: str, is_pitcher: bool) -> Optional[SimPlayer]:
            card = cards.get(player_id)
            if card is None:
                return None
            if is_pitcher:
                slot = PositionSlot.SP if player_id == starting_pitcher_id else PositionSlot.BP
                return SimPitcher(card=card, id=player_id, position_slot=slot, team_override=abbreviation)
            return SimPlayer(card=card, id=player_id, team_override=abbreviation)

        # LINEUP FIRST, THEN THE REST OF THE POOL. `dict.fromkeys` DEDUPES WHILE KEEPING THAT ORDER,
        # WHICH MATTERS BECAUSE THE POOL NORMALLY CONTAINS THE STARTING NINE TOO.
        position_ids = list(dict.fromkeys(lineup_ids + list(position_player_ids)))
        position_players = [player for pid in position_ids if (player := build(pid, is_pitcher=False))]

        starter = build(starting_pitcher_id, is_pitcher=True)
        relievers = [
            pitcher for pid in bullpen_ids
            if pid != starting_pitcher_id and (pitcher := build(pid, is_pitcher=True))
        ]

        if starter is None:
            # NO CARD FOR THE ANNOUNCED STARTER - PROMOTE THE BEST AVAILABLE ARM RATHER THAN
            # FAILING THE WHOLE GAME.
            if not relievers:
                raise ValueError(f'ERROR: No pitchers with cards for {abbreviation}')
            starter = relievers.pop(0)
            starter.position_slot = PositionSlot.SP

        _apply_preset_lineup(position_players, {
            player_id: (order, field_position)
            for order, (player_id, field_position) in enumerate(lineup, start=1)
        })

        sim_team = cls(
            year=year,
            name=abbreviation,
            position_players=position_players,
            rotation=Rotation(players=[starter]),
            bullpen=Bullpen(players=relievers),
            league=league,
            manager=manager,
        )
        sim_team.identity = identity
        return sim_team

    # ------------------------------------------------------------------
    # ROSTER / LINEUP
    # ------------------------------------------------------------------

    @property
    def active_players(self) -> list[SimPlayer]:
        """The 26-man active roster. For builder/tournament teams (no `Roster`) this is the whole team."""
        return (self.position_players + self.rotation.players + self.bullpen.players)

    @property
    def all_players(self) -> list[SimPlayer]:
        """Active roster plus reserves (the full 40-man). Includes reserves so `PlayerStatsGroup`
        seeds identity statlines for anyone who might be called up mid-season."""
        return self.active_players + (self.roster.reserves if self.roster else [])

    def num_players_valid_per_position(self, player_list: list[SimPlayer], current_lineup_dict: dict[str, PositionSlot] = None) -> dict[PositionSlot, float]:
        return PositionEligibility.counts_by_slot(players=player_list, current_lineup_dict=current_lineup_dict)

    def filter_players_w_eligibility(self, player_list: list[SimPlayer], position_slot: PositionSlot, excluded_player_ids: list[str] = None) -> list[SimPlayer]:
        return PositionEligibility.players_for_slot(players=player_list, position_slot=position_slot, excluded_player_ids=excluded_player_ids)

    def _player_for_slot(self, position: PositionSlot, current_lineup: dict[str, PositionSlot], game: Game) -> SimPlayer:
        """Best available starter for a slot, with fallbacks so a capped roster + injuries can't
        deadlock a lineup: (1) normal eligible-active-player ranking, (2) emergency callup from
        the reserve pool, (3) any unused active position player ranked by defense at the slot
        (an out-of-position start), (4) force-activate the IL player closest to returning if the
        reserve pool is also exhausted, (5) raise - there is truly no one left."""

        player_games_since_last_rest = self.consecutive_starts
        excluded_players = list(current_lineup.keys())

        def rating(p: SimPlayer) -> float:
            preset_bonus = _PRESET_LINEUP_BONUS if p.preset_position_slot == position else 0.0
            return p.player_rest_rating(player_games_since_last_rest.get(p.id, 0)) + preset_bonus

        eligible_players_list = self.filter_players_w_eligibility(player_list=self.position_players, position_slot=position, excluded_player_ids=excluded_players)
        if eligible_players_list:
            return sorted(eligible_players_list, key=rating, reverse=True)[0]

        if self.roster is not None:
            protected_ids = set(excluded_players)
            callup = self.roster.emergency_callup(team=self, position_slot=position, game_date=game.date, protected_ids=protected_ids)
            if callup is not None:
                return callup

        unused_players = [p for p in self.position_players if p.id not in excluded_players]
        if unused_players:
            return sorted(unused_players, key=lambda p: (p.defense_for_position_slot(position), rating(p)), reverse=True)[0]

        if self.roster is not None:
            protected_ids = set(excluded_players)
            activated = self.roster.emergency_activate_earliest(team=self, game_date=game.date, protected_ids=protected_ids)
            if activated is not None and activated.id not in excluded_players:
                return activated

        active_count = len(self.position_players)
        il_count = len(self.roster.injured) if self.roster is not None else 0
        raise ValueError(
            f'ERROR: No available players on {self.name} for position {position.value} '
            f'({game.date}, active position players: {active_count}, on IL: {il_count})'
        )

    def fill_starting_position_players(self, game: Game) -> None:

        current_lineup: dict[str, PositionSlot] = {} # KEY: PLAYER ID, VALUE: POSITION
        for _ in range(0,9):

            # ORDER POSITION SLOTS BY NUMBER OF VALID PLAYERS ABLE TO PLAY THERE.
            positions_list_w_counts: dict[PositionSlot, float] = self.num_players_valid_per_position(player_list=self.position_players, current_lineup_dict=current_lineup)
            positions_list_sorted = sorted(positions_list_w_counts.items(), key=lambda x: x[1])
            position = positions_list_sorted[0][0]

            player = self._player_for_slot(position=position, current_lineup=current_lineup, game=game)
            current_lineup[player.id] = position

        # UPDATED PLAYERS
        for player in self.position_players:
            position_for_game = current_lineup.get(player.id, None)
            player.position_slot = position_for_game or PositionSlot.NONE
        self.starting_lineup = [player for player in self.position_players if player.id in current_lineup.keys()]

        # CACHE POSITION LOOKUPS + DEFENSE TOTALS FOR THE GAME. THE LINEUP DOESN'T CHANGE MID-GAME,
        # SO THESE WOULD OTHERWISE BE RECOMPUTED ON EVERY PLATE APPEARANCE.
        self.position_map = {player.position_slot: player for player in self.starting_lineup}
        self.catcher = self.position_map.get(PositionSlot.CA)
        self.infield_defense = sum(
            player.defense_for_position_slot(pos)
            for pos in (PositionSlot._1B, PositionSlot._2B, PositionSlot._3B, PositionSlot.SS)
            if (player := self.position_map.get(pos)) is not None
        )
        self.outfield_defense = sum(
            player.defense_for_position_slot(pos)
            for pos in (PositionSlot.LF, PositionSlot.CF, PositionSlot.RF)
            if (player := self.position_map.get(pos)) is not None
        )

    def generate_batting_order(self, game: Game) -> None:

        starting_players = self.starting_lineup
        if not starting_players:
            raise ValueError(f'LINEUP IS EMPTY FOR {self.name} GAME {game.index}, {game.away_team_name} VS {game.home_team_name}')

        # PRESET BATTING ORDER (BUILDER TEAMS): USE DEFINED SPOTS, FILL GAPS BY OPS
        preset_players = {p.preset_lineup_spot: p for p in starting_players if p.preset_lineup_spot in range(1, 10)}
        if len(preset_players) > 0:
            batting_order: dict[int, SimPlayer] = dict(preset_players)
            remaining_players = sorted([p for p in starting_players if p not in batting_order.values()], key=lambda x: x.projected.get('onbase_plus_slugging', 0), reverse=True)
            open_spots = [spot for spot in range(1, 10) if spot not in batting_order]
            for spot, player in zip(open_spots, remaining_players):
                batting_order[spot] = player
            self.batting_order = [player for _, player in sorted(batting_order.items(), key=lambda x: x[0])]
            return

        batting_order = {}
        hitter_pool: list[SimPlayer] = starting_players.copy()
        ops_key = 'onbase_plus_slugging'
        obp_key = 'onbase_perc'
        hr_key = 'hr_per_650_pa'
        slg_key = 'slugging_perc'
        speed_key = 'speed'
        logic_dict = {
            3: ops_key,
            4: hr_key,
            1: speed_key,
            2: ops_key,
            5: slg_key,
            6: ops_key,
            7: ops_key,
            8: ops_key,
            9: ops_key,
        }
        for order_position, stat_key in logic_dict.items():
            if stat_key == 'speed':
                hitter = sorted(hitter_pool, key=lambda x: (x.speed, x.projected.get(obp_key, 0)), reverse=True)[0]
            else:
                hitter = sorted(hitter_pool, key=lambda x: x.projected.get(stat_key, 0), reverse=True)[0]
            batting_order[order_position] = hitter
            hitter_pool.remove(hitter)

        sorted_player_tuples_list = sorted(batting_order.items(), key=lambda x: x[0])
        sorted_player_list = [player for _, player in sorted_player_tuples_list]

        self.batting_order = sorted_player_list

    def update_lineup_index(self):
        next_lineup_index = self.lineup_index + 1
        self.lineup_index = 0 if next_lineup_index > 8 else next_lineup_index

    # ------------------------------------------------------------------
    # PITCHING
    # ------------------------------------------------------------------

    def reset_pitchers_used(self) -> None:
        for pitcher in (self.rotation.players + self.bullpen.players):
            pitcher.reset()
        self._pitchers_used: list[SimPitcher] = []

    def current_pitcher(self) -> SimPitcher:
        return self._pitchers_used[-1]

    def mark_pitcher_entered(self, pitcher: SimPitcher, inning_num_full: float) -> None:
        """Record a pitcher entering the game.

        Order is tracked by entry rather than by sorting on `start_inning`: two pitchers can share
        an `inning_num_full` (a reliever pulled before recording an out), and sorting then resolves
        the tie by roster order, which can report the pitcher who was just replaced as the current one.
        """
        pitcher.start_inning = inning_num_full
        self._pitchers_used.append(pitcher)

    def check_for_pitcher_sub(self, game_date: date, inning: Inning, runs_allowed: int) -> None:
        """ Check if current pitcher is tired and needs a sub"""
        manager = self.manager
        if self.current_pitcher().is_tired(inning=inning, ip_adjustment=manager.hook_ip_adjustment) and len(self.available_reliever_ids) > 0:
            suggested_reliever = self.bullpen.suggested_reliever(
                game_date=game_date, inning=inning,
                runs_scored=self.current_game_stats.stat(StatCategory.RUNS_SCORED), runs_allowed=runs_allowed,
                available_ids=self.available_reliever_ids,
                closer_nonsave_fit_multiplier=manager.closer_nonsave_fit_multiplier,
                closer_save_inning=manager.closer_save_inning,
            )
            if suggested_reliever:
                self.mark_pitcher_entered(suggested_reliever, inning.inning_num_full)
                self.available_reliever_ids.discard(suggested_reliever.id)

    def update_pitcher_runs_allowed(self, pitcher_runs_allowed_dict: dict) -> None:
        if not pitcher_runs_allowed_dict:
            return
        for pitcher in self._pitchers_used:
            if pitcher.id in pitcher_runs_allowed_dict:
                pitcher.runs_allowed += pitcher_runs_allowed_dict[pitcher.id]

    def log_pitcher_stats(self, game: Game) -> None:
        pitcher_stats = self.stats.stats_list_for_type(type=PlayerType.PITCHER)
        self.bullpen.pitching_log.log_pitcher_stats(game_date=game.date, stats=pitcher_stats)

    # ------------------------------------------------------------------
    # GAME LIFECYCLE
    # ------------------------------------------------------------------

    def update_roster_for_date(self, game_date: date, rng: Random) -> None:
        """Process IL returns and roll new injuries before the day's games. No-op for builder
        teams and when injuries are disabled - critically, `rng` is never touched in that case,
        so a seeded sim's per-game random stream is unaffected by whether injuries are on."""
        if self.roster is None or not self.roster.injuries_enabled:
            return
        if game_date == self._last_roster_date:
            return  # DOUBLEHEADER: ONE ROSTER PASS PER CALENDAR DAY
        self._last_roster_date = game_date
        self.roster.process_date(team=self, game_date=game_date, rng=rng)

    def process_il_returns_for_date(self, game_date: date) -> None:
        """Postseason hook: activate anyone whose IL stint has ended, but never roll new injuries
        or touch `rng` - see `Postseason.simulate`."""
        if self.roster is None:
            return
        self.roster.process_returns(team=self, game_date=game_date)

    def add_new_game(self, game: Game, opposing_team: 'SimTeam') -> None:
        self.lineup_index = 0
        self.reset_pitchers_used()
        self.stats = StatsGroup(year=game.date.year)
        self.current_game_stats = Stats(id=str(game.index))
        self.game_player_appearances = set()
        self.fill_starting_position_players(game=game)
        self.generate_batting_order(game=game)

        # BULLPEN AVAILABILITY IS FIXED FOR THE GAME - THE PITCHING LOG IS ONLY WRITTEN POST-GAME.
        unavailable = self.bullpen.pitching_log.pitcher_ids_with_recent_workload(
            game_date=game.date, days_back=2, ip_cutoff=2,
        )
        self.available_reliever_ids = {p.id for p in self.bullpen.players if p.id not in unavailable}

    def resume_from(self, state: TeamStartState) -> None:
        """Seed mid-game state for a takeover.

        `add_new_game` must have run first - it rebuilds every field this touches (lineup index,
        per-game stats, pitchers used, bullpen availability), so seeding before it would be
        silently discarded.

        Pitchers are replayed through `mark_pitcher_entered` rather than assigned directly so
        `_pitchers_used` keeps its entry ordering, which is what `current_pitcher` and the box
        score both read. A pitcher id that isn't on the roster is skipped - the sim can only field
        arms it has cards for.
        """

        self.current_game_stats.add_stat(StatCategory.RUNS_SCORED, state.runs_scored)
        self.lineup_index = max(0, min(state.lineup_index, 8))

        self.reset_pitchers_used()
        for appearance in state.pitchers_used:
            pitcher = next((p for p in (self.rotation.players + self.bullpen.players) if p.id == appearance.player_id), None)
            if pitcher is None:
                continue
            self.mark_pitcher_entered(pitcher, appearance.start_inning)
            pitcher.end_inning = appearance.end_inning
            pitcher.runs_allowed = appearance.runs_allowed
            self.available_reliever_ids.discard(pitcher.id)

        # NO RECOGNIZED PITCHER MEANS THE GAME WOULD HAVE NO ONE ON THE MOUND - FALL BACK TO THE
        # ROTATION THE WAY A FRESH GAME WOULD.
        if not self._pitchers_used:
            self.mark_pitcher_entered(self.rotation.current_pitcher, float(1))

    def current_hitter(self, game: Game) -> SimPlayer:
        return self.batting_order[self.lineup_index]

    def finalize_stats_post_game(self, game: Game) -> None:
        self.log_pitcher_stats(game)
        self.update_wins_and_losses()
        self.rotation.move_to_next_pitcher_index()
        self.update_players_games_played_stat(game)
        self.update_consecutive_starts()

    def update_consecutive_starts(self) -> None:
        """Roll the per-player consecutive-start counter used by the rest logic."""
        starter_ids = {player.id for player in self.starting_lineup}
        for player in self.position_players:
            if player.id in starter_ids:
                self.consecutive_starts[player.id] = self.consecutive_starts.get(player.id, 0) + 1
            else:
                self.consecutive_starts[player.id] = 0

    def update_wins_and_losses(self) -> None:
        last_game_stats = self.current_game_stats
        runs_scored = last_game_stats.stat(StatCategory.RUNS_SCORED)
        runs_allowed = last_game_stats.stat(StatCategory.RUNS_ALLOWED)
        if runs_scored > runs_allowed:
            self.wins += 1
        else:
            self.losses += 1

    def update_players_games_played_stat(self, game: Game) -> None:
        for player_id in self.game_player_appearances:
            self.stats.update_individual_stats(id=player_id, stats=Stats(id=player_id, totals={StatCategory.G.value: 1}))

    def log_player_appearance(self, game: Game, player_id: str) -> None:
        self.game_player_appearances.add(player_id)

    # ------------------------------------------------------------------
    # RECORD / DEFENSE
    # ------------------------------------------------------------------

    @property
    def games(self) -> int:
        return self.wins + self.losses

    @property
    def win_pct(self) -> float:
        return round(float(self.wins) / max(self.games, 1), 3)

    def points_total(self, apply_bench_multiplier: bool = False) -> int:
        """Sum of active-roster card points. `apply_bench_multiplier` discounts `bench_player_ids`
        by `bench_pts_multiplier`, matching the effective cost paid at draft time rather than each
        bench card's full price - off by default so the raw total (`self.points`) is unaffected."""
        if not apply_bench_multiplier or not self.bench_player_ids:
            return self.points
        return sum(
            round(player.points * self.bench_pts_multiplier) if player.id in self.bench_player_ids else player.points
            for player in self.active_players
        )

    def as_record(self, division: str = None, games_back: float = None, apply_bench_multiplier: bool = False) -> TeamRecord:
        return TeamRecord(
            name=self.name,
            identity=self.identity,
            league=self.league,
            division=division,
            points=self.points_total(apply_bench_multiplier=apply_bench_multiplier),
            wins=self.wins,
            losses=self.losses,
            win_pct=self.win_pct,
            games_back=games_back,
            playoff_seeding=self.playoff_seeding,
        )

    def player_for_position(self, position_slot: PositionSlot) -> Optional[SimPlayer]:
        """Starter at a position for the current game. `position_map` is rebuilt each game."""
        return self.position_map.get(position_slot)

    def player_for_id(self, id: str) -> Optional[SimPlayer]:
        players_w_id = [p for p in self.all_players if p.id == id]
        return None if len(players_w_id) == 0 else players_w_id[0]
