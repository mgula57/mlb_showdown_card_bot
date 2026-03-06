from datetime import date as dt_date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from ..base_client import BaseMLBClient
from ..models.games.schedule import Schedule, GameScheduled


class GamesClient(BaseMLBClient):
    """Client for game-related MLB Stats API endpoints."""

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
        league_id: Optional[int] = None,
        includeProbablePitchers: bool = False,
        tz_name: str = "America/New_York",
        use_date_window: bool = True,
        include_linescore: bool = False,
        include_decisions: bool = False,
    ) -> Schedule:
        """Get schedule for a local day (US-safe by default), with optional probable pitchers."""
        params = {"sportId": sport_id}

        if season:
            params["season"] = season
        if league_id:
            params["leagueId"] = league_id

        target_date = self._resolve_target_date(date, tz_name)

        if use_date_window:
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