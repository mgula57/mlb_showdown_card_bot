from datetime import datetime, timedelta
from random import Random
from typing import Callable, Optional

from ..card.sets import Set
from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.stats.stats_period import StatsPeriod, StatsPeriodType
from ..database.postgres_db import PlayerArchive, PostgresDB
from ..mlb_stats_api import MLBStatsAPI
from ..shared.player_position import PlayerType
from .models import PostseasonFormat, SeasonSimulationConfig, SeasonSimulationResult
from .postseason import Postseason
from .roster import RESERVE_MIN_IP_PITCHER, RESERVE_MIN_PA_POSITION
from .schedule import Schedule
from .standings import Standings
from .stats import PlayerStatsGroup, load_real_league_avgs, load_woba_weights
from .team import SimTeam


class PlayerLoader:
    """Loads season card pools, preferring pre-built cards from dim_card over rebuilding from archive stats."""

    def __init__(self, db: Optional[PostgresDB] = None) -> None:
        self.db = db or PostgresDB(is_archive=True)

    def load_season_cards(self, year: int, set: Set, min_pa: int = 0, min_ip: int = 0, status_callback: Optional[Callable[[str], None]] = None) -> list[ShowdownPlayerCard]:
        """All cards for a season. dim_card pre-built cards first, archive stat rebuilds for anything missing.

        Args:
          min_pa / min_ip: Playing-time floors. Applied to archive records *before* building cards,
            since building a card is ~10x the cost of loading a pre-built one and rosters discard
            these players anyway.
          status_callback: Optional callable invoked with human-readable progress messages.
        """

        def status(message: str) -> None:
            if status_callback:
                status_callback(message)

        # FAST PATH: PRE-BUILT CARDS FROM THE card_bot VIEW / dim_card TABLE
        status(f"Loading pre-built {year} {set.value} cards from the archive DB...")
        cards_by_player_id: dict[str, ShowdownPlayerCard] = {}
        try:
            rows = self.db.fetch_card_list(filters={'year': [str(year)], 'showdown_set': set.value, 'limit': 5000}) or []
            card_id_to_player_id = {str(row['card_id']): str(row['id']) for row in rows if row.get('card_id')}
            if card_id_to_player_id:
                slots = [{'card_id': card_id, 'card_source': 'BOT'} for card_id in card_id_to_player_id.keys()]
                fetched_cards = self.db.fetch_cards_for_roster_slots(slots=slots)
                for card_id, card in fetched_cards.items():
                    cards_by_player_id[card_id_to_player_id[card_id]] = card
            status(f"Loaded {len(cards_by_player_id)} pre-built card(s)")
        except Exception as e:
            status(f"WARNING: pre-built card fetch failed, falling back to archive stats ({e})")

        # FALLBACK: BUILD CARDS FROM RAW ARCHIVE STATS FOR PLAYERS NOT PRE-BUILT
        status(f"Fetching {year} archive stats for players missing a pre-built card...")
        player_archives: list[PlayerArchive] = self.db.fetch_all_stats_from_archive(year_list=[int(year)], exclude_records_with_stats=False)

        def meets_playing_time(archive: PlayerArchive) -> bool:
            if archive.player_type.upper() == 'PITCHER':
                return (archive.ip or 0) >= min_ip
            return (archive.pa or 0) >= min_pa

        missing_archives = [
            archive for archive in player_archives
            if archive.id not in cards_by_player_id and archive.stats and meets_playing_time(archive)
        ]
        if missing_archives:
            status(f"Building {len(missing_archives)} card(s) from raw archive stats (min {min_pa} PA / {min_ip} IP)...")
        built_count = 0
        failed_count = 0
        for archive in missing_archives:
            try:
                cards_by_player_id[archive.id] = ShowdownPlayerCard(
                    year=str(archive.year),
                    set=set,
                    stats=archive.stats,
                    name=archive.name,
                    stats_period=StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(archive.year)),
                )
                built_count += 1
            except Exception:
                failed_count += 1
                continue

        if missing_archives:
            failed_str = f", {failed_count} failed to build" if failed_count else ""
            status(f"Built {built_count} card(s) from archive stats{failed_str}")
        status(f"Player pool ready: {len(cards_by_player_id)} total card(s)")

        return list(cards_by_player_id.values())


