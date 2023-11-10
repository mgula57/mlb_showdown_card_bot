
class ValueRange:

    def __init__(self, min:float, max:float) -> None:
        self.min: float = min
        self.max: float = max

    @property
    def range(self) -> int:
        return self.max - self.min
    
    def percentile(self, value:float, is_desc:bool=False, allow_negative:bool=False) -> float:
        """Get the percentile for a particular value.

        Args:
          value: Value to get percentile of.
          is_desc: Boolean for whether the lowest value should be treated as positive.
          allow_negative: Boolean flag for whether to allow percentile to be < 0
        
        Returns:
          Percentile for the value provided.
        """

        range = self.max - self.min
        value_within_range = value - self.min

        if not allow_negative and value_within_range < 0 and not is_desc:
            value_within_range = 0

        raw_percentile = value_within_range / range

        # REVERSE IF DESC
        percentile_adjusted = 1 - raw_percentile if is_desc else raw_percentile

        if not allow_negative and percentile_adjusted < 0:
            percentile_adjusted = 0

        return percentile_adjusted