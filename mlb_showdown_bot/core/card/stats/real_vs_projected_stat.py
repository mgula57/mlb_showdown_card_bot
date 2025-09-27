from pydantic import BaseModel
from typing import Optional

class RealVsProjectedStat(BaseModel):
    """Model for comparing real vs projected for a single stat"""

    stat: str
    real: int | float
    projected: Optional[float] = None
    diff: Optional[float] = None
    diff_str: Optional[str] = None
    precision: Optional[int] = None
    is_real_estimated: Optional[bool] = None
    is_projected_correction: Optional[bool] = None

    def model_post_init(self, __context):

        # CALCULATE THE DIFFERENCE STRING
        if self.diff_str is None:
            self._populate_diff_string()

    def _populate_diff_string(self) -> None:
        """Populate the diff_str attribute based on the real and projected values."""

        if self.diff is None:
            return

        if self.real == self.projected:
            self.diff_str = '0'
            return

        prefix = '+' if self.projected > self.real else ''
        diff_string = f'{round(self.projected - self.real, self.precision or 0)}'
        diff_string = diff_string.replace('.0', '') if diff_string.endswith('.0') else diff_string
        diff_string = diff_string.replace('0.', '.') if diff_string.replace('-0', '0').startswith('0.') else diff_string
        self.diff_str = f'{prefix}{diff_string}'