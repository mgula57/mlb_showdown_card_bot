"""Two-way card images: one card showing a player's hitting AND pitching sides.

The hitting card owns the image and carries the pitching card in `two_way`. Each layout reuses
both cards' own render helpers (templates, metadata, chart, player images) and rearranges them:

- 2000/2001: a SPLIT card. The hitter (command, chart, photo) fills the top-left half and the
  pitcher the bottom-right, divided by a steep diagonal banner bar holding the name and total
  points. 2000 shares the 2001 layout over its plainer (no line art) team background.
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

    SUPPORTED_SETS: frozenset[Set] = frozenset([Set._2000, Set._2001, Set._2004, Set._2005])
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
        layout_class = SplitLayout0001 if self.hitter.set.is_00_01 else BlockLayout0405
        with self._render_context():
            card_image = layout_class(hitter=self.hitter, pitcher=self.pitcher, is_bordered=is_bordered).render()

        if is_bordered:
            return card_image
        padding = self.hitter.set.card_border_padding
        width, height = card_image.size
        return card_image.crop((padding, padding, width - padding, height - padding))

    @contextmanager
    def _render_context(self) -> Iterator[None]:
        """Temporary settings while composing, restored after:
        - both sides render in the bordered canvas space and prefer two-way tagged auto images.
        - the hitter's accolades (drawn on the Super Season logo) alternate with the pitcher's.
        - a multi-colored team colored parallel (ex: Team Color Blast) splits by side: the hitter's art in
          the primary color, the pitcher's in the secondary. Single color settings apply to both sides.
        """
        overrides: list[tuple[object, str, object]] = []
        for card in (self.hitter, self.pitcher):
            overrides += [(card.image, 'is_bordered', True), (card, '_is_rendering_two_way', True)]
        overrides.append((self.hitter, 'accolades', self.alternating_accolades))
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
            sections = [side.image.stat_highlights_list for side in (self.hitter, self.pitcher)]
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


class SplitLayout0001(TwoWayLayout):
    """2000/2001: hitter top-left, pitcher bottom-right, split by a diagonal 2001-style banner bar."""

    UP = 150                                # hitter block rises into the removed header space
    SEAM_START, SEAM_END_Y = 1330, 820      # divider y at the left / right card edges
    CONTROL_BANNER_TOP_Y, CONTROL_L_X = 278, 1282   # 2001-Pitcher template: CONTROL banner top and the L's middle
    PITCHER_BLOCK_Y = 850                   # pitcher command block drops this far below its native spot (clears the divider)
    CHART_SCALE = 0.84
    BAR_EDGE, BAR_CENTER = 16, 90           # divider: brushed silver edge thickness (each side) and black center, from the 2000 name container
    BAR_DIVIDER = (205, 205, 205)           # tick between the name and the total, and the TWO-WAY label (silver, like the bar edges)
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
    OBLIQUE = 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique'
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


class BlockLayout0405(TwoWayLayout):
    """2004/2005: side-by-side photos, then one name band and a band block per side."""

    ROW = 68                                   # band row pitch
    HITTER_BLOCK_Y, PITCHER_BLOCK_Y = 1563, 1767
    NATIVE_META_Y = 1770                       # native top of the metadata band
    SEAM_TOP_X, SEAM_BOTTOM_X = 960, 640
    HITTER_PHOTO_DX, PITCHER_PHOTO_DX = -363, 356   # each photo slides toward its own half, clearing the seam
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

    # ---------- PHOTOS ----------

    def _side_images(self, card: ShowdownPlayerCard) -> tuple[Image.Image, PlayerImageGroups]:
        """The side's background and player image layers, framed exactly like the side's own card. Bordered
        cards build them with the bleed, so the photos run into the border while the card area stays the same.
        Off-center players get a dedicated (TwoWay) image in the library."""
        card.image.is_bordered = self.is_bordered
        try:
            return card._background_image().convert('RGBA'), self.grouped_layers(card._player_image_layers())
        finally:
            card.image.is_bordered = True

    def _half_mask(self, is_hitter: bool) -> Image.Image:
        """The hitter's half left of the seam, or the pitcher's half right of it."""
        mask = Image.new('L', (self.width, self.height), 0 if is_hitter else 255)
        ImageDraw.Draw(mask).polygon([(0, 0), (self.SEAM_TOP_X, 0), (self.SEAM_BOTTOM_X, self.height), (0, self.height)], fill=255 if is_hitter else 0)
        return mask

    def _photos(self) -> Image.Image:
        """Each side's background and photo slide toward its own half, while its card art (parallels,
        edition art) stays put so both halves line up into one finish. Every layer is clipped to its half."""
        canvas = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
        side_size, offset = (self.hitter.set.card_size_bordered, 0) if self.is_bordered else (self.hitter.set.card_size, self.padding)
        sides = []
        for card, dx in ((self.hitter, self.HITTER_PHOTO_DX), (self.pitcher, self.PITCHER_PHOTO_DX)):
            background, groups = self._side_images(card)
            sides.append((dx, self._half_mask(card is self.hitter), background, groups))

        def place(image: Image.Image, dx: int, mask: Image.Image) -> None:
            canvas.alpha_composite(self.clipped(self.shifted(image, offset + dx, offset), mask))

        for dx, mask, background, _ in sides:
            place(background, dx, mask)
        for group, moves in (('photo_background', True), ('art_under', False), ('photo', True), ('art_over', False)):
            for dx, mask, _, groups in sides:
                place(self.composite(getattr(groups, group), side_size), dx if moves else 0, mask)

        draw = ImageDraw.Draw(canvas)
        draw.line([(self.SEAM_TOP_X, 0), (self.SEAM_BOTTOM_X, self.height)], fill=(10, 10, 10), width=22)
        draw.line([(self.SEAM_TOP_X + 14, 0), (self.SEAM_BOTTOM_X + 14, self.height)], fill=(240, 240, 240), width=5)

        # HOLIDAY FRAME OVER BOTH PHOTOS AND THE SEAM, UNDER THE BANDS (LIKE A REGULAR CARD'S TEMPLATE)
        holiday_frame = self.holiday_frame()
        if holiday_frame:
            canvas.alpha_composite(holiday_frame)
        return canvas

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
