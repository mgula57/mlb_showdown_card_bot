"""Turns a resolved plate appearance into a sentence in the MLB Stats API's voice.

The real feed reads like "Freddy Fermin singles on a line drive to center fielder Daulton Varsho.
Gavin Sheets to 2nd." The sim models neither batted-ball type nor fielders, so it stops at what it
actually knows - the outcome and where every runner ended up - and says only that: "Freddy Fermin
singles. Gavin Sheets to 2nd." Nothing here invents detail the simulation didn't produce.

Kept out of `plate_appearance.py` on purpose: this is presentation, and it is the only thing in the
engine that cares how a result should be worded.
"""

from .result import Result

# THE MLB FEED NAMES BASES THIS WAY IN ITS DESCRIPTIONS ("Gavin Sheets to 2nd", "Judge scores").
_BASE_NAMES = {1: "1st", 2: "2nd", 3: "3rd", 4: "home"}

# PRESENT-TENSE VERB PER CHART RESULT, MATCHING THE FEED'S PHRASING.
_VERBS = {
    Result.SINGLE: "singles",
    Result.SINGLE_PLUS: "singles",
    Result.DOUBLE: "doubles",
    Result.TRIPLE: "triples",
    Result.HOMERUN: "homers",
    Result.BB: "walks",
    Result.SO: "strikes out",
    Result.GB: "grounds out",
    Result.FB: "flies out",
    Result.PU: "pops out",
}

# SHORT BADGE LABEL PER RESULT - THE `event` FIELD, MIRRORING MLB'S `result.event`.
_EVENTS = {
    Result.SINGLE: "Single",
    Result.SINGLE_PLUS: "Single",
    Result.DOUBLE: "Double",
    Result.TRIPLE: "Triple",
    Result.HOMERUN: "Home Run",
    Result.BB: "Walk",
    Result.SO: "Strikeout",
    Result.GB: "Groundout",
    Result.FB: "Flyout",
    Result.PU: "Pop Out",
}


def base_name(base: int) -> str:
    return _BASE_NAMES.get(base, str(base))


class PlateAppearanceNarrator:
    """Reads a finished `PlateAppearance` and produces its `event` and `description`.

    Must be constructed *after* every step of the plate appearance has run (steal, pitch, swing,
    double play, advance) - it works by diffing the base state the swing started from against
    where everyone ended up.
    """

    def __init__(self, plate_appearance) -> None:
        self.pa = plate_appearance

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    @property
    def event(self) -> str:
        """Short label for the result badge, e.g. "Single", "Grounded Into DP"."""
        pa = self.pa
        if pa.swing.is_empty():
            # THE HALF-INNING ENDED ON THE BASEPATHS - THERE WAS NO SWING TO LABEL.
            return "Caught Stealing" if self._caught_stealing else "Stolen Base" if pa.steal_attempts else ""
        if self._grounded_into_double_play:
            return "Grounded Into DP"
        if self._fielders_choice:
            return "Fielders Choice"
        return _EVENTS.get(pa.swing.result, pa.swing.result.value.upper())

    @property
    def description(self) -> str:
        """The full sentence, in the order the events actually happened."""
        parts = self._steal_sentences()
        if not self.pa.swing.is_empty():
            parts.append(self._batter_sentence())
            parts.extend(self._runner_sentences())
        return " ".join(part for part in parts if part)

    # ------------------------------------------------------------------
    # RESULT SHAPE
    # ------------------------------------------------------------------

    @property
    def _grounded_into_double_play(self) -> bool:
        return self.pa.double_play_roll is not None and self.pa.double_play_roll.result == Result.OUT

    @property
    def _fielders_choice(self) -> bool:
        """A ground ball with a runner forced at second who beat the relay: the lead runner is
        erased and the batter reaches, which is what the engine models when the DP roll is safe."""
        return self.pa.double_play_roll is not None and self.pa.double_play_roll.result == Result.SAFE

    @property
    def _caught_stealing(self) -> bool:
        return any(attempt.result == Result.OUT for attempt in self.pa.steal_attempts)

    # ------------------------------------------------------------------
    # SENTENCES
    # ------------------------------------------------------------------

    def _steal_sentences(self) -> list[str]:
        """Steals happen before the pitch, so they lead the description."""
        sentences = []
        for attempt in self.pa.steal_attempts:
            runner = attempt.runner
            target = base_name(attempt.base + 1)
            if attempt.result == Result.SAFE:
                sentences.append(f"{runner.name} steals {target}.")
            else:
                sentences.append(f"{runner.name} caught stealing {target}.")
        return sentences

    def _batter_sentence(self) -> str:
        pa = self.pa
        name = pa.hitter.name
        if self._grounded_into_double_play:
            return f"{name} grounds into a double play."
        if self._fielders_choice:
            return f"{name} grounds into a fielder's choice."
        verb = _VERBS.get(pa.swing.result)
        if verb is None:
            return f"{name} {pa.swing.result.value}."
        return f"{name} {verb}."

    def _runner_sentences(self) -> list[str]:
        """Where everyone who was already on base ended up.

        Diffs the bases as the ball was put in play against the final state. The batter is skipped
        throughout - their own outcome is the sentence above, and on a home run they appear in
        `runners_scored` as well.
        """

        pa = self.pa
        hitter_id = pa.hitter.id
        scored_ids = {runner.id for runner in pa.runners_scored if runner.id != hitter_id}
        final_bases = {runner.id: runner.base for runner in pa.runners.runners}
        thrown_out = {
            attempt.runner.id: attempt.base
            for attempt in pa.advance_attempts if attempt.result == Result.OUT
        }

        sentences = []
        for runner_id, name, base in pa.runners_before_swing:
            if runner_id == hitter_id:
                continue
            if runner_id in scored_ids:
                sentences.append(f"{name} scores.")
            elif runner_id in thrown_out:
                sentences.append(f"{name} out at {base_name(thrown_out[runner_id] + 1)}.")
            elif runner_id in final_bases:
                if final_bases[runner_id] > base:
                    sentences.append(f"{name} to {base_name(final_bases[runner_id])}.")
            elif not (self._grounded_into_double_play or self._fielders_choice):
                # OFF THE BASES WITH NO PLAY OF THEIR OWN TO EXPLAIN IT: FORCED. WHEN THE BATTER
                # GROUNDED INTO A DP OR A FIELDER'S CHOICE THAT SENTENCE ALREADY COVERS IT.
                sentences.append(f"{name} out at {base_name(base + 1)}.")
        return sentences
