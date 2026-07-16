from typing import Optional

from .team import Team, TeamSource, TeamRosterSlot, Lineup, LineupSlot, PitcherAssignment, PickSource
from .autofill import OFFENSE_POSITIONS, _pos_matches, _card_source


class RosterToTeamConverter:
    """Convert a pool of card summary rows for a real MLB/WBC roster into a read-only Team.

    Used to present real rosters (sourced from the card archive) inside the team
    builder UI without going through the drafting flow. Unlike autofill
    (budget-driven and randomized), composition is deterministic and based on real
    playing time: lineup spots go to the eligible hitters with the most games
    played, the rotation is ordered by games started, and the closer role goes to
    the reliever with the most saves.
    """

    # The team builder UI only has SP1-SP5 role slots (ROTATION_ROLES is hardcoded
    # app-wide), so a starter beyond the 5th by games started is folded into the bullpen.
    MAX_ROTATION_SLOTS = 5

    def __init__(
        self,
        cards: list[dict],
        team_id: str,
        name: str,
        abbreviation: str,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
    ) -> None:
        self.cards = cards
        self.team_id = team_id
        self.name = name
        self.abbreviation = abbreviation
        self.primary_color = primary_color
        self.secondary_color = secondary_color

    # ------------------------------------------------------------------
    # SORT KEYS
    # ------------------------------------------------------------------

    @staticmethod
    def _by_games_played(card: dict) -> tuple:
        return (card.get('g') or 0, card.get('points') or 0)

    @staticmethod
    def _by_games_started(card: dict) -> tuple:
        return (card.get('gs') or 0, float(card.get('real_ip') or 0), card.get('points') or 0)

    @staticmethod
    def _by_saves(card: dict) -> tuple:
        return (card.get('real_sv') or 0, card.get('points') or 0)

    # ------------------------------------------------------------------
    # COMPOSITION
    # ------------------------------------------------------------------

    def _assign_lineup(self, hitters: list[dict]) -> dict[str, dict]:
        """Assign the 9 lineup positions to the eligible hitters with the most games played.

        Fills the scarcest positions first (mirrors autofill) so a player who is the
        only option at a position isn't consumed by a deeper one. DH is always last
        since every hitter qualifies.
        """
        eligible = {pos: [c for c in hitters if _pos_matches(c, pos)] for pos in OFFENSE_POSITIONS}
        assignment: dict[str, dict] = {}
        used_ids: set[str] = set()
        for position in sorted(OFFENSE_POSITIONS, key=lambda p: len(eligible[p])):
            candidates = [c for c in eligible[position] if c['card_id'] not in used_ids]
            if not candidates:
                continue
            picked = max(candidates, key=self._by_games_played)
            assignment[position] = picked
            used_ids.add(picked['card_id'])
        return assignment

    def build(self) -> Team:
        hitters = [c for c in self.cards if not c.get('is_pitcher')]
        pitchers = [c for c in self.cards if c.get('is_pitcher')]
        starters = [c for c in pitchers if 'STARTER' in (c.get('positions_list') or [])]
        relievers = [c for c in pitchers if 'STARTER' not in (c.get('positions_list') or [])]

        roster_slots: list[TeamRosterSlot] = []
        lineup_slots: list[LineupSlot] = []
        rotation: list[PitcherAssignment] = []

        # LINEUP: one hitter per field position, batting order by points
        lineup_assignment = self._assign_lineup(hitters)
        lineup_cards_by_points = sorted(lineup_assignment.items(), key=lambda kv: kv[1].get('points') or 0, reverse=True)
        batting_orders = {card['card_id']: order for order, (_, card) in enumerate(lineup_cards_by_points, start=1)}
        for position in OFFENSE_POSITIONS:
            card = lineup_assignment.get(position)
            if card is None:
                continue
            src = _card_source(card)
            roster_slots.append(TeamRosterSlot(
                card_id=card['card_id'], card_source=src, roster_position=position,
                pick_source=PickSource.IMPORTED,
            ))
            lineup_slots.append(LineupSlot(
                card_id=card['card_id'], card_source=src,
                field_position=position, batting_order=batting_orders[card['card_id']],
            ))

        # BENCH: remaining hitters by games played
        lineup_ids = {c['card_id'] for c in lineup_assignment.values()}
        bench = sorted([c for c in hitters if c['card_id'] not in lineup_ids], key=self._by_games_played, reverse=True)
        for card in bench:
            roster_slots.append(TeamRosterSlot(
                card_id=card['card_id'], card_source=_card_source(card), roster_position='BE',
                pick_source=PickSource.IMPORTED,
            ))

        # ROTATION: starters by games started -> SP1..SPn, sized to however many the
        # pool actually has (capped by the number of role slots the UI supports)
        rotation_cards = sorted(starters, key=self._by_games_started, reverse=True)[:self.MAX_ROTATION_SLOTS]
        for i, card in enumerate(rotation_cards, start=1):
            role = f'SP{i}'
            src = _card_source(card)
            roster_slots.append(TeamRosterSlot(
                card_id=card['card_id'], card_source=src, roster_position=role,
                pick_source=PickSource.IMPORTED,
            ))
            rotation.append(PitcherAssignment(card_id=card['card_id'], card_source=src, role=role))

        # BULLPEN: reliever with the most saves closes, the rest by appearances
        bullpen_pool = relievers + [c for c in starters if c not in rotation_cards]
        closer = max(bullpen_pool, key=self._by_saves) if bullpen_pool else None
        bullpen = [closer] if closer else []
        bullpen += sorted([c for c in bullpen_pool if c is not closer], key=self._by_games_played, reverse=True)
        for card in bullpen:
            role = 'CL' if card is closer else 'RP'
            src = _card_source(card)
            roster_slots.append(TeamRosterSlot(
                card_id=card['card_id'], card_source=src, roster_position=role,
                pick_source=PickSource.IMPORTED,
            ))
            rotation.append(PitcherAssignment(card_id=card['card_id'], card_source=src, role=role))

        num_bench = len(bench)
        num_bullpen = len(bullpen)
        team_kwargs = {}
        if self.primary_color:
            team_kwargs['primary_color'] = self.primary_color
        if self.secondary_color:
            team_kwargs['secondary_color'] = self.secondary_color

        return Team(
            team_id=self.team_id,
            user_id=None,
            name=self.name,
            abbreviation=self.abbreviation,
            is_public=True,
            source=TeamSource.MLB,
            pts_limit=None,
            roster_size=len(roster_slots),
            min_bench=num_bench,
            min_bullpen=num_bullpen,
            num_starters=len(rotation_cards),
            roster=roster_slots,
            lineups=[Lineup(name='Starting Lineup', slots=lineup_slots)],
            rotation=rotation,
            **team_kwargs,
        )

    def build_api_dict(self) -> dict:
        """Serialize the composed team to the same shape as the /user/teams endpoints."""
        team = self.build()
        data = team.model_dump(mode='json')
        total_points = sum(card.get('points') or 0 for card in self.cards)
        data['total_points'] = total_points
        return data
