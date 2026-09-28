from better_profanity import profanity


class ProfanityFilter:
    """Checks user-submitted free text (team names, abbreviations, etc.) against a
    profanity word list.

    `better_profanity`'s word list is a module-level singleton loaded from disk, so this
    class exists to load it exactly once and give call sites a single, testable surface
    rather than reaching into the third-party module directly.
    """

    _loaded = False

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._loaded:
            profanity.load_censor_words()
            cls._loaded = True

    @classmethod
    def contains_profanity(cls, text: str | None) -> bool:
        if not text:
            return False
        cls._ensure_loaded()
        return profanity.contains_profanity(text)
