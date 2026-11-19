from typing import Optional

from ..card.sets import Set
from ..card.showdown_player_card import ShowdownPlayerCard
from ..offseason.upcoming_rosters import RosterEntry
from ..shared.player_position import ADJACENT_DEFENSE_PENALTY, PlayerSubType, PlayerType, Position, PositionSlot
from .roster import Roster


class RosterGapFiller:
    """Patches a pre-Opening Day club's card pool so the sim can field a whole team.

    Offseason rosters have holes: an unsigned free agent can leave a position nobody on the 40-man
    plays, and rookies have no card yet. Two fixes, in order:

      1. Adjacent positions. A player at a neighboring position covers the hole (a corner
         outfielder in center, a shortstop at third), one point of defense worse than his own.
      2. Replacement level. A real 40-man player with no card gets a replacement-level card at
         the position. Used for what adjacency can't cover (catcher) and for rotation, bullpen and
         bench spots the carded players can't fill.

    Positions are walked in `Roster.select`'s order with its picks (hitters at the PA floor first,
    then by points), so a hole filled here is a hole that selection would otherwise have left.
    Only a real catcher gets a replacement catcher card; any other slot falls back to any hitter.
    """

    DEFENSIVE_SLOTS = [PositionSlot.CA, PositionSlot._1B, PositionSlot._2B, PositionSlot._3B, PositionSlot.SS, PositionSlot.LF, PositionSlot.CF, PositionSlot.RF]

    # MLB roster position abbreviations that fit each slot, best first, for picking which uncarded
    # player gets a replacement card.
    _MLB_POSITIONS_FOR_SLOT: dict[PositionSlot, list[str]] = {
        PositionSlot.CA: ['C'],
        PositionSlot._1B: ['1B', '3B', 'LF', 'RF'],
        PositionSlot._2B: ['2B', 'SS', '3B', 'IF'],
        PositionSlot._3B: ['3B', 'SS', '2B', 'IF'],
        PositionSlot.SS: ['SS', '2B', '3B', 'IF'],
        PositionSlot.LF: ['LF', 'RF', 'OF', 'CF'],
        PositionSlot.CF: ['CF', 'OF', 'LF', 'RF'],
        PositionSlot.RF: ['RF', 'LF', 'OF', 'CF'],
    }

    def __init__(self, card_year: int, set: Set, uncarded: list[RosterEntry], min_pa: int = 100):
        self.card_year = card_year
        self.set = set
        self.min_pa = min_pa  # the sim's `min_pa`, so hitters are ordered the way `Roster.select` orders them
        # Consumed as replacement cards are handed out, so nobody gets two.
        self.uncarded = list(uncarded)
        self.notes: list[str] = []

    def fill(self, cards: list[ShowdownPlayerCard]) -> list[ShowdownPlayerCard]:
        """The pool with every gap it could close closed. Each fix is described in `notes`."""
        cards = list(cards)
        self._fill_positions(cards)
        self._fill_counts(cards)
        return cards

    # ------------------------------------------------------------------
    # POSITIONS
    # ------------------------------------------------------------------

    def _fill_positions(self, cards: list[ShowdownPlayerCard]) -> None:
        selected: set[str] = set()
        for index, slot in enumerate(self.DEFENSIVE_SLOTS):
            hitters = self._hitters(cards)
            eligible = [c for c in hitters if c.id not in selected and self._plays(c, slot)]
            if eligible:
                selected.add(eligible[0].id)
                continue
            covered = self._cover_with_adjacent(cards, slot, selected, later_slots=self.DEFENSIVE_SLOTS[index + 1:])
            if covered is None:
                covered = self._add_replacement(cards, PlayerType.HITTER, slot.card_position, self._MLB_POSITIONS_FOR_SLOT[slot], label=slot.value,
                                                require_preferred=slot == PositionSlot.CA)
            if covered is not None:
                selected.add(covered.id)

        # The backup catcher has to be someone the walk above didn't already place - a catcher
        # starting at 1B doesn't count.
        has_backup = any(c.id not in selected and self._plays(c, PositionSlot.CA) for c in self._hitters(cards))
        if not has_backup:
            self._add_replacement(cards, PlayerType.HITTER, Position.CA, ['C'], label='backup C', require_preferred=True)

    def _cover_with_adjacent(self, cards: list[ShowdownPlayerCard], slot: PositionSlot, selected: set[str], later_slots: list[PositionSlot]) -> Optional[ShowdownPlayerCard]:
        """Give the best unselected neighbor `slot`'s position, replacing his card in `cards`.

        Prefers a player who isn't the only option at a slot still to be filled, so covering this
        hole doesn't open the next one.
        """
        hitters = [c for c in self._hitters(cards) if c.id not in selected]
        candidates = [(c, self._adjacent_defense(c, slot)) for c in hitters]
        candidates = [(c, defense) for c, defense in candidates if defense is not None]
        if not candidates:
            return None

        def is_only_option_later(card: ShowdownPlayerCard) -> bool:
            for later in later_slots:
                eligible = [c for c in hitters if self._plays(c, later)]
                if len(eligible) == 1 and eligible[0].id == card.id:
                    return True
            return False

        card, source_defense = min(candidates, key=lambda pair: (is_only_option_later(pair[0]), -pair[0].points))
        position = slot.card_position
        defense = max(source_defense - ADJACENT_DEFENSE_PENALTY, 0)
        covering = card.model_copy(update={
            'positions_and_defense': {**card.positions_and_defense, position: defense},
            'positions_list': [*card.positions_list, position],
        })
        cards[cards.index(card)] = covering
        self.notes.append(f"{slot.value}: {card.name} covers from {', '.join(p.value for p in card.positions_list)} ({defense:+d} defense)")
        return covering

    @staticmethod
    def _adjacent_defense(card: ShowdownPlayerCard, slot: PositionSlot) -> Optional[int]:
        """The card's defense at its best neighboring position for `slot`, or None if it has none."""
        for position in slot.adjacent_positions:
            if position in card.positions_and_defense:
                return card.positions_and_defense[position]
        return None

    # ------------------------------------------------------------------
    # COUNTS
    # ------------------------------------------------------------------

    def _fill_counts(self, cards: list[ShowdownPlayerCard]) -> None:
        targets = [
            (PlayerSubType.STARTING_PITCHER, Roster.ACTIVE_ROTATION, PlayerType.PITCHER, Position.SP, 'SP'),
            (PlayerSubType.RELIEF_PITCHER, Roster.ACTIVE_BULLPEN, PlayerType.PITCHER, Position.RP, 'RP'),
            (PlayerSubType.POSITION_PLAYER, Roster.ACTIVE_POSITION_PLAYERS, PlayerType.HITTER, None, 'bench'),
        ]
        for sub_type, needed, player_type, position, label in targets:
            while sum(1 for c in cards if c.player_sub_type == sub_type) < needed:
                if self._add_replacement(cards, player_type, position, preferred_mlb_positions=[], label=label) is None:
                    break

    # ------------------------------------------------------------------
    # REPLACEMENT CARDS
    # ------------------------------------------------------------------

    def _add_replacement(self, cards: list[ShowdownPlayerCard], player_type: PlayerType, position: Optional[Position],
                         preferred_mlb_positions: list[str], label: str, require_preferred: bool = False) -> Optional[ShowdownPlayerCard]:
        entry = self._take_uncarded(player_type, preferred_mlb_positions, require_preferred=require_preferred)
        if entry is None:
            return None
        if position is None:
            # An extra bench bat plays his own listed position.
            try:
                position = Position(entry.position) if entry.position else None
            except ValueError:
                position = None
        card = ShowdownPlayerCard.replacement_level(
            name=entry.name, year=self.card_year, set=self.set, player_type=player_type, position=position, mlb_id=entry.mlb_id,
        )
        cards.append(card)
        self.notes.append(f"{label}: replacement-level card for {entry.name} ({entry.position or '?'}, no {self.card_year} card)")
        return card

    def _take_uncarded(self, player_type: PlayerType, preferred_mlb_positions: list[str], require_preferred: bool = False) -> Optional[RosterEntry]:
        pool = [e for e in self.uncarded if e.is_pitcher == (player_type == PlayerType.PITCHER) and e.position != 'TWP']
        if require_preferred:
            pool = [e for e in pool if e.position in preferred_mlb_positions]
        if not pool:
            return None
        ranked = sorted(pool, key=lambda e: preferred_mlb_positions.index(e.position) if e.position in preferred_mlb_positions else len(preferred_mlb_positions))
        entry = ranked[0]
        self.uncarded.remove(entry)
        return entry

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _hitters(self, cards: list[ShowdownPlayerCard]) -> list[ShowdownPlayerCard]:
        """Position players in `Roster.select`'s order: at the PA floor first, then by points."""
        hitters = [c for c in cards if c.player_sub_type == PlayerSubType.POSITION_PLAYER]
        return sorted(hitters, key=lambda c: (c.stats.get('PA', 0) >= self.min_pa, c.points), reverse=True)

    @staticmethod
    def _plays(card: ShowdownPlayerCard, slot: PositionSlot) -> bool:
        return any(position in slot.valid_positions for position in card.positions_and_defense)
