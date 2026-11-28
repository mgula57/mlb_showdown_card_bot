"""Two-way card images: one card showing a player's hitting AND pitching sides.

The hitting card owns the image and carries the pitching card in `two_way`. Each layout reuses
both cards' own render helpers (templates, metadata, chart, player images) and rearranges them:

- 2000/2001: a SPLIT card. The hitter (command, chart, photo) fills the top-left half and the
  pitcher the bottom-right, divided by a steep diagonal banner bar holding the name and total
  points. 2000 shares the 2001 layout over its plainer (no line art) team background.
- 2002: the photos split side by side under the native frame, and both native command boxes sit side by
  side along the bottom (pitcher in its native spot, hitter left of it) over a strip with the set/year box,
  bot logo and legal text. The name column ends on the pitcher box, with the two-way total above the name.
- 2003: like 2002, both native command boxes side by side along the bottom (raised and cut under their last
  result row, since they run off the card), with the year box, bot logo and legal text in a strip under them.
  The name keeps the top of the name column, with the two-way total level under it, above the logos.
- 2004/2005: the photos split side by side, and the bottom bands become one name band plus a
  self-contained block per side (command badge | metadata / ranges / results).

All coordinates are in the bordered canvas space (1644x2244, 72px bleed). Cards are always
composed bordered and cropped to the regular card size afterwards when the card isn't bordered.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from functools import cached_property
from itertools import zip_longest
from typing import TYPE_CHECKING, Iterator, NamedTuple, Optional

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from .images import ImageColoring, ImageParallel, ParallelColoring, PlayerImageComponent, PlayerImageLayer
from .sets import Set, TemplateImageComponent
from .utils import colors

if TYPE_CHECKING:
    from .showdown_player_card import ShowdownPlayerCard


class PlayerImageGroups(NamedTuple):
    """A side's player image layers in paste order, grouped by whether they follow the photo or stay with the card."""
    photo_background: list[PlayerImageLayer]    # THE PHOTO'S OWN BACKGROUND (MOVES WITH THE PHOTO)
    art_under: list[PlayerImageLayer]           # CARD ART UNDER THE PLAYER (STAYS PUT)
    photo: list[PlayerImageLayer]               # THE PLAYER CUTOUT LAYERS (MOVE)
    art_over: list[PlayerImageLayer]            # CARD ART OVER THE PLAYER, EX: ASG FOREGROUNDS (STAYS PUT)


class TwoWayCardImage:
    """Renders the image for a two-way card, choosing the layout for the card's set."""

    SUPPORTED_SETS: frozenset[Set] = frozenset([Set._2000, Set._2001, Set._2002, Set._2003, Set._2004, Set._2005])
    # BUILT AROUND ONE FRAMED PHOTO WINDOW, WHICH THE 00/01 SPLIT CARD DOESN'T HAVE
    UNSUPPORTED_PARALLELS_00_01: frozenset[ImageParallel] = frozenset([ImageParallel.BREAKOUT, ImageParallel.BOOSTER])

    def __init__(self, hitter: ShowdownPlayerCard, pitcher: ShowdownPlayerCard) -> None:
        self.hitter = hitter
        self.pitcher = pitcher

    @classmethod
    def supports(cls, set: Set) -> bool:
        """True when the set has a two-way layout."""
        return set in cls.SUPPORTED_SETS

    @classmethod
    def supports_parallel(cls, set: Set, parallel: ImageParallel) -> bool:
        """True when the set's two-way layout can show the parallel."""
        return not (set.is_00_01 and parallel in cls.UNSUPPORTED_PARALLELS_00_01)

    def render(self) -> Image.Image:
        """Compose the two-way card.

        Returns:
          Card image at the hitter card's canvas size (bordered or regular), ready for final crop.
        """
        is_bordered = self.hitter.image.is_bordered
        with self._render_context():
            card_image = self.layout_class(hitter=self.hitter, pitcher=self.pitcher, is_bordered=is_bordered).render()

        if is_bordered:
            return card_image
        padding = self.hitter.set.card_border_padding
        width, height = card_image.size
        return card_image.crop((padding, padding, width - padding, height - padding))

    @property
    def layout_class(self) -> type[TwoWayLayout]:
        """The two-way layout for the card's set."""
        if self.hitter.set.is_00_01:
            return SplitLayout0001
        if self.hitter.set == Set._2002:
            return BlockLayout02
        if self.hitter.set == Set._2003:
            return BlockLayout03
        return BlockLayout0405

    @contextmanager
    def _render_context(self) -> Iterator[None]:
        """Temporary settings while composing, restored after:
        - both sides render in the bordered canvas space and prefer two-way tagged auto images.
        - the hitter's accolades (drawn on the Super Season logo) alternate with the pitcher's.
        - side-by-side layouts (02, 04/05) also load both sides' plain cutouts, drawn whole over the blended backgrounds.
        - layouts with a PHOTO_FRAMING_SET crop both photos like that set's cards (2002 uses the wider 04/05 framing).
        - a multi-colored team colored parallel (ex: Team Color Blast) splits by side: the hitter's art in
          the primary color, the pitcher's in the secondary. Single color settings apply to both sides.
        """
        overrides: list[tuple[object, str, object]] = []
        for card in (self.hitter, self.pitcher):
            overrides += [(card.image, 'is_bordered', True), (card, '_is_rendering_two_way', True)]
        overrides.append((self.hitter, 'accolades', self.alternating_accolades))
        if self.layout_class.INCLUDES_CUTOUT:
            overrides += [(card, '_includes_cutout', True) for card in (self.hitter, self.pitcher)]  # WHOLE CUTOUTS OVER THE SEAM
        if self.layout_class.PHOTO_FRAMING_SET:
            overrides += [(card, '_photo_framing_set', self.layout_class.PHOTO_FRAMING_SET) for card in (self.hitter, self.pitcher)]
        if self.hitter.image.parallel.is_team_colored and self.hitter.image.parallel_art_coloring == ImageColoring.MULTI:
            overrides += [(self.hitter.image, 'parallel_coloring', ParallelColoring.PRIMARY), (self.pitcher.image, 'parallel_coloring', ParallelColoring.SECONDARY)]

        originals = [(target, name, getattr(target, name, None)) for target, name, _ in overrides]
        for target, name, value in overrides:
            setattr(target, name, value)
        try:
            yield
        finally:
            for target, name, value in reversed(originals):
                setattr(target, name, value)

    @property
    def alternating_accolades(self) -> list[str]:
        """Hitting and pitching accolades alternated (best of each first), shared ones (ex: ALL STAR) once."""
        sides = [self.hitter.accolades or [], self.pitcher.accolades or []]
        alternated = [accolade for pair in zip_longest(*sides) for accolade in pair if accolade is not None]
        return list(dict.fromkeys(alternated))


