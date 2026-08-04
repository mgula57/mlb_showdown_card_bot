from datetime import date as dt_date, datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from ..base_client import BaseMLBClient
from ..models.games.schedule import Schedule, GameScheduled
from ..models.teams.team import ShowdownTeam


class GamesClient(BaseMLBClient):
    """Client for game-related MLB Stats API endpoints."""

    # -------------------------
    # BOXSCORE / GAME DETAIL
    # -------------------------

    def get_game_boxscore(self, game_pk: int) -> dict:
        """Fetch boxscore + linescore for a single game and return a trimmed payload.

        Uses the MLB Stats API ``/game/{gamePk}/feed/live`` endpoint which
        provides ``gameData``, ``liveData.boxscore`` and ``liveData.linescore``
        in one call, then distills the ~200 KB response down to a compact dict
        suitable for the frontend boxscore view.
        """
        raw = self._make_request(f"../v1.1/game/{game_pk}/feed/live")

        game_data = raw.get("gameData", {})
        live_data = raw.get("liveData", {})
        boxscore = live_data.get("boxscore", {})
        linescore_raw = live_data.get("linescore", {})
        decisions_raw = live_data.get("decisions", {})
        plays_raw = live_data.get("plays", {})

        def _extract_team_info(side: str) -> dict:
            team_raw = game_data.get("teams", {}).get(side, {})
            abbreviation = team_raw.get("abbreviation", "")
            team_match = ShowdownTeam.map_from_mlb_api_team(abbreviation)
            return {
                "id": team_raw.get("id"),
                "name": team_raw.get("name"),
                "abbreviation": team_raw.get("abbreviation", ""),
                "record": team_raw.get("record", {}),
                "primary_color": f"rgb({team_match.primary_color[0]}, {team_match.primary_color[1]}, {team_match.primary_color[2]})" if team_match else None,
                "secondary_color": f"rgb({team_match.secondary_color[0]}, {team_match.secondary_color[1]}, {team_match.secondary_color[2]})" if team_match else None,
            }

        def _extract_team_boxscore(side: str) -> dict:
            team_box = boxscore.get("teams", {}).get(side, {})
            players_dict = team_box.get("players", {})
            batting_order_ids: list[int] = team_box.get("battingOrder", [])
            pitcher_ids: list[int] = team_box.get("pitchers", [])
            batter_ids: list[int] = team_box.get("batters", [])

            def _batter_row(player_id: int) -> dict | None:
                p = players_dict.get(f"ID{player_id}")
                if not p:
                    return None
                b_stats = (p.get("stats") or {}).get("batting", {})
                s_stats = (p.get("seasonStats") or {}).get("batting", {})
                positions = p.get("allPositions") or []
                pos_abbr = "-".join(pos.get("abbreviation", "?") for pos in positions) if positions else (p.get("position", {}).get("abbreviation", ""))
                is_in_lineup = player_id in batting_order_ids
                return {
                    "id": player_id,
                    "name": (p.get("person") or {}).get("fullName", ""),
                    "jersey_number": p.get("jerseyNumber", ""),
                    "position": pos_abbr,
                    "batting_order": p.get("battingOrder", ""),
                    "is_substitute": (p.get("gameStatus") or {}).get("isSubstitute", False),
                    "is_in_lineup": is_in_lineup,
                    "stats": {
                        "summary": b_stats.get("summary", ""),
                        "at_bats": b_stats.get("atBats", 0),
                        "runs": b_stats.get("runs", 0),
                        "hits": b_stats.get("hits", 0),
                        "rbi": b_stats.get("rbi", 0),
                        "base_on_balls": b_stats.get("baseOnBalls", 0),
                        "strike_outs": b_stats.get("strikeOuts", 0),
                        "home_runs": b_stats.get("homeRuns", 0),
                        "stolen_bases": b_stats.get("stolenBases", 0),
                        "left_on_base": b_stats.get("leftOnBase", 0),
                    },
                    "season_stats": {
                        "avg": s_stats.get("avg", ".---"),
                        "obp": s_stats.get("obp", ".---"),
                        "ops": s_stats.get("ops", ".---"),
                    },
                }

            def _pitcher_row(player_id: int) -> dict | None:
                p = players_dict.get(f"ID{player_id}")
                if not p:
                    return None
                pi_stats = (p.get("stats") or {}).get("pitching", {})
                ps_stats = (p.get("seasonStats") or {}).get("pitching", {})
                if not pi_stats:
                    return None
                return {
                    "id": player_id,
                    "name": (p.get("person") or {}).get("fullName", ""),
                    "jersey_number": p.get("jerseyNumber", ""),
                    "stats": {
                        "summary": pi_stats.get("summary", ""),
                        "note": pi_stats.get("note", ""),
                        "innings_pitched": pi_stats.get("inningsPitched", "0.0"),
                        "hits": pi_stats.get("hits", 0),
                        "runs": pi_stats.get("runs", 0),
                        "earned_runs": pi_stats.get("earnedRuns", 0),
                        "base_on_balls": pi_stats.get("baseOnBalls", 0),
                        "strike_outs": pi_stats.get("strikeOuts", 0),
                        "home_runs": pi_stats.get("homeRuns", 0),
                        "pitches_thrown": pi_stats.get("pitchesThrown", 0) or pi_stats.get("numberOfPitches", 0),
                        "strikes": pi_stats.get("strikes", 0),
                        "batters_faced": pi_stats.get("battersFaced", 0),
                    },
                    "season_stats": {
                        "era": ps_stats.get("era", "-.--"),
                        "wins": ps_stats.get("wins", 0),
                        "losses": ps_stats.get("losses", 0),
                    },
                }

            # Build ordered batting list: lineup batters first (in lineup order),
            # then any substitutes who appeared but aren't in the original batting order.
            batting: list[dict] = []
            seen_ids: set[int] = set()
            for bid in batter_ids:
                row = _batter_row(bid)
                if row and bid not in seen_ids:
                    batting.append(row)
                    seen_ids.add(bid)

            pitching: list[dict] = []
            for pid in pitcher_ids:
                row = _pitcher_row(pid)
                if row:
                    pitching.append(row)

            # Team totals
            team_stats_raw = team_box.get("teamStats", {})
            t_bat = team_stats_raw.get("batting", {})
            t_pit = team_stats_raw.get("pitching", {})
            t_fld = team_stats_raw.get("fielding", {})

            return {
                "team": _extract_team_info(side),
                "batting": batting,
                "pitching": pitching,
                "batting_totals": {
                    "at_bats": t_bat.get("atBats", 0),
                    "runs": t_bat.get("runs", 0),
                    "hits": t_bat.get("hits", 0),
                    "rbi": t_bat.get("rbi", 0),
                    "base_on_balls": t_bat.get("baseOnBalls", 0),
                    "strike_outs": t_bat.get("strikeOuts", 0),
                    "home_runs": t_bat.get("homeRuns", 0),
                    "stolen_bases": t_bat.get("stolenBases", 0),
                    "left_on_base": t_bat.get("leftOnBase", 0),
                    "avg": t_bat.get("avg", ".---"),
                    "ops": t_bat.get("ops", ".---"),
                },
                "pitching_totals": {
                    "innings_pitched": t_pit.get("inningsPitched", "0.0"),
                    "hits": t_pit.get("hits", 0),
                    "runs": t_pit.get("runs", 0),
                    "earned_runs": t_pit.get("earnedRuns", 0),
                    "base_on_balls": t_pit.get("baseOnBalls", 0),
                    "strike_outs": t_pit.get("strikeOuts", 0),
                    "home_runs": t_pit.get("homeRuns", 0),
                    "pitches_thrown": t_pit.get("pitchesThrown", 0) or t_pit.get("numberOfPitches", 0),
                    "strikes": t_pit.get("strikes", 0),
                    "era": t_pit.get("era", "-.--"),
                },
                "info": team_box.get("info", []),
                "note": team_box.get("note", ""),
            }

        def _extract_decision(key: str) -> dict | None:
            d = decisions_raw.get(key)
            if not d:
                return None
            return {
                "id": d.get("id"),
                "full_name": d.get("fullName", ""),
                "link": d.get("link", ""),
            }
        
        def _extract_play(play: dict) -> dict:
            """Trim a single raw play down to the fields the frontend needs: result, matchup,
            about, and count (for the post-play out count)."""
            return {
                "result": play.get("result", {}),
                "matchup": play.get("matchup", {}),
                "about": play.get("about", {}),
                "count": play.get("count", {}),
            }

        def _extract_most_recent_play(plays: dict) -> dict | None:
            """Extract details of the most recent play from the plays data."""
            all_plays = plays.get("allPlays", [])
            if not all_plays:
                return None
            return _extract_play(all_plays[-1])

        def _extract_all_plays(plays: dict) -> list[dict]:
            """Full play-by-play list (one entry per plate appearance), oldest first."""
            return [_extract_play(p) for p in plays.get("allPlays", [])]

        def _person(node: dict | None) -> dict | None:
            """Trim a linescore offense/defense slot to id + name. None when the slot is empty
            (base unoccupied, no on-deck hitter between innings, defense not yet set)."""
            if not node or not node.get("id"):
                return None
            return {"id": node.get("id"), "full_name": node.get("fullName", "")}

        # Linescore
        ls_offense = linescore_raw.get("offense") or {}
        ls_defense = linescore_raw.get("defense") or {}
        innings = []
        for inn in linescore_raw.get("innings", []):
            innings.append({
                "num": inn.get("num"),
                "ordinal_num": inn.get("ordinalNum"),
                "away": {"runs": (inn.get("away") or {}).get("runs")},
                "home": {"runs": (inn.get("home") or {}).get("runs")},
            })

        ls_teams = linescore_raw.get("teams", {})

        return {
            "game_pk": game_pk,
            "status": {
                "abstract_game_state": game_data.get("status", {}).get("abstractGameState"),
                "coded_game_state": game_data.get("status", {}).get("codedGameState"),
                "detailed_state": game_data.get("status", {}).get("detailedState"),
                "status_code": game_data.get("status", {}).get("statusCode"),
                "reason": game_data.get("status", {}).get("reason"),
            },
            "datetime": {
                "date_time": game_data.get("datetime", {}).get("dateTime"),
                "official_date": game_data.get("datetime", {}).get("officialDate"),
            },
            "teams": {
                "away": _extract_team_boxscore("away"),
                "home": _extract_team_boxscore("home"),
            },
            "linescore": {
                "current_inning": linescore_raw.get("currentInning"),
                "current_inning_ordinal": linescore_raw.get("currentInningOrdinal"),
                "inning_state": linescore_raw.get("inningState"),
                "inning_half": linescore_raw.get("inningHalf"),
                "is_top_inning": linescore_raw.get("isTopInning"),
                "scheduled_innings": linescore_raw.get("scheduledInnings"),
                "outs": linescore_raw.get("outs"),
                "balls": linescore_raw.get("balls"),
                "strikes": linescore_raw.get("strikes"),
                "offense": {
                    slot: _person(ls_offense.get(raw_key))
                    for slot, raw_key in (
                        ("batter", "batter"), ("on_deck", "onDeck"), ("in_hole", "inHole"),
                        ("first", "first"), ("second", "second"), ("third", "third"),
                    )
                },
                "defense": {
                    slot: _person(ls_defense.get(raw_key))
                    for slot, raw_key in (
                        ("pitcher", "pitcher"), ("catcher", "catcher"), ("first", "first"),
                        ("second", "second"), ("third", "third"), ("shortstop", "shortstop"),
                        ("left", "left"), ("center", "center"), ("right", "right"),
                    )
                },
                "innings": innings,
                "teams": {
                    "away": {
                        "runs": (ls_teams.get("away") or {}).get("runs", 0),
                        "hits": (ls_teams.get("away") or {}).get("hits", 0),
                        "errors": (ls_teams.get("away") or {}).get("errors", 0),
                    },
                    "home": {
                        "runs": (ls_teams.get("home") or {}).get("runs", 0),
                        "hits": (ls_teams.get("home") or {}).get("hits", 0),
                        "errors": (ls_teams.get("home") or {}).get("errors", 0),
                    },
                },
            },
            "decisions": {
                "winner": _extract_decision("winner"),
                "loser": _extract_decision("loser"),
                "save": _extract_decision("save"),
            },
            "probable_pitchers": {
                side: {
                    "id": pitcher.get("id"),
                    "full_name": pitcher.get("fullName", ""),
                }
                for side, pitcher in game_data.get("probablePitchers", {}).items()
                if pitcher
            },
            "most_recent_play": _extract_most_recent_play(plays_raw),
            "plays": _extract_all_plays(plays_raw),
        }

    def get_all_star_rosters(self, season: int, sport_id: int = 1) -> list[dict]:
        """Return All-Star Game participants for a season, split by league (AL/NL).

        Locates the season's All-Star Game via ``gameType=A`` on the schedule, then reads the
        game's live feed to extract each team's participants with their real starting lineup
        position, batting order, and starting pitcher. Each returned row:
        ``{league, mlb_id, player_name, position, batting_order, is_starter, is_starting_pitcher}``.

        Returns an empty list if no All-Star Game is found for the season.
        """
        schedule = self.get_schedule(sport_id=sport_id, season=season, game_type="A", use_date=False)

        game_pk: Optional[int] = None
        for date_block in (schedule.dates or []):
            for game in (date_block.games or []):
                game_pk = game.game_pk
                break
            if game_pk is not None:
                break
        if game_pk is None:
            return []

        raw = self._make_request(f"../v1.1/game/{game_pk}/feed/live")
        game_data = raw.get("gameData", {})
        boxscore = raw.get("liveData", {}).get("boxscore", {})

        # MLB league ids: 103 = American League, 104 = National League.
        def _league_for_side(side: str) -> str:
            league = game_data.get("teams", {}).get(side, {}).get("league", {}) or {}
            if league.get("id") == 103:
                return "AL"
            if league.get("id") == 104:
                return "NL"
            name = (league.get("name") or "").lower()
            return "AL" if "american" in name else "NL"

        rows: list[dict] = []
        for side in ("away", "home"):
            league = _league_for_side(side)
            team_box = boxscore.get("teams", {}).get(side, {})
            players = team_box.get("players", {}) or {}
            batting_order_ids: list[int] = team_box.get("battingOrder", []) or []
            pitcher_ids: list[int] = team_box.get("pitchers", []) or []
            starting_pitcher_id = pitcher_ids[0] if pitcher_ids else None
            starter_batting_order = {pid: i + 1 for i, pid in enumerate(batting_order_ids)}

            for key, player in players.items():
                person = player.get("person") or {}
                mlb_id = person.get("id")
                if mlb_id is None:
                    continue
                position = (player.get("position") or {}).get("abbreviation")
                is_starter = mlb_id in starter_batting_order
                rows.append({
                    "league": league,
                    "mlb_id": mlb_id,
                    "player_name": person.get("fullName"),
                    "position": position,
                    "batting_order": starter_batting_order.get(mlb_id),
                    "is_starter": is_starter,
                    "is_starting_pitcher": mlb_id == starting_pitcher_id,
                })
        return rows

    def _resolve_target_date(self, date_str: Optional[str], tz_name: str) -> dt_date:
        if date_str:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        return datetime.now(ZoneInfo(tz_name)).date()

    def _build_window(self, target_date: dt_date) -> tuple[str, str]:
        return (
            (target_date - timedelta(days=1)).isoformat(),
            (target_date + timedelta(days=1)).isoformat(),
        )

    def _filter_schedule_to_local_date(
        self,
        response: dict,
        target_date: dt_date,
        tz_name: str,
    ) -> dict:
        tz = ZoneInfo(tz_name)
        filtered_dates: list[dict] = []
        total_games = 0

        for date_block in response.get("dates", []):
            games = date_block.get("games", [])
            kept_games = []

            for game in games:
                game_date_raw = game.get("gameDate")
                if not game_date_raw:
                    continue

                try:
                    game_dt_utc = datetime.fromisoformat(game_date_raw.replace("Z", "+00:00"))
                except ValueError:
                    continue

                local_game_date = game_dt_utc.astimezone(tz).date()
                if local_game_date == target_date:
                    kept_games.append(game)

            if kept_games:
                block = dict(date_block)
                block["games"] = kept_games
                block["totalGames"] = len(kept_games)
                filtered_dates.append(block)
                total_games += len(kept_games)

        filtered_response = dict(response)
        filtered_response["dates"] = filtered_dates
        filtered_response["totalGames"] = total_games
        filtered_response["totalItems"] = total_games
        return filtered_response

    def get_schedule(
        self,
        sport_id: int = 1,
        season: Optional[int] = None,
        date: Optional[str] = None,
        league_ids: Optional[list[int]] = None,
        includeProbablePitchers: bool = False,
        tz_name: str = "America/New_York",
        use_date_window: bool = True,
        include_linescore: bool = False,
        include_decisions: bool = False,
        game_type: Optional[str] = None,
        use_date: bool = True,
    ) -> Schedule:
        """Get schedule for a local day (US-safe by default), with optional probable pitchers.

        ``game_type`` filters to a single MLB game type (e.g. ``"A"`` for the All-Star Game).
        Pass ``use_date=False`` to query the whole season (no date/date-window params) — needed
        when locating a season-unique game like the ASG whose date isn't known in advance.
        """
        params = {"sportId": sport_id}

        if season:
            params["season"] = season
        if league_ids:
            params["leagueIds"] = league_ids
        if game_type:
            params["gameType"] = game_type

        target_date = self._resolve_target_date(date, tz_name)

        if not use_date:
            use_date_window = False
        elif use_date_window:
            start_date, end_date = self._build_window(target_date)
            params["startDate"] = start_date
            params["endDate"] = end_date
        else:
            params["date"] = target_date.isoformat()

        params["hydrate"] = "team"
        if includeProbablePitchers:
            params["hydrate"] += ",probablePitcher(note)"
        if include_linescore:
            params["hydrate"] += ",linescore"
        if include_decisions:
            params["hydrate"] += ",decisions"

        response = self._make_request("/schedule", params=params)

        if use_date_window:
            response = self._filter_schedule_to_local_date(
                response=response,
                target_date=target_date,
                tz_name=tz_name,
            )

        return Schedule(**response)

    def get_season_schedule(self, season: int, sport_id: int = 1, game_types: list[str] = ["R"]) -> Schedule:
        """Get every game for a season (regular season only by default).

        Returns a Schedule with `games` flattened across all dates, ordered by date.
        Postponed/cancelled games are excluded so per-team game counts stay accurate.
        """
        params = {
            "sportId": sport_id,
            "season": season,
            "startDate": f"{season}-01-01",
            "endDate": f"{season}-12-31",
            "gameTypes": ",".join(game_types),
            "hydrate": "team",
        }
        response = self._make_request("/schedule", params=params)
        schedule = Schedule(**response)

        excluded_states = {"Postponed", "Cancelled", "Suspended"}
        games: list[GameScheduled] = []
        for schedule_date in (schedule.dates or []):
            for game in (schedule_date.games or []):
                if game.status and game.status.detailed_state in excluded_states:
                    continue
                games.append(game)
        schedule.games = games
        return schedule