"""Normalize the vertical metrics of the web display fonts so capitals sit centered in their line box.

The bundled Helvetica Neue condensed faces ship with uneven ascent/descent, so uppercase text renders
high inside plates, badges and the command art unless every call site nudges it. Rewriting the
metrics once at the font level fixes every use in every browser: the line box becomes symmetric
around the cap height (half the leftover space above the caps, half below the baseline).

Idempotent; rerun after adding or replacing a display font:

    uv run --with fonttools python frontend/scripts/normalize_font_metrics.py
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

FONTS_DIR = Path(__file__).resolve().parent.parent / "src" / "assets" / "fonts"
FONTS = [
    "HelveticaNeueBoldCondensed.ttf",
    "HelveticaNeueExtraBlackCondensed.otf",
    "HelveticaNeueCondensedHeavyOblique.otf",
]

# Total line box, in em. Roomy enough for accents and descenders; with `leading-none` the browser
# trims the excess evenly from both sides, which keeps the caps centered.
LINE_BOX_EM = 1.2
USE_TYPO_METRICS = 1 << 7  # only defined for OS/2 v4+; unneeded when all three metric sets match


class FontMetricsNormalizer:
    def __init__(self, path: Path):
        self.path = path
        self.font = TTFont(path)
        self.units_per_em = self.font["head"].unitsPerEm

    def cap_height(self) -> int:
        glyph_set = self.font.getGlyphSet()
        pen = BoundsPen(glyph_set)
        glyph_set[self.font.getBestCmap()[ord("H")]].draw(pen)
        return round(pen.bounds[3])

    def normalize(self) -> None:
        cap = self.cap_height()
        line_box = round(LINE_BOX_EM * self.units_per_em)
        descent = (line_box - cap) // 2
        ascent = line_box - descent

        hhea, os2 = self.font["hhea"], self.font["OS/2"]
        hhea.ascent, hhea.descent, hhea.lineGap = ascent, -descent, 0
        os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ascent, -descent, 0
        # hhea, typo and win metrics are set identically, so every platform lays out the same box.
        os2.usWinAscent, os2.usWinDescent = ascent, descent
        if os2.version >= 4:
            os2.fsSelection |= USE_TYPO_METRICS
        else:
            os2.fsSelection &= ~USE_TYPO_METRICS

        self.font.save(self.path)
        print(f"{self.path.name}: cap {cap}, ascent {ascent}, descent {descent} (upm {self.units_per_em})")


if __name__ == "__main__":
    for name in FONTS:
        FontMetricsNormalizer(FONTS_DIR / name).normalize()
