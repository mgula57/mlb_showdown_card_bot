import random
import string
from typing import Callable


class JoinCode:
    """Short codes people read aloud or type by hand to join a sim lobby or a league."""

    # EXCLUDES VISUALLY AMBIGUOUS CHARACTERS (0/O, 1/I) SINCE A JOIN CODE IS READ ALOUD/TYPED BY HAND.
    ALPHABET = ''.join(c for c in string.ascii_uppercase + string.digits if c not in 'O0I1')
    LENGTH = 6

    @classmethod
    def generate(cls, is_taken: Callable[[str], bool], attempts: int = 5) -> str | None:
        """A code `is_taken` says is free, or None if every attempt collided - astronomically
        unlikely at ~30^6 combinations, so callers treat it as a circuit breaker, not a real path."""
        for _ in range(attempts):
            code = ''.join(random.choices(cls.ALPHABET, k=cls.LENGTH))
            if not is_taken(code):
                return code
        return None

    @staticmethod
    def normalize(code: str) -> str:
        return code.strip().upper()
