from pydantic import BaseModel
from typing import ClassVar

# INTERNAL
from ..shared.speed import Speed
from .points import Points


class VariableSpeedVariant(BaseModel):
    """Variable speed version of a standard speed 2000/2001 hitter: uncapped speed instead of 10/15/20.

    Stored on the card (`ShowdownPlayerCard.variable_speed_variant`) when it's built, so archived cards
    can be searched, sorted and shown either way without a rebuild. Speed and points are the only
    fields that differ between the two versions.
    """

    speed: Speed
    points: int
    points_breakdown: Points

    # KEY ON A SERIALIZED CARD (`card_data`) THAT HOLDS THE VARIANT
    CARD_DATA_KEY: ClassVar[str] = 'variable_speed_variant'

    @classmethod
    def card_data_as_variable_speed(cls, card_data: dict) -> dict:
        """A serialized card as its variable speed version. Returned unchanged when it has no variant
        (pitchers, sets other than 2000/2001, cards that already use variable speed).

        Args:
          card_data: Serialized standard speed card (`ShowdownPlayerCard.as_json()`).

        Returns:
          Serialized card with the variant's speed and points applied.
        """
        variant = (card_data or {}).get(cls.CARD_DATA_KEY)
        if not variant:
            return card_data
        variable_card_data = {key: value for key, value in card_data.items() if key != cls.CARD_DATA_KEY}
        variable_card_data.update(variant, is_variable_speed_00_01=True)
        return variable_card_data
