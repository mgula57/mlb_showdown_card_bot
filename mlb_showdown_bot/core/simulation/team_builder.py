from __future__ import annotations

from ..card.card_generation import generate_card
from ..card.sets import Era, Set
from ..card.showdown_player_card import ShowdownPlayerCard
from ..mlb_stats_api import RosterTypeEnum, TeamsClient
from ..shared.player_position import PlayerSubType, PlayerType
from .team import SavedTeam, SavedTeamSlot, ShowdownTeam


# ---------------------------------------------------------------------------
# Build from MLB Stats API (live roster)
# ---------------------------------------------------------------------------

def build_showdown_team(
    team_id: int,
    season: int,
    game_set: Set,
    era: Era,
) -> ShowdownTeam:
    """Build a ShowdownTeam from an MLB team's active roster.

    Fetches the active 26-man roster via the MLB Stats API, generates a
    ShowdownPlayerCard for each player, and assembles the result into a
    ShowdownTeam. Cards that fail to generate are silently skipped.

    Args:
        team_id: MLB Stats API team ID (e.g. 147 = Yankees).
        season: Season year to build cards from.
        game_set: Set used for card generation (e.g. Set.EXPANDED).
        era: Era used for stat adjustments (e.g. Era.PITCH_CLOCK).

    Returns:
        ShowdownTeam with roster, batting_order, and rotation populated.
    """
    client = TeamsClient()

    team_info = client.get_team(team_id=team_id)
    team_name = team_info.name if team_info else f"Team {team_id}"
    team_abbrev = team_info.abbreviation if team_info else str(team_id)

    roster = client.get_team_roster(team_id=team_id, season=str(season), roster_type=RosterTypeEnum.ACTIVE)

    cards: list[ShowdownPlayerCard] = []
    for slot in roster.roster:
        player_id = slot.person.id
        try:
            result = generate_card(
                player_id=player_id,
                year=str(season),
                set=game_set.value,
                era=era.value,
                datasource='MLB_API',
                store_in_logs=False,
            )
        except Exception:
            continue
        if result.get('error'):
            continue
        raw_card = result.get('card')
        if not raw_card:
            continue
        try:
            card = ShowdownPlayerCard.model_validate(raw_card)
        except Exception:
            continue
        cards.append(card)

    pitchers = [c for c in cards if c.player_type == PlayerType.PITCHER]
    position_players = [c for c in cards if c.player_type == PlayerType.HITTER]

    rotation = sorted(
        pitchers,
        key=lambda c: 0 if c.player_sub_type == PlayerSubType.STARTING_PITCHER else 1,
    )

    return ShowdownTeam(
        name=team_name,
        team_id=team_id,
        abbreviation=team_abbrev,
        season=season,
        roster=cards,
        batting_order=position_players,
        rotation=rotation,
    )


# ---------------------------------------------------------------------------
# Build from a user's saved team (archive DB lookup)
# ---------------------------------------------------------------------------

# Canonical batting-order for the nine field positions.
# Managers choose differently; this is a reasonable default.
_BATTER_SLOT_ORDER = ['CF', 'RF', 'LF', 'DH', '1B', '3B', 'SS', 'CA', '2B']


def build_showdown_team_from_saved_team(
    saved_team: SavedTeam,
    db: object,  # PostgresDB — typed as object to avoid a hard import cycle
) -> ShowdownTeam:
    """Convert a user's saved team into a simulation-ready ShowdownTeam.

    Each filled slot's card_id (archive composite key '{year}-{bref_id}-{type}')
    is resolved to a full ShowdownPlayerCard via the archive database. Slots
    that are empty or whose cards cannot be found are silently skipped.

    Bench slots (BE*) are ignored for simulation — they are not placed into the
    batting order or rotation but are available via ShowdownTeam.roster.

    Pitching rotation order: SP1, SP2, … then RP1, RP2, …
    Batting order: CF → RF → LF → DH → 1B → 3B → SS → CA → 2B (customisable
    by rearranging the team slots before calling this function).

    Args:
        saved_team: A SavedTeam loaded from the database.
        db: An open PostgresDB instance used to fetch full card data.

    Returns:
        ShowdownTeam ready to be passed to ShowdownGame.new().
    """
    slot_map: dict[str, SavedTeamSlot] = {s.slot_key: s for s in saved_team.filled_slots}

    rotation = _load_pitcher_slots(slot_map, db)
    batting_order = _load_batter_slots(slot_map, db)

    # Bench cards go into the full roster but not into the active lineup
    bench_slots = [s for k, s in slot_map.items() if k.startswith('BE')]
    bench_cards = _fetch_cards(bench_slots, db)

    roster = rotation + batting_order + bench_cards

    return ShowdownTeam(
        name=saved_team.name,
        team_id=saved_team.id,
        abbreviation=(saved_team.metadata or {}).get('abbreviation') or saved_team.name[:3].upper(),
        season=saved_team.inferred_season,
        roster=roster,
        batting_order=batting_order,
        rotation=rotation,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _load_pitcher_slots(
    slot_map: dict[str, SavedTeamSlot],
    db: object,
) -> list[ShowdownPlayerCard]:
    sp_keys = sorted(
        [k for k in slot_map if k.startswith('SP')],
        key=lambda k: int(k[2:]) if k[2:].isdigit() else 99,
    )
    rp_keys = sorted(
        [k for k in slot_map if k.startswith('RP')],
        key=lambda k: int(k[2:]) if k[2:].isdigit() else 99,
    )
    return _fetch_cards([slot_map[k] for k in sp_keys + rp_keys], db)


def _load_batter_slots(
    slot_map: dict[str, SavedTeamSlot],
    db: object,
) -> list[ShowdownPlayerCard]:
    # Use canonical order; include any extra field slots not in the default list
    ordered_keys = _BATTER_SLOT_ORDER + [
        k for k in slot_map
        if k not in _BATTER_SLOT_ORDER and not k.startswith(('SP', 'RP', 'BE'))
    ]
    return _fetch_cards([slot_map[k] for k in ordered_keys if k in slot_map], db)


def _fetch_cards(
    slots: list[SavedTeamSlot],
    db: object,
) -> list[ShowdownPlayerCard]:
    cards: list[ShowdownPlayerCard] = []
    for slot in slots:
        if not slot.card_id:
            continue
        try:
            card = db.fetch_single_card(slot.card_id)
        except Exception:
            continue
        if card is not None:
            cards.append(card)
    return cards