class TwoWayLayout:
    """Shared canvas helpers for the per-set two-way layouts."""

    INCLUDES_CUTOUT = False                     # WHETHER BOTH SIDES ALSO LOAD THEIR PLAIN CUTOUTS WHILE COMPOSING
    PHOTO_FRAMING_SET: Optional[Set] = None     # CROPS BOTH PHOTOS LIKE THIS SET'S CARDS INSTEAD OF THE CARD'S OWN SET
    OBLIQUE = 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique'

    def __init__(self, hitter: ShowdownPlayerCard, pitcher: ShowdownPlayerCard, is_bordered: bool) -> None:
        self.hitter = hitter
        self.pitcher = pitcher
        self.is_bordered = is_bordered  # THE CARD'S OWN SETTING (BOTH SIDES ARE FORCED BORDERED WHILE COMPOSING)
        self.width, self.height = hitter.set.card_size_bordered
        self.padding = hitter.set.card_border_padding

    def render(self) -> Image.Image:
        raise NotImplementedError

    # ---------- ASSETS ----------

    def template(self, name: str) -> Image.Image:
        return Image.open(self.hitter._template_img_path(name)).convert('RGBA')

    def font(self, name: str, size: int, extension: str = 'ttf') -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(self.hitter._font_path(name, extension=extension), size=size)

    # ---------- CANVAS ----------

    def blank(self) -> Image.Image:
        return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))

    def bordered_xy(self, card: ShowdownPlayerCard, xy: tuple[int, int]) -> tuple[int, int]:
        """Regular card coordinates (1500x2100 space) to the bordered canvas."""
        return card._coordinates_adjusted_for_bordering(coordinates=xy, is_forced=True)

    def layer(self, mask: Image.Image, xy: tuple[int, int], color=colors.WHITE) -> Image.Image:
        """Full canvas layer with `color` stamped through `mask` at `xy` (the cards' text-image pattern)."""
        canvas = self.blank()
        canvas.paste(color, xy, mask)
        return canvas

    def shifted(self, image: Image.Image, dx: int, dy: int) -> Image.Image:
        """`image` alpha-composited onto a blank canvas at (dx, dy); negative offsets crop it."""
        canvas = self.blank()
        source = image.convert('RGBA').crop((max(0, -dx), max(0, -dy), image.width, image.height))
        canvas.alpha_composite(source, (max(0, dx), max(0, dy)))
        return canvas

    @staticmethod
    def scaled(image: Image.Image, scale: float) -> Image.Image:
        return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)

    def scaled_about(self, layer: Image.Image, anchor: tuple[float, float], scale: float) -> Image.Image:
        """`layer`'s content scaled by `scale`, keeping the `anchor` point in place."""
        bbox = layer.getbbox()
        if scale == 1 or bbox is None:
            return layer
        anchor_x, anchor_y = anchor
        content = self.scaled(layer.crop(bbox), scale)
        x, y = round(anchor_x - (anchor_x - bbox[0]) * scale), round(anchor_y - (anchor_y - bbox[1]) * scale)
        canvas = self.blank()
        canvas.alpha_composite(content, (x, y))
        return canvas

    @contextmanager
    def secondary_colored(self, card: ShowdownPlayerCard) -> Iterator[None]:
        """Temporarily render `card` in the opposite team color (primary <-> secondary)."""
        original = card.image.coloring
        card.image.coloring = ImageColoring.PRIMARY if original == ImageColoring.SECONDARY else ImageColoring.SECONDARY
        try:
            yield
        finally:
            card.image.coloring = original

    @staticmethod
    def clipped(image: Image.Image, mask: Image.Image) -> Image.Image:
        """`image` kept only where `mask` is set."""
        return Image.composite(image, Image.new('RGBA', image.size, (0, 0, 0, 0)), mask)

    # ---------- PLAYER IMAGE LAYERS ----------

    @staticmethod
    def grouped_layers(layers: list[PlayerImageLayer]) -> PlayerImageGroups:
        """Split a side's player image layers into the photo's background, card art under the player, the
        player cutout layers, and card art over the player. Photos move and scale with their side while card
        art (parallels, edition art) stays put, so both halves line up into one finish.

        The photo background is pasted first, under the card art (ex: Gold Frame or Super Season art sits
        on the background photo and under the cutout), so it's grouped apart from the cutout."""
        photo_background = [layer for layer in layers if layer.is_photo_background]
        rest = [layer for layer in layers if not layer.is_photo_background]
        first_cutout = next((index for index, layer in enumerate(rest) if not layer.is_card_art), len(rest))
        after = rest[first_cutout:]
        return PlayerImageGroups(
            photo_background=photo_background,
            art_under=rest[:first_cutout],
            photo=[layer for layer in after if not layer.is_card_art],
            art_over=[layer for layer in after if layer.is_card_art],
        )

    @staticmethod
    def composite(layers: list[PlayerImageLayer], size: tuple[int, int]) -> Image.Image:
        """Layers alpha-composited in order onto a transparent canvas of `size`, at their own coordinates.
        (A masked paste onto transparency would square a translucent layer's alpha, ex: foil at 65%.)"""
        canvas = Image.new('RGBA', size, (0, 0, 0, 0))
        for layer in layers:
            x, y = layer.xy
            image = layer.image.convert('RGBA')
            canvas.alpha_composite(image.crop((max(0, -x), max(0, -y), image.width, image.height)), (max(0, x), max(0, y)))
        return canvas

    # ---------- STATS ROW ----------

    def stats_row(self) -> Image.Image:
        """The split/date range text and the stat highlights bar in their native spots. The bar splits
        into the hitting side's stats, a divider, then the pitching side's."""
        canvas = self.blank()
        card = self.hitter
        if card.stats_period.show_text_on_card_image:
            split_image = card._stats_period_type_text_img()
            split_xy = card.set.template_component_paste_coordinates(component=TemplateImageComponent.SPLIT, is_multi_year=card.stats_period.is_multi_year, is_full_career=card.stats_period.is_full_career)
            canvas.paste(split_image, self.bordered_xy(card, split_xy), split_image)
        if card.image.shows_stat_highlights:
            sections = [self.hitter.stat_highlights_with_ops(), self.pitcher.image.stat_highlights_list]
            stats_image, stats_xy = card._stat_highlights_image(sections=sections)
            canvas.paste(stats_image, self.bordered_xy(card, stats_xy), stats_image)
        return canvas

    # ---------- ADD-ONS ----------

    def year_and_expansion(self, offsets: Optional[dict[str, tuple[int, int]]] = None) -> Image.Image:
        """The optional year container (00/01) and expansion logo in their native spots, each moved by
        its entry in `offsets` ('year' / 'expansion') where the layout needs the room."""
        canvas = self.blank()
        offsets = offsets or {}
        for key, layer in (('year', self.hitter._year_container_layer()), ('expansion', self.hitter._expansion_layer())):
            if layer is None:
                continue
            image, xy = layer
            dx, dy = offsets.get(key, (0, 0))
            x, y = self.bordered_xy(self.hitter, xy)
            canvas.alpha_composite(self.shifted(image, x + dx, y + dy))
        return canvas

    def holiday_frame(self) -> Optional[Image.Image]:
        """The Holiday edition's frame art across the whole card, or None for other editions."""
        holiday_image = self.hitter._holiday_image()
        return self.shifted(holiday_image, self.padding, self.padding) if holiday_image else None

    @property
    def total_points_text(self) -> str:
        return f"{self.hitter.points + self.pitcher.points}"

    # ---------- TOTAL POINTS ----------

    TOTAL_LABEL_SIZE, TOTAL_POINTS_SIZE = 54, 84
    SILVER = (205, 205, 205)                    # THE TWO-WAY LABEL BESIDE WHITE POINTS

    def total_fonts(self, scale: float) -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
        return self.font(self.OBLIQUE, round(self.TOTAL_LABEL_SIZE * scale)), self.font(self.OBLIQUE, round(self.TOTAL_POINTS_SIZE * scale))

    def stacked_total(self, max_width: int, color) -> Image.Image:
        """'TWO-WAY' over '<total> PT.', centered, shrunk to fit `max_width` (for a name column wide enough to
        hold it level, ex: 2003)."""
        label, points = 'TWO-WAY', f'{self.total_points_text} PT.'
        scale = min(1.0, max_width / max(self.total_fonts(1.0)[0].getlength(label), self.total_fonts(1.0)[1].getlength(points)))
        label_font, points_font = self.total_fonts(scale)
        lines = [(label, label_font), (points, points_font)]
        heights = [font.getbbox(text, anchor='ls')[3] - font.getbbox(text, anchor='ls')[1] for text, font in lines]
        gap = round(12 * scale)
        text = Image.new('RGBA', (max_width, sum(heights) + gap + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text)
        y = 5
        for (line, font), height in zip(lines, heights):
            draw.text((max_width / 2, y - font.getbbox(line, anchor='ls')[1]), line, font=font, fill=color, anchor='ms')
            y += height + gap
        return text.crop(text.getbbox())


class SplitLayout0001(TwoWayLayout):
    """2000/2001: hitter top-left, pitcher bottom-right, split by a diagonal 2001-style banner bar."""

    UP = 150                                # hitter block rises into the removed header space
    SEAM_START, SEAM_END_Y = 1330, 820      # divider y at the left / right card edges
    CONTROL_BANNER_TOP_Y, CONTROL_L_X = 278, 1282   # 2001-Pitcher template: CONTROL banner top and the L's middle
    PITCHER_BLOCK_Y = 850                   # pitcher command block drops this far below its native spot (clears the divider)
    CHART_SCALE = 0.84
    BAR_EDGE, BAR_CENTER = 16, 90           # divider: brushed silver edge thickness (each side) and black center, from the 2000 name container
    BAR_DIVIDER = TwoWayLayout.SILVER       # tick between the name and the total, and the TWO-WAY label (silver, like the bar edges)
    TOTAL_FONT_SIZE = 50                    # reference size; the total is rescaled so its capitals match the name's height
    HITTERBOX_Y = 130
    HITTERBOX_BALL_CENTER = (261, 88)        # 2000-TwoWay-Hitterbox geometry (template coordinates)
    HITTERBOX_SPEED_CENTER = (432, 185)
    HITTERBOX_HAND_CENTER = (609, 185)
    HITTERBOX_TOP_Y, HITTERBOX_BOTTOM_Y = 26, 212   # top of the ON-BASE banner, bottom of the speed/hand bar
    BARS_GAP = -4                           # position bars tuck just under the speed/hand bar, like the native card
    HITTERBOX_BALL_LEFT_X = 173             # left edge of the ball's outer ring; the position bar lines up under it
    POSITION_BAR_MID_OFFSET = 30            # rows below the bars' top where the (slanted) first bar's left edge is measured
    CHART_EDGE_MARGIN = 139                 # both charts sit this far in from their side of the card
    PHOTO_SCALE = 0.79                      # both photos at this share of the regular card's photo size; a full-width
                                            # photo's right edge (scaled width + PITCHER_PHOTO_XY x) must land behind the pitcher chart
    HITTER_PHOTO_XY = (461, -188)           # where each side's scaled photo canvas (its regular card framing) is pasted
    PITCHER_PHOTO_XY = (-50, 789)
    BOTTOM_FRAME_Y = 1990                   # pitcher template rows from here down (legal text, set box, logo) are kept in place
    LEGAL_TEXT_LEFT_X = 380                 # legal text starts right of the set/year box
    LEGAL_TEXT_SCALE = 0.75                 # two-way cards have less room, so the legal text is smaller
    EDITION_LOGO_LEFT_BOTTOM = (110, 2055)  # edition logo's left edge and bottom (just above the set/year box)
    EDITION_LOGO_SCALE = 0.85

    def render(self) -> Image.Image:
        self.angle = math.degrees(math.atan2(self.SEAM_END_Y - self.SEAM_START, self.width))
        card_image = self._backgrounds()
        card_image.alpha_composite(self._photo_backgrounds())
        card_image.alpha_composite(self._card_art(self.hitter_layers.art_under, self.pitcher_layers.art_under))
        card_image.alpha_composite(self._hitter_photo())
        # ART OVER THE PLAYER GOES UNDER THE DIVIDER, SO THE PITCHER'S HALF CAN'T COVER IT
        card_image.alpha_composite(self._card_art(self.hitter_layers.art_over, self.pitcher_layers.art_over))
        divider_bar = self._divider_bar()
        card_image.alpha_composite(divider_bar)
        card_image.alpha_composite(self._pitcher_photo())
        holiday_frame = self.holiday_frame()
        if holiday_frame:
            # OVER BOTH PHOTOS LIKE A REGULAR CARD, BUT UNDER THE DIVIDER BAR (PART OF THE CARD'S FRAME)
            card_image.alpha_composite(self.clipped(holiday_frame, ImageOps.invert(divider_bar.split()[-1])))
        card_image.alpha_composite(self._bottom_frame())
        card_image.alpha_composite(self._hitter_block())
        card_image.alpha_composite(self._pitcher_block())
        set_image = self.hitter._set_and_year_image()
        card_image.alpha_composite(self.shifted(set_image, *self.bordered_xy(self.hitter, (0, 0))))
        card_image.alpha_composite(self._edition_logo())
        card_image.alpha_composite(self.stats_row())
        card_image.alpha_composite(self.year_and_expansion())
        return card_image

    def _edition_logo(self) -> Image.Image:
        """The edition logo (Super Season, Cooperstown, Rookie Season, Postseason, All-Star, WBC). Its native
        spot (right side, mid card) is taken by the divider and CONTROL banner, so it sits bottom-left over
        the pitcher's half, just above the set/year box and left of the legal text."""
        canvas = self.blank()
        additional_logo = self.hitter._additional_logo_image()
        if additional_logo is None:
            return canvas
        logo, _ = additional_logo
        logo = logo.convert('RGBA')
        bbox = logo.getbbox()
        if bbox is None:
            return canvas
        logo = self.scaled(logo.crop(bbox), self.EDITION_LOGO_SCALE)
        left_x, bottom_y = self.EDITION_LOGO_LEFT_BOTTOM
        canvas.alpha_composite(logo, (left_x, bottom_y - logo.height))
        return canvas

    @cached_property
    def pitcher_template(self) -> Image.Image:
        return self.pitcher._template_image().convert('RGBA')

    # ---------- GEOMETRY ----------

    def seam_y(self, x: float) -> float:
        return self.SEAM_START + (self.SEAM_END_Y - self.SEAM_START) * x / self.width

    def half_mask(self, below: bool) -> Image.Image:
        mask = Image.new('L', (self.width, self.height), 0)
        start, end = (0, self.SEAM_START), (self.width, self.SEAM_END_Y)
        points = [start, end, (self.width, self.height), (0, self.height)] if below else [(0, 0), (self.width, 0), end, start]
        ImageDraw.Draw(mask).polygon(points, fill=255)
        return mask

    # ---------- PHOTO HALVES ----------

    def _backgrounds(self) -> Image.Image:
        """Hitter half in the team color, pitcher half in the other team color for contrast."""
        top = self._side_background(self.hitter)
        with self.secondary_colored(self.pitcher):
            bottom = self._side_background(self.pitcher)
            if self.hitter.set == Set._2001:
                bottom.alpha_composite(self._pitcher_half_logo())
        top.paste(bottom, (0, 0), self.half_mask(below=True))
        return top

    def _side_background(self, card: ShowdownPlayerCard) -> Image.Image:
        """The side's background on the bordered canvas. A card that isn't bordered keeps its regular background's
        own transparency (ex: Nationality art's rounded corners), which the forced border would fill otherwise."""
        background = card._background_image(include_2000_name_container=False).convert('RGBA')
        if self.is_bordered:
            return background
        card.image.is_bordered = False
        try:
            regular_alpha = card._background_image(include_2000_name_container=False).convert('RGBA').split()[-1]
        finally:
            card.image.is_bordered = True
        if regular_alpha.getextrema()[0] == 255:
            return background  # FULLY OPAQUE, NOTHING TO KEEP
        alpha = Image.new('L', background.size, 0)
        alpha.paste(regular_alpha, (self.padding, self.padding))
        background.putalpha(ImageChops.multiply(background.split()[-1], alpha))
        return background

    def _pitcher_half_logo(self) -> Image.Image:
        """2001's background logo sits upper-left, crossing the hitter's ON-BASE banner, so the pitcher half
        gets its own, tilted the other way, crossing the CONTROL banner the same way: its tip rises the same
        distance above the banner, through the L of CONTROL. (2000's centered logo already shows in both halves.)"""
        def tip(logo: Image.Image) -> tuple[float, int]:
            alpha = np.asarray(logo.split()[-1]) > 60
            rows = np.nonzero(alpha.any(axis=1))[0]
            top_row = rows.min() if len(rows) else 0
            return float(np.nonzero(alpha[top_row])[0].mean()) if len(rows) else logo.width / 2, int(top_row)

        hitter_logo, (_, hitter_logo_y) = self.hitter.team_logo_for_background(team_override=self.hitter.team_override_for_images)
        rise = self.HITTERBOX_Y + self.HITTERBOX_TOP_Y - (hitter_logo_y + tip(hitter_logo)[1])  # TIP HEIGHT ABOVE ON-BASE
        logo, _ = self.pitcher.team_logo_for_background(team_override=self.pitcher.team_override_for_images, is_rotation_mirrored=True)
        tip_x, tip_y = tip(logo)
        target_x, target_y = self.CONTROL_L_X, self.CONTROL_BANNER_TOP_Y + self.PITCHER_BLOCK_Y - rise
        return self.shifted(logo, int(target_x - tip_x), int(target_y - tip_y))

    @cached_property
    def hitter_layers(self) -> PlayerImageGroups:
        return self._side_layers(self.hitter)

    @cached_property
    def pitcher_layers(self) -> PlayerImageGroups:
        """Built in the opposite team color, like the pitcher's half background (team colored parallel art matches it)."""
        with self.secondary_colored(self.pitcher):
            return self._side_layers(self.pitcher)

    def _side_layers(self, card: ShowdownPlayerCard) -> PlayerImageGroups:
        """The side's player image layers, framed exactly as on its regular card. The cutouts come
        without their glow, which is added after scaling."""
        original_glow = card.image.glow_multiplier
        card.image.glow_multiplier = 0
        try:
            return self.grouped_layers(card._player_image_layers(include_2000_containers=False))
        finally:
            card.image.glow_multiplier = original_glow

    def _card_art(self, hitter_art: list[PlayerImageLayer], pitcher_art: list[PlayerImageLayer]) -> Image.Image:
        """Each side's card art (parallels, edition art) unscaled in its own half. The art lines up across
        the divider, and team colored art takes each half's coloring."""
        canvas = self.clipped(self.composite(hitter_art, (self.width, self.height)), self.half_mask(below=False))
        canvas.alpha_composite(self.clipped(self.composite(pitcher_art, (self.width, self.height)), self.half_mask(below=True)))
        return canvas

    def _photo_backgrounds(self) -> Image.Image:
        """Each side's photo background (when its parallel shows one), moved and scaled like its photo and
        clipped to its own half. No glow, it's a full rectangle."""
        canvas = self.blank()
        for layers, xy, below in ((self.hitter_layers, self.HITTER_PHOTO_XY, False), (self.pitcher_layers, self.PITCHER_PHOTO_XY, True)):
            if layers.photo_background:
                background = self.shifted(self.scaled(self.composite(layers.photo_background, (self.width, self.height)), self.PHOTO_SCALE), *xy)
                canvas.alpha_composite(self.clipped(background, self.half_mask(below=below)))
        return canvas

    def _hitter_photo(self) -> Image.Image:
        """Hitter tucked behind the divider (clipped to the top half)."""
        photo = self._player_layer(self.hitter, self.hitter_layers.photo, self.HITTER_PHOTO_XY)
        return self.clipped(photo, self.half_mask(below=False))

    def _pitcher_photo(self) -> Image.Image:
        """Pitcher in the bottom half, cap breaking just over the divider."""
        return self._player_layer(self.pitcher, self.pitcher_layers.photo, self.PITCHER_PHOTO_XY)

    def _player_layer(self, card: ShowdownPlayerCard, photo_layers: list[PlayerImageLayer], xy: tuple[int, int]) -> Image.Image:
        """The side's photo layers scaled by PHOTO_SCALE and pasted with their canvas origin at `xy`,
        plus a white outer glow.

        Every card gets the same transform, so placement only depends on how the image is framed for
        its regular card. Off-center or cropped photos get a dedicated (TwoWay) auto image instead.
        """
        canvas = self.composite(photo_layers, (self.width, self.height))
        return self._with_glow(card, self.shifted(self.scaled(canvas, self.PHOTO_SCALE), *xy))

    def _with_glow(self, card: ShowdownPlayerCard, layer: Image.Image) -> Image.Image:
        """The same white outer glow a regular 00/01 cutout gets (set glow radius x the card's glow multiplier).
        Parallels that swap the glow for a drop shadow (ex: Gold Frame) get none, like their regular cards."""
        radius = int(card.set.player_image_glow_radius * card.image.glow_multiplier)
        if radius <= 0 or PlayerImageComponent.GLOW in card.image.parallel.special_components_replacements:
            return layer
        glowed = card._add_outer_glow(image=layer, color='white', radius=radius, enhancement_factor=1.75)
        return glowed.crop((radius, radius, radius + layer.width, radius + layer.height))  # GLOW PADS BY THE RADIUS

    # ---------- DIVIDER ----------

    def _divider_bar(self) -> Image.Image:
        """The 2000 name container (brushed silver edges, black center) along the diagonal: name, then the two-way total points."""
        length = int(math.hypot(self.width, self.SEAM_END_Y - self.SEAM_START)) + 300
        bar = self._name_container_bar(length)
        draw = ImageDraw.Draw(bar)
        middle_y = self.BAR_EDGE + self.BAR_CENTER // 2

        def along(x: float) -> float:
            """Card x -> distance along the bar."""
            return length / 2 + (x - self.width / 2) / math.cos(math.radians(self.angle))

        name = self.hitter.name_on_card_image
        label, points = 'TWO-WAY ', f'{self.total_points_text} pt.'
        name_x, end_x, gap = along(600), along(self.width - self.padding - 20), 55

        def fonts(name_size: int) -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
            """Name font, plus the total's font sized so its capitals stand as tall as the name's."""
            name_font = self.font('Futura Black', name_size)
            total_size = round(self.TOTAL_FONT_SIZE * self.cap_height(name_font) / self.cap_height(self.font(self.OBLIQUE, self.TOTAL_FONT_SIZE)))
            return name_font, self.font(self.OBLIQUE, total_size)

        name_size = 62
        name_font, total_font = fonts(name_size)
        while name_size > 36 and name_x + name_font.getlength(name) + gap + total_font.getlength(label + points) > end_x:
            name_size -= 2
            name_font, total_font = fonts(name_size)

        # SHARED BASELINE: BOTH FONTS' CAPITALS CENTERED IN THE BAR
        baseline_y = middle_y + self.cap_height(name_font) / 2
        draw.text((name_x, baseline_y), name, font=name_font, fill=colors.WHITE, anchor='ls')
        total_x = name_x + name_font.getlength(name) + gap
        draw.rectangle((total_x - 30, self.BAR_EDGE + 8, total_x - 24, self.BAR_EDGE + self.BAR_CENTER - 8), fill=self.BAR_DIVIDER)
        draw.text((total_x, baseline_y), label, font=total_font, fill=self.BAR_DIVIDER, anchor='ls')
        draw.text((total_x + total_font.getlength(label), baseline_y), points, font=total_font, fill=colors.WHITE, anchor='ls')

        bar = bar.rotate(-self.angle, expand=True, resample=Image.Resampling.BICUBIC)
        mid_x, mid_y = self.width // 2, int(self.seam_y(self.width / 2))
        return self.shifted(bar, mid_x - bar.width // 2, mid_y - bar.height // 2)

    @staticmethod
    def cap_height(font: ImageFont.FreeTypeFont) -> int:
        """Height of a capital letter above the baseline."""
        return -font.getbbox('H', anchor='ls')[1]

    def _name_container_bar(self, length: int) -> Image.Image:
        """The 2000 name container turned horizontal: its silver edges and black center resized
        separately to BAR_EDGE / BAR_CENTER, so the brushed texture keeps its full height on each edge."""
        container = self.hitter._2000_player_name_container_image().convert('RGBA')
        container = container.crop(container.getbbox()).rotate(90, expand=True)
        edge = container.height * 45 // 225  # SILVER EDGE SHARE OF THE CONTAINER (45 OF 225 PX)
        bands = [
            (container.crop((0, 0, container.width, edge)), self.BAR_EDGE),
            (container.crop((0, edge, container.width, container.height - edge)), self.BAR_CENTER),
            (container.crop((0, container.height - edge, container.width, container.height)), self.BAR_EDGE),
        ]
        bar = Image.new('RGBA', (length, 2 * self.BAR_EDGE + self.BAR_CENTER), (0, 0, 0, 0))
        y = 0
        for band, height in bands:
            bar.alpha_composite(band.resize((length, height), Image.Resampling.LANCZOS), (0, y))
            y += height
        return bar

    # ---------- FRAME ----------

    def _bottom_frame(self) -> Image.Image:
        """The pitcher template's bottom strip in its native spot: legal text, the bot logo, and on 2001 the
        subtle black set/year box. 2000 draws that box as its own layer, so it's added here too."""
        canvas = self.blank()
        if self.hitter.set == Set._2000:
            set_box = self.hitter._2000_player_set_container_image().convert('RGBA')
            canvas.alpha_composite(set_box, self.bordered_xy(self.hitter, (0, 0)))
        strip = self.pitcher_template.crop((0, self.BOTTOM_FRAME_Y, self.width, self.height))
        canvas.alpha_composite(strip, (0, self.BOTTOM_FRAME_Y))
        return self._shrink_legal_text(canvas)

    def _shrink_legal_text(self, canvas: Image.Image) -> Image.Image:
        """Scale the legal text down by LEGAL_TEXT_SCALE, centered on the area it filled at full size.
        The text is whatever the strip draws between the set/year box and the bot logo."""
        logo_x, _ = self.bordered_xy(self.hitter, self.hitter.set.template_component_paste_coordinates(TemplateImageComponent.BOT_LOGO))
        region = (self.LEGAL_TEXT_LEFT_X, self.BOTTOM_FRAME_Y, logo_x, self.height)
        bbox = canvas.crop(region).getbbox()
        if bbox is None:
            return canvas
        left, top, right, bottom = bbox[0] + region[0], bbox[1] + region[1], bbox[2] + region[0], bbox[3] + region[1]
        text = self.scaled(canvas.crop((left, top, right, bottom)), self.LEGAL_TEXT_SCALE)
        canvas.paste((0, 0, 0, 0), (left, top, right, bottom))
        x, y = (left + right - text.width) // 2, (top + bottom - text.height) // 2
        canvas.alpha_composite(text, (x, y))
        return canvas

    def _chart_panel(self, card: ShowdownPlayerCard, template: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
        """The side's chart box (from its template) with its chart text, scaled down."""
        chart, color = card._chart_image()
        chart_xy = self.bordered_xy(card, card.set.template_component_paste_coordinates(TemplateImageComponent.CHART, player_type=card.player_type))
        panel = template.copy()
        panel.paste(color, chart_xy, chart)
        return self.scaled(panel.crop(box), self.CHART_SCALE)

    # ---------- HITTER (TOP-LEFT) ----------

    def _hitter_block(self) -> Image.Image:
        """Command banner (TwoWay-Hitterbox template), the native position/points bars moved left, and the chart."""
        canvas = self.blank()
        oblique = lambda size: self.font(self.OBLIQUE, size)

        # POSITION + POINTS BARS: THE NATIVE BARS AND THEIR TEXT, SLID LEFT UNDER THE BANNER
        canvas.alpha_composite(self._position_bars())

        # COMMAND BANNER + SPEED/HAND BAR
        box_x, box_y = 0, self.HITTERBOX_Y
        canvas.alpha_composite(self.template('2000-TwoWay-Hitterbox'), (box_x, box_y))
        command = self.template(f'{self.hitter.set.template_year}-Hitter-{self.hitter.chart.command}')
        command = command.crop(command.getbbox())
        ball_x, ball_y = self.HITTERBOX_BALL_CENTER
        canvas.alpha_composite(command, (box_x + ball_x - command.width // 2, box_y + ball_y - command.height // 2))

        draw = ImageDraw.Draw(canvas)
        show_speed_number = self.hitter.set == Set._2001 or self.hitter.is_variable_speed_00_01
        speed = f'SPEED {self.hitter.speed.letter.value}' + (f' ({self.hitter.speed.speed})' if show_speed_number else '')
        speed_x, speed_y = self.HITTERBOX_SPEED_CENTER
        hand_x, hand_y = self.HITTERBOX_HAND_CENTER
        draw.text((box_x + speed_x, box_y + speed_y), speed, font=oblique(46), fill=colors.WHITE, anchor='mm')
        draw.text((box_x + hand_x, box_y + hand_y), self.hitter.hand.value, font=oblique(50), fill=colors.WHITE, anchor='mm')

        # CHART, SAME DISTANCE FROM THE LEFT EDGE AS THE PITCHER'S IS FROM THE RIGHT
        # EXTRA POSITION BARS (MULTI-POSITION, E.G. CAREER CARDS) PUSH THE CHART DOWN BY THEIR HEIGHT
        panel = self._chart_panel(self.hitter, self.hitter._template_image(), (1155, 1375, 1505, 1925))
        canvas.alpha_composite(panel, (self.CHART_EDGE_MARGIN, 690 - self.UP + self._extra_position_bars_height))
        return canvas

    @property
    def _position_bar_sizings(self) -> list[str]:
        """Per position bar, in card order: LARGE for long position text (e.g. LF/RF), else SMALL."""
        return ['LARGE' if len(position) > 4 else 'SMALL' for position, _ in self.hitter.positions_and_defense_img_order]

    def _position_bars_template(self, sizings: list[str]) -> Image.Image:
        return self.template(f"0001-Hitter-{'-'.join(sizings)}")

    @property
    def _extra_position_bars_height(self) -> int:
        """How much taller the hitter's position/points bars are than a single-position card's."""
        sizings = self._position_bar_sizings
        height = lambda image: image.getbbox()[3] - image.getbbox()[1]
        return height(self._position_bars_template(sizings)) - height(self._position_bars_template(sizings[:1]))

    def _position_bars(self) -> Image.Image:
        """The hitter's native position/points bars with their native text, moved to the left side."""
        bars_template = self._position_bars_template(self._position_bar_sizings)
        bars = self.blank()
        bars.alpha_composite(bars_template, (self.padding, self.padding))
        metadata, color = self.hitter._metadata_image(include_speed_and_hand=False)
        bars.alpha_composite(self.layer(metadata, (self.padding, self.padding), color))
        bars_top = bars_template.getbbox()[1] + self.padding
        mid_row = bars.split()[-1].crop((0, bars_top + self.POSITION_BAR_MID_OFFSET, self.width, bars_top + self.POSITION_BAR_MID_OFFSET + 1))
        position_bar_left = mid_row.getbbox()[0]
        bars_target_top = self.HITTERBOX_Y + self.HITTERBOX_BOTTOM_Y + self.BARS_GAP
        return self.shifted(bars, self.HITTERBOX_BALL_LEFT_X - position_bar_left, bars_target_top - bars_top)

    # ---------- PITCHER (BOTTOM-RIGHT) ----------

    def _pitcher_block(self) -> Image.Image:
        """The pitcher's native command block and metadata, lowered, plus its chart."""
        canvas = self.blank()
        template = self.pitcher_template
        canvas.alpha_composite(template.crop((850, 230, self.width, 660)), (850, 230 + self.PITCHER_BLOCK_Y))

        metadata, color = self.pitcher._metadata_image()
        metadata_x, metadata_y = self.bordered_xy(self.pitcher, self.pitcher.set.template_component_paste_coordinates(TemplateImageComponent.METADATA))
        canvas.paste(color, (metadata_x, metadata_y + self.PITCHER_BLOCK_Y), metadata)

        panel = self._chart_panel(self.pitcher, template, (1155, 1385, 1505, 1895))
        canvas.alpha_composite(panel, (self.width - self.CHART_EDGE_MARGIN - panel.width, 1500))
        return canvas


class SideBySideLayout(TwoWayLayout):
    """Shared by the layouts that put both photos side by side (2002, 2004/2005): each side's background
    fills the card and blends into the other's along a diagonal seam, with both whole cutouts over it."""

    INCLUDES_CUTOUT = True                      # BOTH SIDES LOAD THEIR PLAIN CUTOUTS, DRAWN WHOLE OVER THE SEAM
    # THE SEAM BETWEEN THE TWO BACKGROUNDS (CANVAS X AT THE TOP / BOTTOM EDGE), BLENDED OVER SEAM_BLEND PX. IT TURNS
    # MORE UPRIGHT WHEN A PHOTO SLIDES FAR ENOUGH THAT ITS HALF WOULD REACH ITS FILLED EDGE (SEE seam_xs)
    SEAM_TOP_X, SEAM_BOTTOM_X = 1420, 60
    SEAM_BLEND = 45
    # EACH PHOTO SLIDES TOWARD ITS OWN HALF
    HITTER_PHOTO_XY, PITCHER_PHOTO_XY = (-300, 0), (400, 0)

    # ---------- PHOTOS ----------

    def _side_images(self, card: ShowdownPlayerCard) -> tuple[Image.Image, PlayerImageGroups]:
        """The side's background and player image layers, framed exactly like the side's own card. They're
        always built with the bleed (cards are bordered while composing), so a photo slid toward its half shows
        its own bleed instead of a filled edge. Non-bordered cards crop the bleed off afterwards.
        Off-center players get a dedicated (TwoWay) image in the library."""
        return card._background_image().convert('RGBA'), self.grouped_layers(card._player_image_layers())

    @property
    def seam_edge_margin(self) -> int:
        """How far the seam stays from a photo's filled edge: the seam's feather plus the fill's fade into the photo."""
        return 2 * self.SEAM_BLEND + self.SLIDE_FILL_FADE // 2

    @property
    def seam_xs(self) -> tuple[int, int]:
        """The seam's (top, bottom) canvas x. The hitter's photo, slid left, ends its real pixels (bleed
        included) short of the card's right edge, and the pitcher's, slid right, starts its real pixels past
        the left edge. The seam is turned upright as needed so the hitter's half ends before the hitter's
        filled edge at the top, and the pitcher's half starts after the pitcher's at the bottom."""
        hitter_real_right_x = self.width + min(self.HITTER_PHOTO_XY[0], 0)
        pitcher_real_left_x = max(self.PITCHER_PHOTO_XY[0], 0)
        top_x = min(self.SEAM_TOP_X, hitter_real_right_x - self.seam_edge_margin)
        bottom_x = max(self.SEAM_BOTTOM_X, pitcher_real_left_x + self.seam_edge_margin)
        return top_x, bottom_x

    def _hitter_mask(self) -> Image.Image:
        """The hitter's half left of the seam (the pitcher's is the rest), feathered so the two backgrounds
        blend into each other."""
        top_x, bottom_x = self.seam_xs
        mask = Image.new('L', (self.width, self.height), 0)
        ImageDraw.Draw(mask).polygon([(0, 0), (top_x, 0), (bottom_x, self.height), (0, self.height)], fill=255)
        return mask.filter(ImageFilter.GaussianBlur(self.SEAM_BLEND))

    SLIDE_FILL_BLUR, SLIDE_FILL_FADE = 30, 120

    def slid(self, image: Image.Image, dx: int, dy: int) -> Image.Image:
        """An opaque background moved by (dx, dy) at the same size. The edges it uncovers are filled by
        stretching its edge pixels outward, heavily blurred and faded into the photo, so they read as more
        out-of-focus crowd (a mirror would reflect the player's cap). The seam keeps each half off its own
        photo's filled side edge (see seam_xs), so this mostly shows only along the card's outer edges."""
        if dx == 0 and dy == 0:
            return image
        pixels = np.asarray(image.convert('RGBA'))
        height, width = pixels.shape[:2]
        pad = ((max(dy, 0), max(-dy, 0)), (max(dx, 0), max(-dx, 0)), (0, 0))
        padded = np.pad(pixels, pad, mode='edge')
        top, left = max(-dy, 0), max(-dx, 0)
        slid = Image.fromarray(padded[top:top + height, left:left + width])

        # BLUR THE UNCOVERED EDGES AND FADE THEM INTO THE PHOTO
        uncovered = Image.new('L', slid.size, 255)
        uncovered.paste(0, (max(dx, 0), max(dy, 0), width + min(dx, 0), height + min(dy, 0)))
        fade = ImageChops.lighter(uncovered.filter(ImageFilter.GaussianBlur(self.SLIDE_FILL_FADE / 2)), uncovered)
        slid.paste(slid.filter(ImageFilter.GaussianBlur(self.SLIDE_FILL_BLUR)), (0, 0), fade)
        return slid

    HEAD_SHARE = 0.13             # top share of a cutout's body height treated as the player's head
    LIMB_WIDTH = 150              # parts thinner than this (raised arms, bats) aren't the body when finding the head
    BODY_SCALE = 8                # the body is found at 1/8 size, so the limb filter stays cheap
    HEAD_COVER_MARGIN = 0.05      # the hitter only moves in front when that hides clearly less of a head
    # THE FRONT CUTOUT'S SOFT SHADOW, CAST ONLY ON THE BACK PLAYER (NOT THE FAR-OFF BACKGROUND), NUDGED TOWARD THEM
    OVERLAP_SHADOW_BLUR, OVERLAP_SHADOW_OPACITY, OVERLAP_SHADOW_OFFSET = 18, 0.55, 12

    @classmethod
    def _head_alpha(cls, cutout: Image.Image) -> np.ndarray:
        """The cutout's alpha (0-1) kept only over the top of the player's body (their head). Thin parts are
        opened away and loose pieces dropped first, so a raised throwing hand or a bat above the helmet isn't
        mistaken for the head."""
        alpha_image = cutout.getchannel('A')
        alpha = np.asarray(alpha_image, dtype=np.float32) / 255
        kernel = cls.LIMB_WIDTH // cls.BODY_SCALE | 1
        small = (alpha_image.resize((cutout.width // cls.BODY_SCALE, cutout.height // cls.BODY_SCALE))
                 .point(lambda v: 255 if v > 127 else 0)
                 .filter(ImageFilter.MinFilter(kernel)).filter(ImageFilter.MaxFilter(kernel)))

        # KEEP ONLY THE PIECE CONNECTED TO THE WIDEST ROW (THE TORSO / LEGS), DROPPING ISLANDS LIKE A FIST AND BALL
        pixels = np.asarray(small)
        if pixels.max() == 0:
            return np.zeros_like(alpha)
        widest_row = int((pixels > 0).sum(axis=1).argmax())
        columns = np.flatnonzero(pixels[widest_row])
        ImageDraw.floodfill(small, (int(columns[len(columns) // 2]), widest_row), 128)
        body = small.point(lambda v: 255 if v == 128 else 0).resize(cutout.size)
        body = np.asarray(body, dtype=np.float32) / 255
        rows = np.flatnonzero(body.max(axis=1) > 0.5)
        bottom = rows[0] + int((rows[-1] - rows[0]) * cls.HEAD_SHARE)
        head = np.zeros_like(alpha)
        head[rows[0]:bottom] = (alpha * body)[rows[0]:bottom]
        return head

    @classmethod
    def _head_covered(cls, front: Image.Image, back: Image.Image) -> float:
        """Share of the back cutout's head hidden by the front cutout."""
        head = cls._head_alpha(back)
        total = head.sum()
        if total == 0:
            return 0.0
        return float((head * np.asarray(front.getchannel('A'), dtype=np.float32) / 255).sum() / total)

    def _stacked(self, hitter_cutout: Image.Image, pitcher_cutout: Image.Image) -> list[Image.Image]:
        """Back to front: the back cutout, the front cutout's shadow on it, then the front cutout. The pitcher
        usually goes in front (their throwing arm reaching across reads well), but the hitter does when the
        pitcher's arm or glove would otherwise cover the hitter's face."""
        hitter_head_hidden = self._head_covered(front=pitcher_cutout, back=hitter_cutout)
        pitcher_head_hidden = self._head_covered(front=hitter_cutout, back=pitcher_cutout)
        is_hitter_in_front = hitter_head_hidden > pitcher_head_hidden + self.HEAD_COVER_MARGIN
        back, front = (pitcher_cutout, hitter_cutout) if is_hitter_in_front else (hitter_cutout, pitcher_cutout)
        return [back, self._overlap_shadow(front, back, toward_left=not is_hitter_in_front), front]

    def _overlap_shadow(self, front: Image.Image, back: Image.Image, toward_left: bool) -> Image.Image:
        """The front cutout's blurred silhouette, shifted toward the back player and kept only on them."""
        offset = self.OVERLAP_SHADOW_OFFSET
        silhouette = front.getchannel('A').filter(ImageFilter.GaussianBlur(self.OVERLAP_SHADOW_BLUR))
        silhouette = silhouette.point(lambda v: int(v * self.OVERLAP_SHADOW_OPACITY))
        cast = Image.new('L', front.size, 0)
        cast.paste(silhouette, (-offset if toward_left else offset, offset // 2))
        shadow = Image.new('RGBA', front.size, (0, 0, 0, 0))
        shadow.putalpha(ImageChops.multiply(cast, back.getchannel('A')))
        return shadow

    def _photos(self) -> Image.Image:
        """Both backgrounds fill the card, blended along the seam, with each side's whole cutout over them
        (stacked so neither covers the other's face), so neither player is cut by the seam. Each side's photo slides toward its own half, while its card art
        (parallels, edition art) stays put so both halves line up into one finish."""
        side_size = self.hitter.set.card_size_bordered

        halves, cutouts, art_overs = [], [], []
        for card, xy in ((self.hitter, self.HITTER_PHOTO_XY), (self.pitcher, self.PITCHER_PHOTO_XY)):
            background, groups = self._side_images(card)
            side = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
            side.alpha_composite(self.slid(background, *xy))
            side.alpha_composite(self.slid(self.composite(groups.photo_background, side_size), *xy))
            side.alpha_composite(self.composite(groups.art_under, side_size))
            halves.append(side)
            cutouts.append(self.shifted(self.composite(groups.photo, side_size), *xy))
            art_overs.append(self.composite(groups.art_over, side_size))

        hitter_mask = self._hitter_mask()
        canvas = Image.composite(halves[0], halves[1], hitter_mask)

        # BOTH CUTOUTS SIT WHOLE OVER THE BLENDED BACKGROUNDS, UNDER EACH SIDE'S CARD ART
        for layer in self._stacked(*cutouts):
            canvas.alpha_composite(layer)
        for art_over, mask in zip(art_overs, (hitter_mask, ImageOps.invert(hitter_mask))):
            canvas.alpha_composite(self.clipped(art_over, mask))

        # HOLIDAY FRAME OVER BOTH PHOTOS AND THE SEAM, UNDER THE BANDS (LIKE A REGULAR CARD'S TEMPLATE)
        holiday_frame = self.holiday_frame()
        if holiday_frame:
            canvas.alpha_composite(holiday_frame)
        return canvas


class BlockLayout0405(SideBySideLayout):
    """2004/2005: side-by-side photos, then one name band and a band block per side."""

    ROW = 68                                   # band row pitch
    HITTER_BLOCK_Y, PITCHER_BLOCK_Y = 1563, 1767
    NATIVE_META_Y = 1770                       # native top of the metadata band
    NAME_X = 150
    CHART_X = (395, 1460)
    # BADGE TEMPLATE, ITS NATIVE (REGULAR CARD) POSITION ON THE BORDERED CANVAS, THE NATIVE MIDDLE Y, AND ITS SCALE
    # (FROM ITS TOP CENTER, WITH ITS COMMAND NUMBER). THE TALLER CONTROL BADGE IS SHRUNK SO ITS BANNER
    # STAYS ABOVE THE BOTTOM ROW. KEYED BY is_pitcher
    BADGES: dict[bool, tuple[str, tuple[int, int], int, float]] = {
        False: ('0405-ONBASE', (123, 1635), 1728, 1.0),
        True: ('0405-CONTROL', (126, 1605), 1705, 0.94),
    }
    BADGE_DX = -10
    CONDENSED = 'Helvetica Neue 77 Bold Condensed'
    TOTAL_GAP = 30                             # space kept between the total points and the logo (or its year text)
    TOTAL_MIN_SCALE = 0.6                      # the total shrinks no further than this for long names

    def render(self) -> Image.Image:
        self.name_band_dy = self.HITTER_BLOCK_Y - self.NATIVE_META_Y
        card_image = self._photos()
        card_image.alpha_composite(self._bands())
        card_image.alpha_composite(self._text())
        return card_image

    # ---------- BANDS ----------

    def _strip(self, template: Image.Image) -> Image.Image:
        """One band row (separator line + clean colored row) from a template."""
        return template.crop((0, 1835, self.width, 1835 + self.ROW))

    def _bands(self) -> Image.Image:
        canvas = self.blank()
        hitter_template = self.hitter._template_image().convert('RGBA')
        pitcher_template = self.pitcher._template_image().convert('RGBA')

        # NAME BAND WITHOUT THE BAKED BADGE: REPAINT THE BADGE COLUMNS WITH THE BAND COLOR NEXT TO THEM
        name_band = hitter_template.crop((0, 1655, self.width, self.NATIVE_META_Y))
        pixels = name_band.load()
        for y in range(name_band.height):
            color = pixels[345, y]
            for x in range(345):
                pixels[x, y] = color
        canvas.alpha_composite(name_band, (0, 1655 + self.name_band_dy))

        for index in range(3):
            canvas.alpha_composite(self._strip(hitter_template), (0, self.HITTER_BLOCK_Y + index * self.ROW))
            canvas.alpha_composite(self._strip(pitcher_template), (0, self.PITCHER_BLOCK_Y + index * self.ROW))
        # BOTTOM ROW (STATS PERIOD + STAT HIGHLIGHTS HOLDER) SITS UNDER THE PITCHER BLOCK, SO IT TAKES ITS COLOR
        bottom_y = self.PITCHER_BLOCK_Y + 3 * self.ROW
        canvas.alpha_composite(pitcher_template.crop((0, bottom_y, self.width, self.height)), (0, bottom_y))
        ImageDraw.Draw(canvas).rectangle((0, self.PITCHER_BLOCK_Y - 3, self.width, self.PITCHER_BLOCK_Y + 6), fill=(0, 0, 0))

        # COMMAND BADGES (0405-ONBASE / 0405-CONTROL) WITH THE SIDE'S COMMAND NUMBER, CENTERED ON THEIR BLOCK
        for card, block_y in ((self.hitter, self.HITTER_BLOCK_Y), (self.pitcher, self.PITCHER_BLOCK_Y)):
            badge_name, (native_x, native_y), native_middle_y, scale = self.BADGES[card.is_pitcher]
            dx, dy = self.BADGE_DX, block_y + 3 * self.ROW // 2 - native_middle_y
            badge = self.template(badge_name)
            badge_x, badge_y = native_x + dx, native_y + dy
            layer = self.blank()
            layer.alpha_composite(badge, (badge_x, badge_y))
            player_type = 'Pitcher' if card.is_pitcher else 'Hitter'
            command = self.template(f'{card.set.template_year}-{player_type}-{card.chart.command}')
            layer.alpha_composite(self.shifted(command, self.padding + dx, self.padding + dy))
            canvas.alpha_composite(self.scaled_about(layer, (badge_x + badge.width / 2, badge_y), scale))
        return canvas

    # ---------- TEXT ----------

    def _text(self) -> Image.Image:
        canvas = self.blank()

        # NAME + LOGO RISE WITH THE NAME BAND
        name_text, name_color = self.hitter._player_name_text_image()
        name_xy = self.bordered_xy(self.hitter, self.hitter.set.template_component_paste_coordinates(TemplateImageComponent.PLAYER_NAME))
        name = self.layer(name_text, name_xy, name_color)
        name_bbox = name.getbbox() or (self.NAME_X, 0, self.NAME_X, 0)
        name_dx = self.NAME_X - name_bbox[0]
        canvas.alpha_composite(self.shifted(name, name_dx, self.name_band_dy))
        total_end_x = self.width - self.padding - self.TOTAL_GAP
        if not self.hitter.image.hide_team_logo:
            logo, logo_xy = self.hitter._team_logo_image()
            logo_layer = self.shifted(self.layer(logo, self.bordered_xy(self.hitter, logo_xy), logo), 0, self.name_band_dy)
            canvas.alpha_composite(logo_layer)
            logo_bbox = logo_layer.getbbox()
            if logo_bbox:
                total_end_x = logo_bbox[0] - self.TOTAL_GAP  # INCLUDES THE OPTIONAL YEAR TEXT LEFT OF THE LOGO

        # TOTAL POINTS AFTER THE NAME, SHRUNK WHEN NEEDED TO END BEFORE THE LOGO (AND YEAR TEXT)
        draw = ImageDraw.Draw(canvas)
        label, total = 'TWO-WAY', f'{self.total_points_text} PT.'
        total_y = 1655 + self.name_band_dy + 62
        label_x = name_bbox[2] + name_dx + 40
        scale = 1.0
        while True:
            label_font, total_font = self.font(self.CONDENSED, round(34 * scale)), self.font(self.CONDENSED, round(58 * scale))
            label_gap = round(14 * scale)
            if scale <= self.TOTAL_MIN_SCALE or label_x + label_font.getlength(label) + label_gap + total_font.getlength(total) <= total_end_x:
                break
            scale -= 0.05
        draw.text((label_x, total_y), label, font=label_font, fill=(225, 225, 225), anchor='lm')
        draw.text((label_x + label_font.getlength(label) + label_gap, total_y), total, font=total_font, fill=colors.WHITE, anchor='lm')

        # EACH SIDE'S METADATA + ICONS IN ITS OWN BLOCK
        for card, block_y in ((self.hitter, self.HITTER_BLOCK_Y), (self.pitcher, self.PITCHER_BLOCK_Y)):
            dy = block_y - self.NATIVE_META_Y
            metadata, color = card._metadata_image()
            metadata_xy = self.bordered_xy(card, card.set.template_component_paste_coordinates(TemplateImageComponent.METADATA))
            canvas.alpha_composite(self.shifted(self.layer(metadata, metadata_xy, color), 0, dy))
            canvas.alpha_composite(self.shifted(card._add_icons_to_image(self.blank()), 0, dy))

        set_image = self.hitter._set_and_year_image()
        canvas.alpha_composite(self.shifted(set_image, *self.bordered_xy(self.hitter, (0, 0))))
        canvas.alpha_composite(self.stats_row())
        canvas.alpha_composite(self.year_and_expansion())

        # CHARTS: EACH SIDE IN ITS NATIVE COLUMNS, RIGHT OF ITS BADGE
        sides = [(self._chart_columns(card), block_y) for card, block_y in ((self.hitter, self.HITTER_BLOCK_Y), (self.pitcher, self.PITCHER_BLOCK_Y))]
        chart_font = self._fitted_chart_font([columns for columns, _ in sides])
        for columns, block_y in sides:
            self._draw_chart(draw, columns, block_y, chart_font)
        return canvas

    @staticmethod
    def _chart_columns(card: ShowdownPlayerCard) -> list[tuple[str, str]]:
        return [(category.value, card.chart.ranges[category]) for category in card.chart.categories_list]

    def _column_spacing(self, columns: list[tuple[str, str]]) -> float:
        x0, x1 = self.CHART_X
        return (x1 - x0) / max(len(columns) - 1, 1)

    def _fitted_chart_font(self, sides: list[list[tuple[str, str]]]) -> ImageFont.FreeTypeFont:
        """Largest font (up to the regular chart size) whose ranges fit every side's columns."""
        size = 57
        while size > 30:
            font = self.font(self.CONDENSED, size)
            if all(max(font.getlength(text) for _, text in columns) <= self._column_spacing(columns) - 22 for columns in sides):
                return font
            size -= 1
        return self.font(self.CONDENSED, size)

    def _draw_chart(self, draw: ImageDraw.ImageDraw, columns: list[tuple[str, str]], block_y: int, font: ImageFont.FreeTypeFont) -> None:
        spacing = self._column_spacing(columns)
        for index, (label, range_text) in enumerate(columns):
            x = self.CHART_X[0] + index * spacing
            for row, text in ((1, range_text), (2, label)):
                draw.text((x, block_y + row * self.ROW + 37), text, font=font, fill=colors.WHITE, anchor='mm', stroke_width=3, stroke_fill=(20, 20, 20))


class BlockLayout02(SideBySideLayout):
    """2002: side-by-side photos under the native frame, and both command boxes side by side along the
    bottom (pitcher in the native spot, hitter left of it), raised over a strip holding the set/year box,
    bot logo and legal text. The name column fades in from the top so the photos show through it, and
    ends on the pitcher box like a regular card's. The two-way total sits on a tab over the CONTROL header."""

    PHOTO_FRAMING_SET = Set._2004              # THE WIDER 04/05 FRAMING (NATIVE 02 IS ZOOMED IN), SO NEITHER PLAYER'S ARMS RUN UNDER THE NAME COLUMN
    # 04/05'S PHOTO PLACEMENT AND SEAM (THE FADING NAME COLUMN LETS THE PITCHER'S ARM SHOW THROUGH), MOVED
    # DOWN SO THE HEADS SIT JUST UNDER THE MLB SHOWDOWN HEADER
    PHOTO_DY = 72
    HITTER_PHOTO_XY = (SideBySideLayout.HITTER_PHOTO_XY[0] - 80, SideBySideLayout.HITTER_PHOTO_XY[1] + PHOTO_DY)
    PITCHER_PHOTO_XY = (SideBySideLayout.PITCHER_PHOTO_XY[0] - 30, SideBySideLayout.PITCHER_PHOTO_XY[1] + PHOTO_DY)
    BOX = (858, 1470, 1512, 2106)              # NATIVE COMMAND BOX BOUNDS. IT'S L-SHAPED (BOX_PARTS): THE LEGAL TEXT SITS IN ITS NOTCH
    BOX_PARTS = (
        (858, 1525, 1511, 1922),               # COMMAND HEADER + METADATA
        (1147, 1525, 1511, 2106),              # RANGES + RESULTS
        (1289, 1470, 1512, 1525),              # BLACK CAP OVER THE COMMAND SQUARE (ITS TOP AND LEFT BORDER, BELOW THE NAME COLUMN'S STRIPES)
    )
    BOXES_DY = -100                            # BOTH BOXES RISE TO MAKE ROOM FOR THE STRIP UNDER THEM
    BOX_GAP = 40                               # BETWEEN THE HITTER BOX AND THE PITCHER BOX
    LOGO_GAP = 25                              # KEPT BETWEEN THE RAISED LOGOS AND THE HITTER BOX
    # NATIVE BOTTOM STRIP: THE SET/YEAR BOX + BOT LOGO, THEN THE LEGAL TEXT LEFT OF THE RANGES COLUMN
    STRIP = (0, 1921, 1147, 2106)
    LEGAL_BOX = (360, 1926, 1140, 2106)        # JUST THE LEGAL TEXT (INSIDE THE BOX'S OWN EDGES)
    BAND_X = 320                               # A STRIP COLUMN WITH ONLY THE TRANSLUCENT BAND (NO TEXT), STRETCHED FULL WIDTH
    BAND_MAX_ALPHA = 40                        # STRIP PIXELS THIS TRANSPARENT ARE THE BAND, NOT TEXT
    STRIP_TOP_Y = 2012                         # WHERE THE STRIP'S TOP LANDS (JUST UNDER THE BOXES)
    LEGAL_SCALE = 0.7                          # THE LEGAL TEXT SHRINKS TO FIT UNDER THE PITCHER BOX, RIGHT ALIGNED WITH IT
    STATS_ROW_X, STATS_ROW_GAP = 310, 30       # THE STATS ROW (SPLIT / STAT HIGHLIGHTS) FILLS THE STRIP FROM HERE TO THE LEGAL TEXT
    STATS_ROW_DY = 8                           # STATS ROW TOP BELOW THE STRIP TOP
    # NAME COLUMN: THE NATIVE ONE (WITH ITS STRIPES) IS REPLACED BY ITS BLACK CENTER FADING IN FROM THE TOP,
    # LIKE THE GOLD FRAME TEMPLATE'S. IT'S PARTLY SEE-THROUGH WHERE THE NAME BEGINS AND NEARLY SOLID AT THE BOX
    NAME_COLUMN_X = (1290, 1512)               # NATIVE COLUMN, STRIPES INCLUDED
    FADE_X = (1323, 1482)                      # ITS BLACK CENTER
    FADE_NAME_OPACITY, FADE_END_OPACITY = 0.6, 0.97
    # TOTAL ON A TAB OVER THE PITCHER'S HEADER, AS TALL AS THE CAP OVER THE COMMAND SQUARE
    TOTAL_RIGHT_X = 1241                       # RIGHT EDGE OF THE NATIVE CONTROL TEXT
    TOTAL_SCALE = 0.62
    TOTAL_BASELINE_INSET = 8                   # BASELINE ABOVE THE TAB'S BOTTOM
    TOTAL_TAB_TUCK = 6                         # THE TAB RUNS THIS FAR UNDER THE HEADER AND THE CAP

    def render(self) -> Image.Image:
        card_image = self._photos()
        card_image.alpha_composite(self._frame())
        card_image.alpha_composite(self._logos())
        card_image.alpha_composite(self._strip())
        card_image.alpha_composite(self._total_tab())  # UNDER THE BOXES, SO THEIR SOFT EDGES BLEND INTO IT
        for card, dx in ((self.hitter, self.hitter_box_dx), (self.pitcher, 0)):
            card_image.alpha_composite(self._box(card, dx))
        card_image.alpha_composite(self.name_layer)
        card_image.alpha_composite(self._stats_row_in_strip())
        card_image.alpha_composite(self.year_and_expansion(offsets=self._add_on_offsets()))
        return card_image

    @property
    def hitter_box_dx(self) -> int:
        box_x0, _, box_x1, _ = self.BOX
        return -(box_x1 - box_x0 + self.BOX_GAP)

    @property
    def boxes_top_y(self) -> int:
        """Top of the raised boxes' header row (the hitter box has no name column cap above it)."""
        return self.BOX_PARTS[0][1] + self.BOXES_DY

    @cached_property
    def hitter_template(self) -> Image.Image:
        return self.hitter._template_image().convert('RGBA')

    @cached_property
    def pitcher_template(self) -> Image.Image:
        return self.pitcher._template_image().convert('RGBA')

    # ---------- FRAME ----------

    def _frame(self) -> Image.Image:
        """The hitter template above the raised boxes: the MLB SHOWDOWN header, the stripes and the name
        column, which now ends on the pitcher box's column cap and fades in from the top."""
        canvas = self.blank()
        cut_y = self.BOX[1] + self.BOXES_DY
        canvas.alpha_composite(self.hitter_template.crop((0, 0, self.width, cut_y)))
        column_x0, column_x1 = self.NAME_COLUMN_X
        canvas.paste((0, 0, 0, 0), (column_x0, 0, column_x1, cut_y))
        canvas.alpha_composite(self._name_column_fade(cut_y), (self.FADE_X[0], 0))
        return canvas

    def _name_column_fade(self, bottom_y: int) -> Image.Image:
        """The column's center in its native color (sampled just above the cap, so dark mode and edition
        templates keep theirs), clear at the top, FADE_NAME_OPACITY where the name begins and
        FADE_END_OPACITY where it meets the cap."""
        x0, x1 = self.FADE_X
        red, green, blue, _ = self.hitter_template.getpixel(((x0 + x1) // 2, self.BOX[1] - 1))
        name_bbox = self.name_layer.getbbox()
        name_top_y = min(name_bbox[1], bottom_y - 1) if name_bbox else bottom_y // 2
        opacity = np.interp(np.arange(bottom_y), [0, name_top_y, bottom_y - 1], [0, self.FADE_NAME_OPACITY, self.FADE_END_OPACITY])
        alpha = Image.fromarray(np.repeat((opacity * 255).astype(np.uint8)[:, None], x1 - x0, axis=1))
        column = Image.new('RGBA', alpha.size, (red, green, blue, 255))
        column.putalpha(alpha)
        return column

    def _logos(self) -> Image.Image:
        """The team logo and edition logo (Rookie Season, Postseason, ...) from their native spots, raised
        together just enough to clear the hitter box."""
        canvas = self.blank()
        if not self.hitter.image.hide_team_logo:
            logo, logo_xy = self.hitter._team_logo_image()
            canvas.alpha_composite(self.layer(logo, self.bordered_xy(self.hitter, logo_xy), logo))
        canvas = self.hitter._add_additional_logo(image=canvas)
        bbox = canvas.getbbox()
        if bbox is None:
            return canvas
        return self.shifted(canvas, 0, min(0, self.boxes_top_y - self.LOGO_GAP - bbox[3]))

    # ---------- COMMAND BOXES ----------

    def _box_mask(self) -> Image.Image:
        mask = Image.new('L', (self.width, self.height), 0)
        draw = ImageDraw.Draw(mask)
        for x0, y0, x1, y1 in self.BOX_PARTS:
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)
        return mask

    def _box(self, card: ShowdownPlayerCard, dx: int) -> Image.Image:
        """The side's native command box (from its own template, which has its result labels and command)
        with its metadata and chart, moved by (dx, BOXES_DY)."""
        box = (self.hitter_template if card is self.hitter else self.pitcher_template).copy()
        for image, color, component in (
            (*card._metadata_image(), TemplateImageComponent.METADATA),
            (*card._chart_image(), TemplateImageComponent.CHART),
        ):
            xy = self.bordered_xy(card, card.set.template_component_paste_coordinates(component, player_type=card.player_type))
            box.paste(color, xy, image)
        return self.shifted(self.clipped(box, self._box_mask()), dx, self.BOXES_DY)

    # ---------- STRIP ----------

    @property
    def strip_dy(self) -> int:
        return self.STRIP_TOP_Y - self.STRIP[1]

    @property
    def strip_bottom_y(self) -> int:
        """Bottom of the strip's visible area (the card's trim line)."""
        return self.height - self.padding

    @cached_property
    def native_strip(self) -> Image.Image:
        """The native strip's contents without its translucent band: the set/year box, bot logo and legal text."""
        x0, y0, _, _ = self.STRIP
        strip = self.hitter_template.crop(self.STRIP)
        strip.putalpha(strip.getchannel('A').point(lambda alpha: alpha if alpha > self.BAND_MAX_ALPHA else 0))
        native = self.blank()
        native.alpha_composite(strip, (x0, y0))
        native.alpha_composite(self.shifted(self.hitter._set_and_year_image(), *self.bordered_xy(self.hitter, (0, 0))))
        return native

    @cached_property
    def legal_text(self) -> Optional[Image.Image]:
        legal = self.native_strip.crop(self.LEGAL_BOX)
        bbox = legal.getbbox()
        return self.scaled(legal.crop(bbox), self.LEGAL_SCALE) if bbox else None

    @property
    def legal_xy(self) -> tuple[int, int]:
        """Right aligned with the pitcher box, centered in the strip's visible height."""
        width, height = self.legal_text.size if self.legal_text else (0, 0)
        return self.BOX[2] - width, (self.STRIP_TOP_Y + self.strip_bottom_y - height) // 2

    def _strip(self) -> Image.Image:
        """The native bottom strip under both boxes: its translucent band stretched across the card, the
        set/year box and bot logo at full size on the left, and the legal text scaled down under the
        pitcher box."""
        x0, y0, _, y1 = self.STRIP
        canvas = self.blank()
        band = self.hitter_template.crop((self.BAND_X, y0, self.BAND_X + 1, y1)).resize((self.width, y1 - y0))
        canvas.alpha_composite(band, (0, self.STRIP_TOP_Y))
        canvas.alpha_composite(self.shifted(self.native_strip.crop((x0, y0, self.LEGAL_BOX[0], y1)), x0, self.STRIP_TOP_Y))
        if self.legal_text:
            canvas.alpha_composite(self.legal_text, self.legal_xy)
        return canvas

    def _stats_row_in_strip(self) -> Image.Image:
        """The split text / stat highlights row, moved into the strip between the set box and the legal text
        (shrunk when the two sides' stats run wider than that)."""
        row = self.stats_row()
        bbox = row.getbbox()
        if bbox is None:
            return row
        row = row.crop(bbox)
        max_width = self.legal_xy[0] - self.STATS_ROW_GAP - self.STATS_ROW_X
        if row.width > max_width:
            row = self.scaled(row, max_width / row.width)
        canvas = self.blank()
        canvas.alpha_composite(row, (self.STATS_ROW_X, self.STRIP_TOP_Y + self.STATS_ROW_DY))
        return canvas

    def _add_on_offsets(self) -> dict[str, tuple[int, int]]:
        """The year text moves with the strip. The expansion logo (TD, PR), which sits where the hitter box
        now is, centers in the notch under the pitcher box's metadata, between the two boxes."""
        offsets = {'year': (0, self.strip_dy)}
        expansion = self.hitter._expansion_layer()
        if expansion:
            image, xy = expansion
            bbox = image.getbbox()
            if bbox:
                x, y = self.bordered_xy(self.hitter, xy)
                notch_x0, notch_y0, notch_x1 = self.BOX_PARTS[0][0], self.BOX_PARTS[0][3], self.BOX_PARTS[1][0]
                notch_y1 = self.BOX_PARTS[1][3]
                center_x, center_y = (notch_x0 + notch_x1) / 2, (notch_y0 + notch_y1) / 2 + self.BOXES_DY
                offsets['expansion'] = (round(center_x - (x + (bbox[0] + bbox[2]) / 2)), round(center_y - (y + (bbox[1] + bbox[3]) / 2)))
        return offsets

    # ---------- NAME COLUMN ----------

    @cached_property
    def name_layer(self) -> Image.Image:
        """The native name, raised with the column's end."""
        name_text, name_color = self.hitter._player_name_text_image()
        name_xy = self.bordered_xy(self.hitter, self.hitter.set.template_component_paste_coordinates(TemplateImageComponent.PLAYER_NAME))
        return self.shifted(self.layer(name_text, name_xy, name_color), 0, self.BOXES_DY)

    def _total_tab(self) -> Image.Image:
        """'TWO-WAY <total> PT.' on a tab across the top of the pitcher's header, filled like the cap over
        the command square so the header becomes one flat-topped block, right aligned with the CONTROL text.
        It's drawn under the boxes and tucks under the header and cap."""
        canvas = self.blank()
        header_x0, header_y0 = self.BOX_PARTS[0][:2]
        cap_x0, cap_y0 = self.BOX_PARTS[2][:2]
        tab_top_y, tab_bottom_y = cap_y0 + self.BOXES_DY, header_y0 + self.BOXES_DY
        fill = self.pitcher_template.getpixel((cap_x0 + 5, cap_y0 + 5))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((header_x0, tab_top_y, cap_x0 + self.TOTAL_TAB_TUCK, tab_bottom_y + self.TOTAL_TAB_TUCK), fill=fill)

        label_font, points_font = self.total_fonts(self.TOTAL_SCALE)
        label, points = 'TWO-WAY ', f'{self.total_points_text} PT.'
        baseline_y = tab_bottom_y - self.TOTAL_BASELINE_INSET
        points_x = self.TOTAL_RIGHT_X - points_font.getlength(points)
        draw.text((points_x - label_font.getlength(label), baseline_y), label, font=label_font, fill=self.SILVER, anchor='ls')
        draw.text((points_x, baseline_y), points, font=points_font, fill=colors.WHITE, anchor='ls')
        return canvas


class BlockLayout03(SideBySideLayout):
    """2003: side-by-side photos under the native frame, and both native command boxes side by side along
    the bottom (pitcher in the native spot, hitter left of it, cut at the card's edge), raised and cut just
    under their last result row. Under them: the year box and expansion logo (under the stats row when there
    is one), then the bot logo and legal text. The name keeps the top of the name column, with the two-way
    total level under it, above the logos sitting on the boxes."""

    BOX = (888, 1458, 1644, 2150)              # NATIVE COMMAND BOX, CUT JUST UNDER ITS LAST RESULT ROW (IT RUNS OFF THE CARD)
    BOXES_DY = -150
    BOX_GAP = 30
    LOGO_GAP = 25
    YEAR_BOX = (140, 1845, 315, 1898)          # NATIVE YEAR / SET NUMBER BOXES
    LEGAL_BOX = (140, 1945, 860, 2144)         # NATIVE LEGAL TEXT (TRANSLUCENT WHITE OVER THE PHOTO)
    LEGAL_SCALE = 0.72
    STRIP_GAP = 26                             # BETWEEN THE ITEMS IN THE STRIP
    STRIP_PADDING = 10                         # KEPT ABOVE AND BELOW THE STRIP'S CONTENT
    STRIP_ROW_GAP = 8                          # BETWEEN THE STATS ROW AND THE LOGOS ROW UNDER IT
    TOTAL_GAP = 30
    COLUMN_X = 1320                            # NAME COLUMN'S LEFT EDGE (ITS WHITE LINES), FOR LOGOS THAT CROWD IT
    COLUMN_INNER = (1383, 1572)                # THE COLUMN'S BLACK, TO THE CARD'S TRIM
    TOTAL_MARGIN = 16                          # KEPT ON EACH SIDE OF THE TOTAL IN THE COLUMN

    def render(self) -> Image.Image:
        card_image = self._photos()
        card_image.alpha_composite(self.hitter_template.crop((0, 0, self.width, self.BOX[1] + self.BOXES_DY)))
        logos = self._logos()
        card_image.alpha_composite(logos)
        for card, dx in ((self.hitter, self.hitter_box_dx), (self.pitcher, 0)):
            card_image.alpha_composite(self._box(card, dx))
        card_image.alpha_composite(self._strip())
        card_image.alpha_composite(self._name_and_total(bottom_limit=self._column_bottom_limit(logos)))
        return card_image

    @cached_property
    def hitter_template(self) -> Image.Image:
        return self.hitter._template_image().convert('RGBA')

    @property
    def trim_right(self) -> int:
        return self.width - self.padding

    @property
    def hitter_box_dx(self) -> int:
        return -(self.trim_right - self.BOX[0] + self.BOX_GAP)

    @property
    def boxes_top_y(self) -> int:
        return self.BOX[1] + self.BOXES_DY

    @property
    def boxes_bottom_y(self) -> int:
        return self.BOX[3] + self.BOXES_DY

    # ---------- LOGOS ----------

    def _logos(self) -> Image.Image:
        """The team logo (in the name column) and any edition logo, moved together to sit just above the raised
        boxes, like the team logo sits on a regular card's box. That leaves the name column the most room. Logos
        that would crowd the total under the name (ex: Super Season) slide left out of the column."""
        logos = self.blank()
        if not self.hitter.image.hide_team_logo:
            logo, logo_xy = self.hitter._team_logo_image()
            logos.alpha_composite(self.layer(logo, self.bordered_xy(self.hitter, logo_xy), logo))
        logos = self.hitter._add_additional_logo(image=logos)
        bbox = logos.getbbox()
        if bbox is None:
            return logos
        logos = self.shifted(logos, 0, self.boxes_top_y - self.LOGO_GAP - bbox[3])
        if self._column_space(self._column_bottom_limit(logos)) < self.total_image.height:
            logos = self.shifted(logos, self.COLUMN_X - self.LOGO_GAP - bbox[2], 0)
        return logos

    # ---------- COMMAND BOXES ----------

    def _box(self, card: ShowdownPlayerCard, dx: int) -> Image.Image:
        """The side's native command box (its template with its command, metadata, icons and chart), cut under
        its last result row and moved by (dx, BOXES_DY). The hitter's is cut at the card's edge too, where the
        pitcher's starts."""
        box = (self.hitter_template if card is self.hitter else card._template_image().convert('RGBA')).copy()
        for image, color, component in (
            (*card._metadata_image(), TemplateImageComponent.METADATA),
            (*card._chart_image(), TemplateImageComponent.CHART),
        ):
            xy = self.bordered_xy(card, card.set.template_component_paste_coordinates(component, player_type=card.player_type))
            box.paste(color, xy, image)
        box = card._add_icons_to_image(box)
        x0, y0, x1, y1 = self.BOX
        if card is self.hitter:
            x1 = self.trim_right
        canvas = self.blank()
        canvas.alpha_composite(box.crop((x0, y0, x1, y1)), (x0 + dx, y0 + self.BOXES_DY))
        return canvas

    # ---------- STRIP ----------

    @cached_property
    def native_bottom(self) -> Image.Image:
        """The hitter template's bottom-left pieces (year box, bot logo, legal text) with the set/year text."""
        native = self.hitter_template.copy()
        native.alpha_composite(self.shifted(self.hitter._set_and_year_image(), *self.bordered_xy(self.hitter, (0, 0))))
        return native

    def _strip(self) -> Image.Image:
        """The strip under the boxes. On the right, the bot logo then the legal text (right aligned under the
        pitcher box). On the left, the year box and expansion logo (TD, PR), under the stats row (split / stat
        highlights) when the card has one, which shrinks only when it can't fit."""
        canvas = self.blank()
        top, bottom = self.boxes_bottom_y + self.STRIP_PADDING, self.height - self.padding - self.STRIP_PADDING
        middle_y = (top + bottom) / 2

        def place_right_to_left(image: Image.Image, right_x: int) -> int:
            """Paste `image` ending at `right_x`, vertically centered; returns its left x."""
            canvas.alpha_composite(image, (right_x - image.width, round(middle_y - image.height / 2)))
            return right_x - image.width

        x = self.trim_right - self.STRIP_GAP
        legal = self.native_bottom.crop(self.LEGAL_BOX)
        if legal.getbbox():
            x = place_right_to_left(self.scaled(legal.crop(legal.getbbox()), self.LEGAL_SCALE), x) - self.STRIP_GAP
        x = place_right_to_left(self.hitter._bot_logo_img().convert('RGBA'), x) - self.STRIP_GAP
        left_x, left_width = self.YEAR_BOX[0], x - self.YEAR_BOX[0]

        items = [self.native_bottom.crop(self.YEAR_BOX)]
        expansion = self.hitter._expansion_layer()
        if expansion:
            items.append(expansion[0])
        items = [item.crop(item.getbbox()) for item in items if item.getbbox()]
        items_height = max(item.height for item in items)

        row = self.stats_row()
        if row.getbbox():
            row = row.crop(row.getbbox())
            scale = min(1.0, left_width / row.width, (bottom - top - items_height - self.STRIP_ROW_GAP) / row.height)
            row = self.scaled(row, scale) if scale < 1 else row
            group_top = round(middle_y - (row.height + self.STRIP_ROW_GAP + items_height) / 2)
            canvas.alpha_composite(row, (left_x, group_top))
            middle_y = group_top + row.height + self.STRIP_ROW_GAP + items_height / 2

        for item in items:
            canvas.alpha_composite(item, (left_x, round(middle_y - item.height / 2)))
            left_x += item.width + self.STRIP_GAP
        return canvas

    # ---------- NAME COLUMN ----------

    def _column_bottom_limit(self, logos: Image.Image) -> int:
        """How far down the name column the total can reach: the top of the logos in the column, else the boxes."""
        bbox = logos.crop((self.COLUMN_X, 0, self.width, self.boxes_top_y)).getbbox()
        return bbox[1] if bbox else self.boxes_top_y

    @cached_property
    def name_layer(self) -> tuple[Image.Image, object]:
        """The native name at the top of the column, and its color."""
        name_text, name_color = self.hitter._player_name_text_image()
        name_xy = self.bordered_xy(self.hitter, self.hitter.set.template_component_paste_coordinates(TemplateImageComponent.PLAYER_NAME))
        return self.layer(name_text, name_xy, name_color), name_color

    def _column_space(self, bottom_limit: int) -> float:
        """Room for the total between the native name and `bottom_limit`."""
        name_bbox = self.name_layer[0].getbbox()
        return bottom_limit - self.TOTAL_GAP - ((name_bbox[3] if name_bbox else 0) + self.TOTAL_GAP)

    @cached_property
    def total_image(self) -> Image.Image:
        x0, x1 = self.COLUMN_INNER
        return self.stacked_total(x1 - x0 - 2 * self.TOTAL_MARGIN, self.name_layer[1])

    def _name_and_total(self, bottom_limit: int) -> Image.Image:
        """The native name at the top of the column, with the two-way total level under it, centered between
        the name and the logo. When a long name leaves too little room, the name shrinks (from its top end)."""
        canvas, _ = self.name_layer
        canvas = canvas.copy()
        name_bbox = canvas.getbbox()
        if name_bbox is None:
            return canvas
        total = self.total_image
        shortfall = total.height - self._column_space(bottom_limit)
        if shortfall > 0:
            center_x = (name_bbox[0] + name_bbox[2]) / 2
            canvas = self.scaled_about(canvas, (center_x, name_bbox[1]), 1 - shortfall / (name_bbox[3] - name_bbox[1]))
            name_bbox = canvas.getbbox()
        x0, x1 = self.COLUMN_INNER
        middle_y = (name_bbox[3] + bottom_limit) / 2
        canvas.alpha_composite(total, (round((x0 + x1 - total.width) / 2), round(middle_y - total.height / 2)))
        return canvas
