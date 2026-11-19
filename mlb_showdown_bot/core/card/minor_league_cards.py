from typing import Optional

from ..mlb_stats_api import MLBStatsAPI, Player
from .sets import Set
from .showdown_player_card import ShowdownPlayerCard
from .stats.normalized_player_stats import PlayerStatsNormalizer
from .stats.stats_period import StatsPeriod, StatsPeriodLeague, StatsPeriodType


class MinorLeagueCardBuilder:
    """Builds cards from a player's minor-league stats, for players without a big-league card.

    Minor-league numbers run hot against MLB pitching and hitting, so every card is built with a
    run-value penalty (`NERF_BY_RUN_VALUE`). The card's stats period carries the MILB league, which
    is how the rest of the app tells these apart from MLB cards.
    """

    NERF_BY_RUN_VALUE = 25
    # A season this thin makes a card out of noise. `build_many` skips anything under it.
    MIN_PA_HITTER = 50
    MIN_IP_PITCHER = 15

    def __init__(self, mlb_stats_api: MLBStatsAPI):
        self.api = mlb_stats_api

    @classmethod
    def card_from_player(cls, player: Player, year: int, set: Set, name: Optional[str] = None, **card_fields) -> Optional[ShowdownPlayerCard]:
        """A card from a player already fetched with minor-league stats, or None if there are none
        to build from. `card_fields` pass through to the card (e.g. a WBC team and image)."""
        if not player or not player.stats:
            return None
        # Same as the Card Builder's MiLB cards: the stats period carries the league, which gives
        # the card the generic MILB team and keeps rookie status off it.
        stats_period = StatsPeriod(year=str(year), type=StatsPeriodType.REGULAR_SEASON, league=StatsPeriodLeague.MILB)
        stats = PlayerStatsNormalizer.from_mlb_api(player=player, stats_period=stats_period).as_dict()
        return ShowdownPlayerCard(
            name=name or player.full_name,
            year=str(year),
            set=set,
            mlb_id=player.id,
            league="MILB",
            era="DYNAMIC",
            stats_period=stats_period,
            stats=stats,
            nerf_by_run_value=cls.NERF_BY_RUN_VALUE,
            **card_fields,
        )

    def build_many(self, mlb_ids: list[int], year: int, set: Set, fallback_years: int = 1) -> dict[int, ShowdownPlayerCard]:
        """Minor-league cards for each player with enough of a season, keyed by MLB id.

        Tries `year` first, then each prior year up to `fallback_years` back for anyone still
        missing (a player hurt for most of `year`). One batched MLB API call per year tried.
        """
        cards: dict[int, ShowdownPlayerCard] = {}
        remaining = list(dict.fromkeys(mlb_ids))
        for card_year in range(year, year - fallback_years - 1, -1):
            if not remaining:
                break
            players = self.api.build_players_from_id_list(player_ids=remaining, seasons=[card_year], league='MILB').players
            for player in players:
                try:
                    card = self.card_from_player(player, year=card_year, set=set)
                except Exception:
                    # No usable stats that year (e.g. zero PA); try the next year back.
                    continue
                if card is not None and self._has_enough_sample(card):
                    cards[player.id] = card
            remaining = [mlb_id for mlb_id in remaining if mlb_id not in cards]
        return cards

    @classmethod
    def _has_enough_sample(cls, card: ShowdownPlayerCard) -> bool:
        if card.is_pitcher:
            return float(card.stats.get('IP', 0) or 0) >= cls.MIN_IP_PITCHER
        return float(card.stats.get('PA', 0) or 0) >= cls.MIN_PA_HITTER


__all__ = ['MinorLeagueCardBuilder']
