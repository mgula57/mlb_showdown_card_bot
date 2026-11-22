from typing import Optional

from ..mlb_stats_api import MLBStatsAPI, Player
from .sets import Set
from .showdown_player_card import ShowdownPlayerCard
from .stats.normalized_player_stats import PlayerStatsNormalizer
from .stats.stats_period import StatsPeriod, StatsPeriodLeague, StatsPeriodType


class MinorLeagueCardBuilder:
    """Builds cards from a player's minor-league stats, for players without a big-league card.

    Minor-league numbers run hot against MLB pitching and hitting, so cards are built with a
    run-value penalty (`NERF_BY_RUN_VALUE`). `build_many(nerf_small_samples_only=True)` keeps it
    only for a thin season (the offseason transaction feed shows a prospect's full line as it is).
    The card's stats period carries the MILB league, which is how the rest of the app tells these
    apart from MLB cards.
    """

    NERF_BY_RUN_VALUE = 25
    # A season this thin makes a card out of noise. `build_many` skips anything under it.
    MIN_PA_HITTER = 50
    MIN_IP_PITCHER = 15
    # Under these, a season is still small enough to run hot, so `nerf_small_samples_only` nerfs it.
    SMALL_SAMPLE_PA_HITTER = 150
    SMALL_SAMPLE_IP_PITCHER = 40

    def __init__(self, mlb_stats_api: MLBStatsAPI):
        self.api = mlb_stats_api

    @classmethod
    def card_from_player(cls, player: Player, year: int, set: Set, name: Optional[str] = None,
                         nerf_by_run_value: Optional[float] = NERF_BY_RUN_VALUE, **card_fields) -> Optional[ShowdownPlayerCard]:
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
            nerf_by_run_value=nerf_by_run_value,
            **card_fields,
        )

    def build_many(self, mlb_ids: list[int], year: int, set: Set, fallback_years: int = 1,
                   nerf_small_samples_only: bool = False) -> dict[int, ShowdownPlayerCard]:
        """Minor-league cards for each player with enough of a season, keyed by MLB id.

        Tries `year` first, then each prior year up to `fallback_years` back for anyone still
        missing (a player hurt for most of `year`). One batched MLB API call per year tried.
        `nerf_small_samples_only` builds a full season un-nerfed and nerfs only one under
        `SMALL_SAMPLE_PA_HITTER` / `SMALL_SAMPLE_IP_PITCHER`. Player type comes from the built card,
        so a thin season is built twice - a handful of cards per call.
        """
        cards: dict[int, ShowdownPlayerCard] = {}
        remaining = list(dict.fromkeys(mlb_ids))
        for card_year in range(year, year - fallback_years - 1, -1):
            if not remaining:
                break
            players = self.api.build_players_from_id_list(player_ids=remaining, seasons=[card_year], league='MILB').players
            for player in players:
                try:
                    card = self.card_from_player(player, year=card_year, set=set, nerf_by_run_value=None if nerf_small_samples_only else self.NERF_BY_RUN_VALUE)
                    if card is not None and nerf_small_samples_only and not self._has_sample(card, self.SMALL_SAMPLE_PA_HITTER, self.SMALL_SAMPLE_IP_PITCHER):
                        card = self.card_from_player(player, year=card_year, set=set)
                except Exception:
                    # No usable stats that year (e.g. zero PA); try the next year back.
                    continue
                if card is not None and self._has_sample(card, self.MIN_PA_HITTER, self.MIN_IP_PITCHER):
                    cards[player.id] = card
            remaining = [mlb_id for mlb_id in remaining if mlb_id not in cards]
        return cards

    @staticmethod
    def _has_sample(card: ShowdownPlayerCard, min_pa: int, min_ip: int) -> bool:
        if card.is_pitcher:
            return float(card.stats.get('IP', 0) or 0) >= min_ip
        return float(card.stats.get('PA', 0) or 0) >= min_pa


__all__ = ['MinorLeagueCardBuilder']
