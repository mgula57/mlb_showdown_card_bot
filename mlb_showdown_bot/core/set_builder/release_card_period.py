from datetime import date
from typing import Optional
from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.stats.stats_period import SeasonHalf, StatsPeriodType
from ..database.postgres_db import PostgresDB
from ..mlb_stats_api.clients.seasons_client import SeasonsClient
from .release_card_rebuilder import ReleaseCardRebuilder


class ReleaseCardPeriodError(ValueError):
    """The card can't be built for the stats period (e.g. no games in that half of the season)."""


class SeasonHalfCalendar:
    """When each half of a season runs, split at the All-Star break by MLB's season calendar.
    A past season's calendar never changes, so it's looked up once per process."""

    _client = SeasonsClient()
    _halves: dict[int, tuple[date, date, date, date]] = {}

    @classmethod
    def dates(cls, year: int, half: SeasonHalf) -> tuple[date, date]:
        """The first and last day of `half` in `year`. Raises ReleaseCardPeriodError without a calendar."""
        if year not in cls._halves:
            season = cls._client.get_season(year)
            bounds = [
                season.regular_season_start_date, season.last_date_1st_half,
                season.first_date_2nd_half, season.regular_season_end_date,
            ] if season else []
            if not all(bounds):
                raise ReleaseCardPeriodError(f"No All-Star break dates found for {year}.")
            cls._halves[year] = tuple(date.fromisoformat(value) for value in bounds)
        first_start, first_end, second_start, second_end = cls._halves[year]
        return (first_start, first_end) if half == SeasonHalf.FIRST_HALF else (second_start, second_end)


class ReleaseCardPeriod:
    """Rebuilds an archived full-season card for an edition's stats period (a half of the season).

    The half becomes a date range over the card's archived game logs, so no stats are fetched from
    the web. The result is the full card JSON, embedded in the release card snapshot (`card_data`)
    like a variable speed or custom card, since the archive only holds the full-season version.
    """

    def __init__(self, db: PostgresDB) -> None:
        self.db = db

    def card_for_half(self, card: ShowdownPlayerCard, half: SeasonHalf) -> ShowdownPlayerCard:
        period = card.stats_period
        if period.type != StatsPeriodType.REGULAR_SEASON or period.year_int is None or card.is_wotc:
            raise ReleaseCardPeriodError('Only single-season Showdown Bot cards can be built for half of a season.')
        start_date, end_date = SeasonHalfCalendar.dates(period.year_int, half)

        card_data = card.as_json()
        stats = card_data.get('stats') or {}
        if not stats.get('game_logs'):
            stats = self._archived_stats(card)
        stats_period = {
            **card_data['stats_period'],
            'type': StatsPeriodType.DATE_RANGE.value,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'season_half': half.value,
        }
        for derived in ('stats', 'display_text'):
            stats_period.pop(derived, None)
        image = {k: v for k, v in (card_data.get('image') or {}).items() if k not in ReleaseCardRebuilder.IMAGE_OUTPUT_FIELDS}

        half_card = ShowdownPlayerCard.rebuilt_from_card_data({**card_data, 'stats': stats, 'stats_period': stats_period, 'image': image})
        # A period with no games falls back to the full season's stats, which would pass for the half
        if not half_card.stats_period.stats or half_card.stats_period.empty_message in half_card.warnings:
            raise ReleaseCardPeriodError(f"{card.name} has no games in the {half.card_text.lower()} of {period.year_int}.")
        return half_card

    def apply_to_row(self, row: dict, card: ShowdownPlayerCard, half: SeasonHalf, variable_speed: bool = False) -> ShowdownPlayerCard:
        """Overwrites a `card_bot` row's card-derived columns with the card's half-season version and
        embeds it (`card_data`), so renders and rosters load it instead of the archived card."""
        half_card = self.card_for_half(card, half)
        if variable_speed:
            half_card.apply_variable_speed_00_01(True)
        row.update(half_card.card_bot_columns())
        row['card_data'] = half_card.as_json()
        if half_card.is_variable_speed_00_01:
            row['is_variable_speed_00_01'] = True
        return half_card

    def snapshot(self, card_id: str, half: SeasonHalf, variable_speed: bool = False) -> dict:
        """The release card snapshot of an archived card for `half`, as manual add snapshots it."""
        rows = self.db.fetch_card_list({'card_id': [card_id], 'limit': 1, 'variable_speed': variable_speed})
        card = self.db.fetch_cards_for_roster_slots([{'card_id': card_id, 'card_source': 'BOT'}]).get(str(card_id))
        if not rows or card is None:
            raise ReleaseCardPeriodError('Card not found in the archive.')
        self.apply_to_row(rows[0], card, half, variable_speed)
        return rows[0]

    def _archived_stats(self, card: ShowdownPlayerCard) -> dict:
        """The player-season's archived stats, which carry the game logs the card's own copy may have dropped."""
        archive, _ = self.db.fetch_player_stats_from_archive(
            year=str(card.stats_period.year_int), bref_id=card.bref_id,
            team_override=card.stats_period.team_override, type_override=card.stats_period.player_type_override,
        )
        if archive is None or not (archive.stats or {}).get('game_logs'):
            raise ReleaseCardPeriodError(f"No game logs are archived for {card.name} in {card.stats_period.year_int}.")
        return archive.stats