class Season:
    """Simulates a full season (real MLB year or custom-team tournament) and returns structured results."""

    def __init__(self, config: SeasonSimulationConfig, db: Optional[PostgresDB] = None, mlb_stats_api: Optional[MLBStatsAPI] = None) -> None:
        self.config = config
        self.rng = Random(config.seed)
        self.db = db
        self.mlb_stats_api = mlb_stats_api or MLBStatsAPI()
        self.schedule: Optional[Schedule] = None
        self.standings: Optional[Standings] = None
        self.league_stats: Optional[PlayerStatsGroup] = None
        self.postseason: Optional[Postseason] = None

    def simulate(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> SeasonSimulationResult:
        """Run the full simulation.

        Args:
          progress_callback: Called with (games_completed, total_games) after each game.
          log_callback: Called with each play-by-play line (CLI game log).
          status_callback: Called with human-readable progress messages during setup (player loading, roster building, scheduling).
        """

        def status(message: str) -> None:
            if status_callback:
                status_callback(message)

        config = self.config
        started_at = datetime.now()

        # SETUP TEAMS + SCHEDULE
        if config.is_tournament:
            status(f"Loading {len(config.custom_teams)} custom team(s) for tournament '{config.league_name}'...")
            teams = self._build_tournament_teams()
            status(f"Loaded {len(teams)} team(s): {', '.join(sorted(teams.keys()))}")
            num_teams = len(teams)
            default_games = num_teams * (num_teams - 1)  # EACH MATCHUP TWICE
            self.schedule = Schedule(
                year=config.year,
                tournament=config.league_name,
                game_limit=config.tournament_games or default_games,
                team_names=list(teams.keys()),
            )
        else:
            loader = PlayerLoader(db=self.db)
            # LOWER THAN THE ACTIVE-ROSTER THRESHOLDS SO A FULL 40-MAN CAN BE FILLED FROM RESERVE
            # DEPTH - BUT NO LOWER THAN THE RESERVE SAMPLE-SIZE FLOORS, SINCE `Roster.select`
            # REJECTS ANYTHING BELOW THOSE ANYWAY AND BUILDING THE CARD WOULD BE WASTED WORK.
            cards = loader.load_season_cards(
                year=config.year, set=config.set,
                min_pa=min(config.min_pa, RESERVE_MIN_PA_POSITION),
                min_ip=min(config.min_ip_sp, config.min_ip_rp, RESERVE_MIN_IP_PITCHER),
                status_callback=status_callback,
            )
            status(f"Building {config.year} MLB schedule...")
            self.schedule = Schedule(
                year=config.year,
                pct_limit=config.pct_of_games,
                game_limit=config.games_limit,
                mlb_stats_api=self.mlb_stats_api,
            )
            status(f"Building rosters for {len(self.schedule.unique_team_names)} team(s)...")
            teams = self._build_season_teams(cards=cards, status_callback=status_callback)
            status(f"Rosters built for {len(teams)} team(s)")

        self.standings = Standings(
            year=config.year,
            tournament=config.league_name if config.is_tournament else None,
            team_leagues=self.schedule.team_leagues,
            teams=teams,
            mlb_stats_api=self.mlb_stats_api,
        )
        self.league_stats = PlayerStatsGroup(players=self.standings.all_players, year=config.year, name="LEAGUE")

        # SIMULATE GAMES
        total_games = len(self.schedule.games)
        status(f"Simulating {total_games} game(s)...")
        for index, game in enumerate(self.schedule.games):
            home_team = self.standings.teams[game.home_team_name]
            away_team = self.standings.teams[game.away_team_name]
            home_team.update_roster_for_date(game_date=game.date, rng=self.rng)
            away_team.update_roster_for_date(game_date=game.date, rng=self.rng)
            game.setup(home_team=home_team, away_team=away_team)
            game.simulate(rng=self.rng, collect_log=config.include_game_logs, log_callback=log_callback)

            self.league_stats.merge(game.home_team.stats)
            self.league_stats.merge(game.away_team.stats)

            if progress_callback:
                progress_callback(index + 1, total_games)

        # SNAPSHOT REGULAR SEASON STANDINGS BEFORE PLAYOFF GAMES ADD TO TEAM W/L
        standings_result = self.standings.as_result()

        # POSTSEASON
        if config.simulate_postseason and total_games > 0:
            postseason_format = config.postseason_format
            if config.is_tournament and postseason_format == PostseasonFormat.DYNAMIC:
                postseason_format = PostseasonFormat.WORLD_SERIES
            status(f"Simulating postseason ({postseason_format.value})...")
            self.postseason = Postseason(
                year=config.year,
                standings=self.standings,
                format=postseason_format,
                start_date=self.schedule.games[-1].date + timedelta(days=5),
            )
            self.postseason.simulate(rng=self.rng)

        return self._build_result(started_at=started_at, standings_result=standings_result)

    # ------------------------------------------------------------------
    # TEAM CONSTRUCTION
    # ------------------------------------------------------------------

    def _build_tournament_teams(self) -> dict[str, SimTeam]:
        config = self.config
        db = self.db or PostgresDB(is_archive=True)
        teams: dict[str, SimTeam] = {}
        for builder_team in config.custom_teams:
            cards = db.fetch_cards_for_roster_slots(slots=builder_team.roster)
            if len(cards) == 0:
                raise ValueError(f"No cards could be loaded for team '{builder_team.name}'")
            teams[builder_team.abbreviation] = SimTeam.from_builder_team(
                team=builder_team,
                cards=cards,
                year=config.year,
                league=config.league_name,
            )
        if len(teams) < 2:
            raise ValueError("Tournament mode requires at least 2 custom teams")
        return teams

    def _build_season_teams(self, cards: list[ShowdownPlayerCard], status_callback: Optional[Callable[[str], None]] = None) -> dict[str, SimTeam]:
        config = self.config

        def status(message: str) -> None:
            if status_callback:
                status_callback(message)

        cards_by_team: dict[str, list[ShowdownPlayerCard]] = {}
        for card in cards:
            team_abbr = card.team.value if card.team else None
            if team_abbr:
                cards_by_team.setdefault(team_abbr, []).append(card)

        real_games_per_team = self.schedule.original_games_per_team or 162

        teams: dict[str, SimTeam] = {}
        missing_teams: list[str] = []
        for team_name in self.schedule.unique_team_names:
            team_cards = cards_by_team.get(team_name, [])
            if len(team_cards) == 0:
                missing_teams.append(team_name)
                continue
            team = SimTeam.from_player_pool(
                year=config.year,
                name=team_name,
                cards=team_cards,
                league=self.schedule.team_leagues.get(team_name),
                min_pa=config.min_pa,
                min_ip_sp=config.min_ip_sp,
                min_ip_rp=config.min_ip_rp,
                active_roster_size=config.active_roster_size,
                full_roster_size=config.full_roster_size,
                enable_injuries=config.enable_injuries,
                games_per_season=real_games_per_team,
            )
            teams[team_name] = team
            for warning in team.roster.warnings:
                status(f"{team_name}: {warning}")

        if missing_teams:
            raise ValueError(f"No player cards found for scheduled team(s): {missing_teams}. Check team abbreviation mappings.")

        if config.enable_injuries:
            for team in teams.values():
                team.roster.build_profiles(
                    team=team,
                    games_per_team=self.schedule.games_per_team,
                    real_games_per_team=real_games_per_team,
                    games_per_day=self.schedule.games_per_day,
                    severity=config.injury_severity_multiplier,
                    rotation_size=team.roster.ACTIVE_ROTATION,
                )

        return teams

    # ------------------------------------------------------------------
    # RESULTS
    # ------------------------------------------------------------------

    def _build_result(self, started_at: datetime, standings_result) -> SeasonSimulationResult:
        config = self.config
        ended_at = datetime.now()

        schedule_length = self.schedule.schedule_length or len(self.schedule.games)
        original_schedule_length = self.schedule.original_schedule_length or schedule_length
        stats_min_ip = int(60 * schedule_length / max(original_schedule_length, 1))
        stats_min_pa = int(250 * schedule_length / max(original_schedule_length, 1))

        league_totals = {
            player_type.value: self.league_stats.aggregated_stats(type=player_type)
            for player_type in [PlayerType.HITTER, PlayerType.PITCHER]
        }

        real_league_averages = {}
        woba_weights = {}
        if not config.is_tournament:
            for player_type in [PlayerType.HITTER, PlayerType.PITCHER]:
                try:
                    real_league_averages[player_type.value] = load_real_league_avgs(year=config.year, type=player_type)
                except (ValueError, FileNotFoundError):
                    continue
        try:
            woba_weights = load_woba_weights(year=config.year)
        except FileNotFoundError:
            pass

        transactions = sorted(
            (t for team in self.standings.teams.values() if team.roster for t in team.roster.transactions),
            key=lambda t: (t.date, t.team),
        )

        return SeasonSimulationResult(
            config=config,
            started_at=started_at,
            ended_at=ended_at,
            schedule_length=schedule_length,
            original_schedule_length=original_schedule_length,
            stats_min_pa=stats_min_pa,
            stats_min_ip=stats_min_ip,
            standings=standings_result,
            player_stats=list(self.league_stats.stats.values()),
            league_totals=league_totals,
            real_league_averages=real_league_averages,
            woba_weights=woba_weights,
            games=[game.as_result() for game in self.schedule.games if game.is_game_over],
            postseason=self.postseason.as_result() if self.postseason else None,
            transactions=transactions,
        )
