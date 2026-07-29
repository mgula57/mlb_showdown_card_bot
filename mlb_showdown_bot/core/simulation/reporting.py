from typing import Optional

from prettytable import PrettyTable

from ..shared.player_position import PlayerType
from .models import PostseasonFormat, PostseasonRound, SeasonSimulationResult, SeriesResult
from .stats import StatCategory, Stats

_HITTER_CATEGORIES = [
    StatCategory.G, StatCategory.PA, StatCategory.BA, StatCategory.OBP, StatCategory.SLG, StatCategory.OPS, StatCategory.OPS_PLUS,
    StatCategory.BB, StatCategory.HITS, StatCategory.SINGLES, StatCategory.DOUBLES, StatCategory.TRIPLES,
    StatCategory.HOMERUNS, StatCategory.RBI, StatCategory.SO, StatCategory.GDP,
    StatCategory.SB, StatCategory.CS, StatCategory.RUNS, StatCategory.wRC_PLUS,
]
_PITCHER_CATEGORIES = [
    StatCategory.G, StatCategory.ERA, StatCategory.WHIP, StatCategory.IP,
    StatCategory.EARNED_RUNS, StatCategory.SO9, StatCategory.GDP, StatCategory.GDPa,
]


_HEADER_WIDTH = 70


class SeasonReport:
    """Renders a SeasonSimulationResult as rich CLI tables and brackets."""

    def __init__(self, result: SeasonSimulationResult) -> None:
        self.result = result

    # ------------------------------------------------------------------
    # SHARED HELPERS
    # ------------------------------------------------------------------

    def _print_header(self, title: str) -> None:
        print(f"\n{f' {title} '.center(_HEADER_WIDTH, '=')}")

    def print_summary(self) -> None:
        """One-line-per-fact overview of the run, printed before the detailed tables."""
        config = self.result.config
        self._print_header("SEASON SUMMARY")
        label = config.league_name if config.is_tournament else str(config.year)
        print(f"  {'League/Year':<18}{label}")
        print(f"  {'Set':<18}{config.set.value}")
        print(f"  {'Games Simulated':<18}{self.result.schedule_length} / {self.result.original_schedule_length}")
        num_teams = sum(len(records) for records in self.result.standings.divisions.values())
        print(f"  {'Teams':<18}{num_teams}")
        if config.simulate_postseason:
            postseason = self.result.postseason
            champion = postseason.world_series_winner if postseason else None
            print(f"  {'Postseason':<18}{config.postseason_format.value}{f' (Champion: {champion})' if champion else ''}")
        if config.seed is not None:
            print(f"  {'Seed':<18}{config.seed}")

    # ------------------------------------------------------------------
    # STANDINGS
    # ------------------------------------------------------------------

    def print_standings(self) -> None:
        self._print_header("STANDINGS")
        for division, records in self.result.standings.divisions.items():
            tbl = PrettyTable()
            tbl.field_names = ['Division', 'Team', 'PTS', 'W', 'L', 'W-L%', 'GB']
            tbl.align['Team'] = 'l'
            for record in records:
                games_back = '-' if record.games_back is None else record.games_back
                tbl.add_row([division, record.name, record.points, record.wins, record.losses, record.win_pct, games_back])
            print(tbl)

    # ------------------------------------------------------------------
    # PLAYER STATS
    # ------------------------------------------------------------------

    def _stats_table(self, stats_list: list[Stats], player_type: PlayerType, show_team: bool = True, show_position: bool = True, show_points: bool = True, show_command: bool = True, show_diffs_row: bool = False, is_diff_a_pct: bool = False, show_rank: bool = False, stats_to_ignore: list[StatCategory] = []) -> PrettyTable:

        league_stats = self.result.league_totals.get(player_type.value)
        woba_weights = self.result.woba_weights

        field_names = [StatCategory.NAME] + ([StatCategory.TEAM] if show_team else []) + ([StatCategory.POSITION] if show_position else []) + ([StatCategory.POINTS] if show_points else []) + ([StatCategory.COMMAND] if show_command else [])
        field_names += _HITTER_CATEGORIES if player_type == PlayerType.HITTER else _PITCHER_CATEGORIES
        field_names = [category for category in field_names if category not in stats_to_ignore]

        def value(stats: Stats, category: StatCategory):
            return stats.stat(category, league_stats=league_stats, woba_weights=woba_weights, combine_1b_and_1b_plus=True)

        tbl = PrettyTable()
        tbl.field_names = (['#'] if show_rank else []) + ['TYPE'] + [category.abbreviation for category in field_names]
        tbl.align[StatCategory.NAME.abbreviation] = 'l'
        for index, statline in enumerate(stats_list):
            is_last_record = len(stats_list) == (index + 1)
            rank = [index + 1] if show_rank else []
            tbl.add_row(rank + [player_type.value.upper()] + [value(statline, category) for category in field_names], divider=is_last_record and show_diffs_row)

        if show_diffs_row and len(stats_list) >= 2:
            diffs_row = []
            for category in field_names:
                if category.is_text:
                    diffs_row.append('')
                    continue
                first = value(stats_list[0], category)
                second = value(stats_list[1], category)
                if is_diff_a_pct:
                    denominator = second if second > 0 else 1.0
                    pct = round((first - second) / denominator * 100.0, 1)
                    diffs_row.append(f"{'+' if (first - second) > 0 else ''}{pct}%")
                else:
                    diffs_row.append(round(first - second, category.decimal_places))
            tbl.add_row(([''] if show_rank else []) + [''] + diffs_row)

        return tbl

    def print_top_players(self, limit: int = 20) -> None:
        self._print_header("TOP HITTERS")
        top_hitters = self.result.top_players(player_type=PlayerType.HITTER.value, stat=StatCategory.OPS.value, limit=limit, min_pa=self.result.stats_min_pa)
        print(self._stats_table(stats_list=top_hitters, player_type=PlayerType.HITTER, show_rank=True))
        self._print_header("TOP PITCHERS")
        top_pitchers = self.result.top_players(player_type=PlayerType.PITCHER.value, stat=StatCategory.ERA.value, limit=limit, is_desc=False, min_ip=self.result.stats_min_ip)
        print(self._stats_table(stats_list=top_pitchers, player_type=PlayerType.PITCHER, show_rank=True))

    def print_real_life_comparison(self) -> None:
        self._print_header("SIM VS. REAL-LIFE")
        for player_type in [PlayerType.PITCHER, PlayerType.HITTER]:
            sim_stats = self.result.league_totals.get(player_type.value)
            real_stats = self.result.real_league_averages.get(player_type.value)
            if sim_stats is None or real_stats is None:
                continue
            sim_stats = sim_stats.model_copy(update={'name': 'SIM'})
            real_stats = real_stats.model_copy(update={'name': 'REAL'})
            print(self._stats_table(
                stats_list=[sim_stats, real_stats],
                player_type=player_type,
                show_team=False, show_position=False, show_points=False, show_command=False,
                show_diffs_row=True, is_diff_a_pct=True,
                stats_to_ignore=[StatCategory.G],
            ))

    def print_outliers(self, limit: int = 5) -> None:
        for direction_label, hitter_desc in [('POSITIVE', True), ('NEGATIVE', False)]:
            self._print_header(f"{direction_label} OUTLIERS")
            for player_type, is_desc in [(PlayerType.HITTER, hitter_desc), (PlayerType.PITCHER, not hitter_desc)]:
                min_pa = self.result.stats_min_pa if player_type == PlayerType.HITTER else 0
                min_ip = self.result.stats_min_ip if player_type == PlayerType.PITCHER else 0
                outliers = self.result.top_outliers(player_type=player_type.value, limit=limit, is_desc=is_desc, min_pa=min_pa, min_ip=min_ip)
                tbl = PrettyTable(field_names=['Name', 'Type', 'OPS (SIM)', 'OPS (REAL)', 'DIFF'])
                tbl.align['Name'] = 'l'
                for entry in outliers:
                    tbl.add_row([entry.name, entry.player_type, entry.sim_ops, entry.real_ops, entry.diff])
                print(tbl)

    def print_team_stats(self, teams: list[str]) -> None:
        """Prints all hitting and pitching stats for players on the given teams. Pass ["*"] for every team."""
        team_names = sorted({s.team for s in self.result.player_stats if s.team}) if teams == ["*"] else teams
        for team in team_names:
            self._print_header(f"TEAM - {team}")
            for player_type in [PlayerType.HITTER, PlayerType.PITCHER]:
                sort_category = StatCategory.OPS if player_type == PlayerType.HITTER else StatCategory.IP
                stats_list = sorted(
                    [s for s in self.result.player_stats if s.player_type == player_type and s.team == team],
                    key=lambda s: s.stat(sort_category),
                    reverse=player_type == PlayerType.HITTER
                )
                print(self._stats_table(stats_list=stats_list, player_type=player_type))

    # ------------------------------------------------------------------
    # POSTSEASON BRACKET
    # ------------------------------------------------------------------

    def _series_bracket_str(self, series: SeriesResult, format: PostseasonFormat, is_reversed: bool = False) -> str:
        if series.round == PostseasonRound.WORLD_SERIES:
            world_series_text = ""
            for _ in range(8):
                world_series_text += "               \n"
            world_series_text += f"{series.away_team} ({series.away_team_wins}) {series.home_team} ({series.home_team_wins})\n"
            world_series_text += f"---------------\n"
            world_series_text += f"WINNER: {series.winner}    \n"
            for _ in range(6):
                world_series_text += "               \n"

            return world_series_text
        else:
            whitespace = '        '
            prefix_whitespace = whitespace if is_reversed else ''
            suffix_whitespace = whitespace if not is_reversed else ''
            prefix_padding = '  ' if is_reversed else ''
            suffix_padding = '  ' if not is_reversed else ''
            num_vert_lines = 3 if series.round == PostseasonRound.CHAMPIONSHIP and format.is_wildcard_round else 1
            vertical_line_str = "".join([f'{prefix_padding}{suffix_whitespace}|{prefix_whitespace}{suffix_padding}\n' for _ in range(num_vert_lines)])
            return (
                f'{prefix_padding} {series.away_team} ({series.away_team_wins}) {suffix_padding}\n'
                f'{prefix_padding}---------{suffix_padding}\n'
                f'{vertical_line_str}'
                f'{suffix_whitespace}---{prefix_whitespace}\n'
                f'{vertical_line_str}'
                f'{prefix_padding}---------{suffix_padding}\n'
                f'{prefix_padding} {series.home_team} ({series.home_team_wins}) {suffix_padding}\n'
                f'           \n'
            )

    def print_postseason_bracket(self) -> None:

        postseason = self.result.postseason
        if postseason is None:
            return

        self._print_header("PLAYOFFS")
        print()

        leagues = sorted({series.league for round_series in postseason.rounds.values() for series in round_series if series.league})
        world_series_list = postseason.rounds.get(PostseasonRound.WORLD_SERIES.value, [])

        # SIMPLE LISTING WHEN THE FULL 2-LEAGUE BRACKET DOESN'T APPLY (TOURNAMENTS)
        if len(leagues) != 2 or len(world_series_list) == 0:
            for round_value, series_list in postseason.rounds.items():
                for series in series_list:
                    print(f"{round_value}: {series.away_team} ({series.away_team_wins}) @ {series.home_team} ({series.home_team_wins}) -> {series.winner}")
            if postseason.world_series_winner:
                print(f"\nCHAMPION: {postseason.world_series_winner}")
            return

        def horizontal_join(str1, str2) -> str:
            return "\n".join(["".join(elem) for elem in zip(str1, str2)])

        league_brackets = {league: '' for league in leagues}

        for league in leagues:
            is_reversed = league == leagues[0]  # FIRST LEAGUE (AL) RENDERS ON THE RIGHT, REVERSED
            round_strings = []
            for round_value, series_list in postseason.rounds.items():
                if round_value == PostseasonRound.WORLD_SERIES.value:
                    continue
                future_rounds = len(postseason.rounds) - len(round_strings)
                final_str = ""
                blank_line = '           \n'
                for _ in round_strings:
                    for _ in range(2):
                        final_str += blank_line
                for series in series_list:
                    if series.league == league:
                        final_str += self._series_bracket_str(series=series, format=postseason.format, is_reversed=is_reversed)

                for _ in range(future_rounds):
                    final_str += blank_line

                round_strings.append(final_str)

            league_bracket = ""
            if is_reversed:
                round_strings.reverse()
            for index in range(len(round_strings) - 1):
                left_side = league_bracket if index > 0 else round_strings[index]
                right_side = round_strings[index + 1]
                league_bracket = horizontal_join(left_side.split("\n"), right_side.split("\n"))
            league_brackets[league] = league_bracket

        # ADD WORLD SERIES BETWEEN THE LEAGUE BRACKETS
        world_series_text = self._series_bracket_str(series=world_series_list[0], format=postseason.format)
        final_bracket = horizontal_join(league_brackets[leagues[1]].split("\n"), world_series_text.split("\n"))
        final_bracket = horizontal_join(final_bracket.split("\n"), league_brackets[leagues[0]].split("\n"))
        print(final_bracket)

    # ------------------------------------------------------------------
    # TRANSACTIONS
    # ------------------------------------------------------------------

    def print_transactions(self, limit: int = 100, teams: Optional[list[str]] = None) -> None:
        self._print_header("TRANSACTIONS")
        transactions = self.result.transactions
        if teams:
            transactions = [t for t in transactions if t.team in teams]

        if not transactions:
            print("  NO TRANSACTIONS (INJURIES DISABLED)" if not self.result.config.enable_injuries else "  NO TRANSACTIONS")
            return

        summary = self.result.injury_summary_by_team()
        summary_tbl = PrettyTable()
        summary_tbl.field_names = ['Team', 'IL Stints', 'Games Missed', 'Callups']
        summary_tbl.align['Team'] = 'l'
        for team, counts in sorted(summary.items(), key=lambda kv: kv[1]['games_missed'], reverse=True):
            if teams and team not in teams:
                continue
            summary_tbl.add_row([team, counts['stints'], counts['games_missed'], counts['callups']])
        print(summary_tbl)

        detail_tbl = PrettyTable()
        detail_tbl.field_names = ['Date', 'Team', 'Type', 'Player', 'Pos', 'Days', 'Return', 'Related', 'Detail']
        detail_tbl.align['Player'] = 'l'
        detail_tbl.align['Related'] = 'l'
        for t in transactions[:limit]:
            detail_tbl.add_row([
                t.date, t.team, t.type.value, t.player_name, t.position,
                t.il_days or '', t.return_date or '', t.related_player_name or '', t.detail,
            ])
        print(detail_tbl)
        if len(transactions) > limit:
            print(f"  ... {len(transactions) - limit} more")

    # ------------------------------------------------------------------
    # RUNTIME
    # ------------------------------------------------------------------

    def print_runtime(self) -> None:
        total_seconds = self.result.runtime_seconds
        mins_duration = int(total_seconds // 60)
        seconds_duration = round(total_seconds, (0 if total_seconds > 1 else 1)) if total_seconds < 60 else round(total_seconds % 60)
        mins_str = f" {mins_duration} MINUTES" if mins_duration > 0 else ""
        seconds_str = f" {seconds_duration} SECONDS" if seconds_duration > 0 else ""
        self._print_header("DONE")
        print(f"RAN IN{mins_str}{seconds_str}")
