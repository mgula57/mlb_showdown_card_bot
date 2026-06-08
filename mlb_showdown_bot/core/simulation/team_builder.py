from __future__ import annotations

from ..card.card_generation import generate_card
from ..card.sets import Era, Set
from ..card.showdown_player_card import ShowdownPlayerCard
from ..mlb_stats_api import RosterTypeEnum, TeamsClient
from ..shared.player_position import PlayerSubType, PlayerType
from .team import ShowdownTeam


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

    # Fetch team metadata
    team_info = client.get_team(team_id=team_id)
    team_name = team_info.name if team_info else f"Team {team_id}"
    team_abbrev = team_info.abbreviation if team_info else str(team_id)

    # Fetch active roster
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

    # Separate and sort
    pitchers = [c for c in cards if c.player_type == PlayerType.PITCHER]
    position_players = [c for c in cards if c.player_type == PlayerType.HITTER]

    # Starters before relievers within rotation
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
