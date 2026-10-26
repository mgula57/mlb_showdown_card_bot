from pydantic import BaseModel
from typing import ClassVar

# INTERNAL
from ..shared.speed import Speed


class VariableSpeedVariant(BaseModel):
    """Variable speed version of a standard speed 2000/2001 hitter: uncapped speed instead of 10/15/20.

    Stored on the card (`ShowdownPlayerCard.variable_speed_variant`) when it's built, so archived cards
    can be searched and sorted either way without a rebuild. Speed and points are the only fields that
    differ between the two versions. The points breakdown isn't stored: it's cheap to recompute with
    `ShowdownPlayerCard.apply_variable_speed_00_01` when a card is shown.
    """

    speed: Speed
    points: int

    # KEY ON A SERIALIZED CARD (`card_data`) THAT HOLDS THE VARIANT
    CARD_DATA_KEY: ClassVar[str] = 'variable_speed_variant'
