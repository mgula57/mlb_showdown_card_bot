import re

from better_profanity import profanity
from unidecode import unidecode


class ProfanityFilter:
    """Checks user-submitted free text (team names, comments, etc.) against a
    profanity word list.

    `better_profanity`'s word list is a module-level singleton loaded from disk, so this
    class exists to load it exactly once and give call sites a single, testable surface
    rather than reaching into the third-party module directly.

    The stock list flags 66 real players' names (Dick Allen, Whitey Ford, Shota Imanaga...),
    found by running every `card_bot` name through it. Re-run that check if the list or the
    library changes.
    """

    # Flagged words that are players' names and harmless on their own, so they're allowed anywhere
    # ("Dick's '72 card"): Dick Allen, Len Barker, Willy Adames, Woody Williams, Chien-Ming Wang,
    # AJ Pollock, Shota Imanaga, Kim Seaman, Gaylord Perry
    _ALLOWED_WORDS = ('dick', 'len', 'willy', 'woody', 'wang', 'pollock', 'shota', 'seaman', 'gaylord')

    # Players whose name includes a word that's also a slur. Allowed only as the full name, so the
    # slur on its own is still caught. Matched without accents (Kiké Hernández)
    _ALLOWED_NAMES = ('kike hernandez', 'guido grilli', 'whitey ford', 'whitey herzog')
    _ALLOWED_NAMES_PATTERN = re.compile(r'\b(?:' + '|'.join(re.escape(n) for n in _ALLOWED_NAMES) + r')\b', re.IGNORECASE)

    _loaded = False

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._loaded:
            profanity.load_censor_words(whitelist_words=list(cls._ALLOWED_WORDS))
            cls._loaded = True

    @classmethod
    def contains_profanity(cls, text: str | None) -> bool:
        if not text:
            return False
        cls._ensure_loaded()
        return profanity.contains_profanity(cls._ALLOWED_NAMES_PATTERN.sub(' ', unidecode(text)))
