"""WBC edition cards must resolve their roster team from whichever datasource found the player.

No database, no network: runs as `python tests/test_wbc_team_lookup.py` anywhere.
"""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from mlb_showdown_bot.core.card import card_generation
from mlb_showdown_bot.core.card.showdown_player_card import PlayerType
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod
from mlb_showdown_bot.core.database.postgres_db import PostgresDB


class CardReached(Exception):
    """Stops generate_card right after the WBC lookup, before any image work."""


def _generate_wbc_card(datasource: str) -> tuple[MagicMock, dict]:
    db = MagicMock()
    db.__enter__.return_value = db
    db.fetch_wbc_team_for_player.return_value = ("AUS", 2026)
    db.fetch_bref_id_for_mlb_id.return_value = None
    db.fetch_fangraphs_fielding_stats.return_value = []
    db.fetch_bref_award_voting.return_value = []

    mlb_api = MagicMock()
    player = mlb_api.return_value.build_full_player_from_search.return_value
    player.id = 683953
    player.fangraphs_id = None

    normalized = MagicMock(PA=100, bref_id=None)
    normalized.as_dict.return_value = {}

    with (
        patch.object(card_generation, "check_for_preprocessed_card", return_value=None),
        patch.object(card_generation, "PostgresDB", return_value=db),
        patch.object(card_generation, "MLBStatsAPI_V2", mlb_api),
        patch.object(card_generation, "StatcastAPIClient"),
        patch.object(card_generation.PlayerStatsNormalizer, "from_mlb_api", return_value=normalized),
        patch.object(card_generation, "BaseballReferenceScraper") as scraper,
        patch.object(card_generation, "ImageSource"),
        patch.object(card_generation, "ShowdownImage"),
        patch.object(card_generation, "ShowdownPlayerCard", side_effect=CardReached) as card,
    ):
        scraper.return_value.baseball_ref_id = "bazzatr01"
        scraper.return_value.stats_period.is_multi_year = False
        scraper.return_value.stats_period.year_int = 2026
        scraper.return_value.fetch_player_stats.return_value = {}
        card_generation.generate_card(
            name="Travis Bazzana", year="2026", set="2000", edition="WBC", datasource=datasource,
        )
    return db, card.call_args.kwargs


def test_mlb_api_card_looks_up_wbc_team_by_mlb_id():
    db, card_kwargs = _generate_wbc_card("MLB_API")

    db.fetch_wbc_team_for_player.assert_called_once_with(year=2026, mlb_id=683953, bref_id=None)
    assert card_kwargs["wbc_team"] == "AUS"
    assert card_kwargs["wbc_year"] == 2026


def test_bref_card_looks_up_wbc_team_by_bref_id():
    db, card_kwargs = _generate_wbc_card("BREF")

    db.fetch_wbc_team_for_player.assert_called_once_with(year=2026, mlb_id=None, bref_id="bazzatr01")
    assert card_kwargs["wbc_team"] == "AUS"


def _preprocessed_card(card_year: str, seasons: list[int], requested_year: str = "2026", league: str = "MLB"):
    db = MagicMock()
    db.__enter__.return_value = db
    card = SimpleNamespace(year=card_year, mlb_id=683953, player_type=PlayerType.HITTER)
    db.wbc_card_search.return_value = card
    stats_period = StatsPeriod(type="REGULAR", year=requested_year, league=league)

    with patch.object(card_generation, "PostgresDB", return_value=db), patch.object(card_generation, "MLBStatsAPI_V2") as mlb_api:
        mlb_api.return_value.people.get_player_seasons.return_value = seasons
        result = card_generation.check_for_preprocessed_card(
            stats_period=stats_period, name="Travis Bazzana", year=requested_year, set="2000", edition="WBC",
        )
    return result, card


def test_stored_card_skipped_once_player_has_mlb_stats_for_requested_year():
    result, _ = _preprocessed_card(card_year="2025", seasons=[2026])
    assert result is None


def test_stored_card_kept_for_player_without_mlb_stats_that_year():
    result, card = _preprocessed_card(card_year="2025", seasons=[])
    assert result is card


def test_stored_card_kept_when_requesting_its_own_year():
    result, card = _preprocessed_card(card_year="2025", seasons=[2026], requested_year="2025")
    assert result is card


def test_lookup_binds_mlb_id_as_text_to_match_roster_column():
    db = PostgresDB.__new__(PostgresDB)
    db.connection = MagicMock()
    cursor = db.connection.cursor.return_value
    cursor.fetchone.return_value = ("AUS", 2026)

    assert db.fetch_wbc_team_for_player(year=2026, mlb_id=683953) == ("AUS", 2026)
    assert cursor.execute.call_args.args[1] == ("683953", None, 2026, 2026)


if __name__ == "__main__":
    test_mlb_api_card_looks_up_wbc_team_by_mlb_id()
    test_bref_card_looks_up_wbc_team_by_bref_id()
    test_stored_card_skipped_once_player_has_mlb_stats_for_requested_year()
    test_stored_card_kept_for_player_without_mlb_stats_that_year()
    test_stored_card_kept_when_requesting_its_own_year()
    test_lookup_binds_mlb_id_as_text_to_match_roster_column()
    print("All WBC team lookup checks passed.")
