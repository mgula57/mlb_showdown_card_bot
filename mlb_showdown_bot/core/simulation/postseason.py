import uuid
from datetime import date, timedelta
from random import Random
from typing import Optional

from .game import Game
from .models import PostseasonFormat, PostseasonResult, PostseasonRound, SeriesResult
from .standings import Standings
from .team import SimTeam


class PostseasonSeries:

    def __init__(self, id: str, league: str, round: PostseasonRound, format: PostseasonFormat, start_date: date, home_team: SimTeam, away_team: SimTeam, prior_round_seed_matchup: list[int] = []) -> None:
        self.id = id
        self.league = league
        self.round = round
        self.format = format
        self.start_date = start_date
        self.home_team = home_team
        self.away_team = away_team
        self.prior_round_seed_matchup = prior_round_seed_matchup
        match round:
            case PostseasonRound.WILDCARD: self.length = format.num_games_wildcard
            case PostseasonRound.DIVISIONAL: self.length = format.num_games_division
            case PostseasonRound.CHAMPIONSHIP: self.length = format.num_games_championship_series
            case PostseasonRound.WORLD_SERIES: self.length = format.num_games_world_series

        self.generate_games_list()

    @property
    def teams_list(self) -> list[SimTeam]:
        return [team for team in [self.home_team, self.away_team] if team is not None]

    @property
    def is_teams_populated(self) -> bool:
        return self.home_team is not None and self.away_team is not None

    @property
    def series_winner(self) -> Optional[SimTeam]:
        """ If the series is over, return the winning team. """
        for team in [self.away_team, self.home_team]:
            if self.wins_for_team(team.name) > (self.length / 2.0):
                return team

        return None

    def generate_games_list(self) -> None:
        """ Generate games list and store to self """

        # IF EITHER TEAM IS EMPTY, DON'T POPULATE GAMES LIST
        if self.home_team is None or self.away_team is None or self.start_date is None:
            self.games = []
            return

        games = []
        is_top_team_home = True
        date_index = 0
        for game_num in range(1, self.length + 1):
            is_change_in_home_team = is_top_team_home != self.is_top_team_home(game_num)
            if is_change_in_home_team:
                date_index += 1
            is_top_team_home = self.is_top_team_home(game_num)
            home_team_name = self.home_team.name if is_top_team_home else self.away_team.name
            away_team_name = self.away_team.name if is_top_team_home else self.home_team.name
            games.append(
                Game(
                    index=game_num + self.round.game_num_index_addition,
                    date=self.start_date + timedelta(days=date_index),
                    home_team_name=home_team_name,
                    away_team_name=away_team_name,
                    home_team_game_number=game_num,
                    away_team_game_number=game_num,
                )
            )
            date_index += 1
        self.games = games

    def is_top_team_home(self, game_index: int) -> bool:
        match game_index:
            case 1 | 2: return True
            case 3 | 4: return True if self.format == PostseasonFormat.WILDCARD_3 else False
            case 5: return False if self.length == 7 else True
            case 6 | 7: return True
            case _: return True

    def wins_for_team(self, team_name: str) -> int:
        num_wins = 0
        for game in self.games:
            if game.winning_team:
                num_wins += int(game.winning_team.name == team_name)
        return num_wins

    def as_result(self) -> SeriesResult:
        winner = self.series_winner
        return SeriesResult(
            round=self.round,
            league=self.league,
            home_team=self.home_team.name if self.home_team else "TBD",
            away_team=self.away_team.name if self.away_team else "TBD",
            home_team_seed=self.home_team.playoff_seeding if self.home_team else None,
            away_team_seed=self.away_team.playoff_seeding if self.away_team else None,
            home_team_wins=self.wins_for_team(self.home_team.name) if self.home_team else 0,
            away_team_wins=self.wins_for_team(self.away_team.name) if self.away_team else 0,
            winner=winner.name if winner else None,
            games=[game.as_result() for game in self.games if game.is_game_over],
        )


class Postseason:

    def __init__(self, year: int, standings: Standings, format: PostseasonFormat, start_date: date, collect_box_score: bool = False) -> None:
        self.year = year
        self.standings = standings
        self.format = self.default_format_for_year(year=year) if format == PostseasonFormat.DYNAMIC else format
        self.start_date = start_date
        self.collect_box_score = collect_box_score
        # SCHEDULE PLACEHOLDERS
        self.rounds: dict[PostseasonRound, dict[str, PostseasonSeries]] = {round: {} for round in self.format.rounds}
        self.generate_initial_schedule()

    @property
    def teams_scheduled(self) -> list[SimTeam]:
        teams_in_schedule = []
        for round in self.rounds.values():
            for series in round.values():
               teams_in_schedule.extend(series.teams_list)

        return list(set(teams_in_schedule))

    @property
    def world_series(self) -> Optional[PostseasonSeries]:
        world_series_round = self.rounds.get(PostseasonRound.WORLD_SERIES, None)
        if world_series_round is None:
            return None

        world_series_series = list(world_series_round.values())
        if len(world_series_series) == 0:
            return None

        return world_series_series[0]

    @property
    def world_series_winner_team(self) -> Optional[SimTeam]:
        if self.world_series is None:
            return None

        return self.world_series.series_winner

    @property
    def world_series_winner_team_name(self) -> Optional[str]:
        team = self.world_series_winner_team

        if team is None:
            return None

        return team.name

    def default_format_for_year(self, year: int) -> PostseasonFormat:
        """ Returns Postseason Format used in real life during that year """
        formats = [PostseasonFormat.WORLD_SERIES, PostseasonFormat.WILDCARD_1, PostseasonFormat.WILDCARD_2, PostseasonFormat.WILDCARD_3, PostseasonFormat.CHAMPIONSHIP_SERIES,]
        for format in formats:
            if year in format.year_range:
                return format

        return PostseasonFormat.CHAMPIONSHIP_SERIES

    def generate_initial_schedule(self) -> None:
        """ Generate and store the postseason schedule """
        match self.format:

            case PostseasonFormat.WILDCARD_1:
                for league in self.standings.leagues:

                    # 3 DIVISION WINNERS
                    division_winners = self.standings.division_leaders_list(league=league)
                    team_divisional_1 = division_winners[0]
                    team_divisional_2 = division_winners[1]
                    team_divisional_3 = division_winners[2]
                    team_divisional_1.playoff_seeding = 1
                    team_divisional_2.playoff_seeding = 2
                    team_divisional_3.playoff_seeding = 3

                    # 1 WILD CARD TEAM
                    non_division_winning_teams = [team for team in self.standings.teams.values() if team.league == league and team not in division_winners]
                    non_division_winning_teams_sorted = sorted(non_division_winning_teams, key=lambda tm: (tm.win_pct, tm.wins), reverse=True)
                    wild_card_team = non_division_winning_teams_sorted[0]
                    wild_card_team.playoff_seeding = 4

                    # SETUP SERIES
                    division_series_1 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.DIVISIONAL, format=self.format, start_date=self.start_date, home_team=team_divisional_1, away_team=wild_card_team)
                    division_series_2 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.DIVISIONAL, format=self.format, start_date=self.start_date, home_team=team_divisional_2, away_team=team_divisional_3)
                    self.add_series(round=PostseasonRound.DIVISIONAL, series_list=[division_series_1, division_series_2])

            case PostseasonFormat.WILDCARD_2:
                for league in self.standings.leagues:

                    # ADD TOP 3 DIVISION WINNERS TO DIVISIONAL SERIES. LEAVE WC BLANK
                    division_winners = self.standings.division_leaders_list(league=league)
                    team_divisional_1 = division_winners[0]
                    team_divisional_2 = division_winners[1]
                    team_divisional_3 = division_winners[2]
                    team_divisional_1.playoff_seeding = 1
                    team_divisional_2.playoff_seeding = 2
                    team_divisional_3.playoff_seeding = 3
                    division_series_1 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.DIVISIONAL, format=self.format, start_date=None, home_team=team_divisional_1, away_team=None, prior_round_seed_matchup=[4,5])
                    division_series_2 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.DIVISIONAL, format=self.format, start_date=None, home_team=team_divisional_2, away_team=team_divisional_3)
                    self.add_series(round=PostseasonRound.DIVISIONAL, series_list=[division_series_1, division_series_2])

                    # 2 WILD CARD TEAMS PLAY 1 GAME SERIES
                    non_division_winning_teams = [team for team in self.standings.teams.values() if team.league == league and team not in division_winners]
                    non_division_winning_teams_sorted = sorted(non_division_winning_teams, key=lambda tm: (tm.win_pct, tm.wins), reverse=True)
                    wild_card_team_1 = non_division_winning_teams_sorted[0]
                    wild_card_team_2 = non_division_winning_teams_sorted[1]
                    wild_card_team_1.playoff_seeding = 4
                    wild_card_team_2.playoff_seeding = 5
                    wild_card_series = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.WILDCARD, format=self.format, start_date=self.start_date, home_team=wild_card_team_1, away_team=wild_card_team_2)
                    self.add_series(round=PostseasonRound.WILDCARD, series_list=[wild_card_series])

            case PostseasonFormat.WILDCARD_3:

                for league in self.standings.leagues:

                    # ADD TOP 2 DIVISION WINNERS TO DIVISIONAL SERIES
                    division_winners = self.standings.division_leaders_list(league=league)
                    team_divisional_1 = division_winners[0]
                    team_divisional_2 = division_winners[1]
                    wild_card_1 = division_winners[2]
                    team_divisional_1.playoff_seeding = 1
                    team_divisional_2.playoff_seeding = 2
                    wild_card_1.playoff_seeding = 3
                    division_series_1 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.DIVISIONAL, format=self.format, start_date=None, home_team=team_divisional_1, away_team=None, prior_round_seed_matchup=[4,5])
                    division_series_2 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.DIVISIONAL, format=self.format, start_date=None, home_team=team_divisional_2, away_team=None, prior_round_seed_matchup=[3,6])
                    self.add_series(round=PostseasonRound.DIVISIONAL, series_list=[division_series_1, division_series_2])

                    # ADD 3RD DIVISION WINNER AND TOP 3 OTHER TEAMS TO WILD CARD ROUND
                    teams_remaining = [team for team in self.standings.teams.values() if team.league == league and team not in (self.teams_scheduled + [wild_card_1])]
                    teams_remaining_sorted = sorted(teams_remaining, key=lambda tm: (tm.win_pct, tm.wins), reverse=True)
                    wild_card_2 = teams_remaining_sorted[0]
                    wild_card_3 = teams_remaining_sorted[1]
                    wild_card_4 = teams_remaining_sorted[2]
                    wild_card_2.playoff_seeding = 4
                    wild_card_3.playoff_seeding = 5
                    wild_card_4.playoff_seeding = 6
                    wc_series_1 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.WILDCARD, format=self.format, start_date=self.start_date, home_team=wild_card_1, away_team=wild_card_4)
                    wc_series_2 = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.WILDCARD, format=self.format, start_date=self.start_date, home_team=wild_card_2, away_team=wild_card_3)
                    self.add_series(round=PostseasonRound.WILDCARD, series_list=[wc_series_1, wc_series_2])

            case PostseasonFormat.CHAMPIONSHIP_SERIES:
                # BEST TEAMS IN EACH DIVISION (2 DIVISIONS) GO TO LCS
                for league in self.standings.leagues:
                    division_winners = self.standings.top_teams(num_teams=2, divisions=self.standings.divisions(leagues=[league]))
                    team_championship_series_1 = division_winners[0]
                    team_championship_series_2 = division_winners[1]
                    team_championship_series_1.playoff_seeding = 1
                    team_championship_series_2.playoff_seeding = 2
                    league_championship_series = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=PostseasonRound.CHAMPIONSHIP, format=self.format, start_date=self.start_date, home_team=team_championship_series_1, away_team=team_championship_series_2)
                    self.add_series(round=PostseasonRound.CHAMPIONSHIP, series_list=[league_championship_series])

            case PostseasonFormat.WORLD_SERIES:
                # BEST TEAMS IN EACH LEAGUE GO TO WORLD SERIES.
                # SINGLE LEAGUE (TOURNAMENTS): TOP 2 TEAMS OVERALL.
                if len(self.standings.leagues) >= 2:
                    top_teams = [self.standings.top_team(divisions=self.standings.divisions(leagues=[league])) for league in self.standings.leagues]
                else:
                    top_teams = self.standings.top_teams(num_teams=2)
                top_teams_sorted = sorted(top_teams, key=lambda tm: (tm.win_pct, tm.wins), reverse=True)
                world_series = PostseasonSeries(id=str(uuid.uuid4()), league=None, round=PostseasonRound.WORLD_SERIES, format=self.format, start_date=self.start_date, home_team=top_teams_sorted[0], away_team=top_teams_sorted[1])
                self.add_series(round=PostseasonRound.WORLD_SERIES, series_list=[world_series])

            case _: return None

    def add_series(self, round: PostseasonRound, series_list: list[PostseasonSeries]) -> None:
        """ Add list of series to the rounds attribute """
        for series in series_list:
            self.rounds[round].update({
                series.id: series,
            })

    def advance_teams_to_next_round(self, round: PostseasonRound, teams_advancing_per_league: dict[str, list[SimTeam]], start_date: date) -> None:
        """ Advances team(s) to the next round in their league. """

        if round.next_round is None:
            # NO ADVANCING IF WORLD SERIES
            return None

        match round.next_round:
            case PostseasonRound.DIVISIONAL:
                for league, advancing_teams_list in teams_advancing_per_league.items():
                    # GAMES WITH OPEN SLOTS IN THE LEAGUE
                    series_updated = {}
                    for series_id, series in self.rounds[round.next_round].items():
                        team_for_series_list = [team for team in advancing_teams_list if team.playoff_seeding in series.prior_round_seed_matchup]
                        team_for_series = None
                        if len(team_for_series_list) > 0:
                            team_for_series = team_for_series_list[0]
                        series.start_date = start_date
                        if series.league == league and not series.is_teams_populated and team_for_series:
                            series.away_team = team_for_series
                        series_updated[series_id] = series
                    self.rounds[round.next_round].update(series_updated)

            case PostseasonRound.CHAMPIONSHIP:
                for league, advancing_teams_list in teams_advancing_per_league.items():
                    advancing_teams_list_sorted = sorted(advancing_teams_list, key=lambda tm: tm.playoff_seeding)
                    championship_series = PostseasonSeries(id=str(uuid.uuid4()), league=league, round=round.next_round, format=self.format, start_date=start_date, home_team=advancing_teams_list_sorted[0], away_team=advancing_teams_list_sorted[1])
                    self.rounds[round.next_round].update({ championship_series.id: championship_series })

            case PostseasonRound.WORLD_SERIES:
                # TAKE 2 CHAMPIONSHIP SERIES WINNERS AND MATCH THEM UP
                advancing_teams_list = [team for league_teams in teams_advancing_per_league.values() for team in league_teams if team is not None]
                if len(advancing_teams_list) < 2:
                    return None
                world_series = PostseasonSeries(id=str(uuid.uuid4()), league=None, round=round.next_round, format=self.format, start_date=start_date, home_team=advancing_teams_list[0], away_team=advancing_teams_list[1])
                self.rounds[round.next_round].update({ world_series.id: world_series })

    def simulate(self, rng: Random) -> None:

        for round, series_dict in self.rounds.items():
            teams_advancing = {league: [] for league in self.standings.leagues}
            for series in series_dict.values():
                if len(series.games) == 0:
                    series.generate_games_list()

                end_date = self.start_date
                for game in series.games:
                    if series.series_winner is None:
                        game_num = game.index - series.round.game_num_index_addition
                        home_team = series.home_team if series.is_top_team_home(game_num) else series.away_team
                        away_team = series.away_team if series.is_top_team_home(game_num) else series.home_team
                        # POSTSEASON: PROCESS IL RETURNS ONLY - NEVER ROLL NEW INJURIES HERE. TEAMS
                        # PLAY HURT IN OCTOBER AND THE REGULAR-SEASON HAZARD ISN'T CALIBRATED FOR
                        # THE POSTSEASON'S SPARSER SCHEDULE, SO THIS INTENTIONALLY TAKES NO `rng`.
                        home_team.process_il_returns_for_date(game_date=game.date)
                        away_team.process_il_returns_for_date(game_date=game.date)
                        game.setup(home_team=home_team, away_team=away_team)
                        game.simulate(rng=rng, collect_box_score=self.collect_box_score)
                        end_date = game.date

                series.end_date = end_date

                if series.league:
                    teams_advancing.setdefault(series.league, []).append(series.series_winner)

            self.advance_teams_to_next_round(round=round, teams_advancing_per_league=teams_advancing, start_date=max([series.end_date for series in series_dict.values()]) + timedelta(days=2))

    def as_result(self) -> PostseasonResult:
        rounds: dict[str, list[SeriesResult]] = {}
        for round, series_dict in self.rounds.items():
            rounds[round.value] = [series.as_result() for series in series_dict.values()]
        return PostseasonResult(
            format=self.format,
            rounds=rounds,
            world_series_winner=self.world_series_winner_team_name,
        )
