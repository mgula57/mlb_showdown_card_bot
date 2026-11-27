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
from typing import TYPE_CHECKING, Iterator, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .images import ImageColoring
from .sets import Set, TemplateImageComponent
from .utils import colors

if TYPE_CHECKING:
    from .showdown_player_card import ShowdownPlayerCard


class TwoWayCardImage:
    """Renders the image for a two-way card, choosing the layout for the card's set."""

    SUPPORTED_SETS: frozenset[Set] = frozenset([Set._2000, Set._2001, Set._2004, Set._2005])

    def __init__(self, hitter: ShowdownPlayerCard, pitcher: ShowdownPlayerCard) -> None:
        self.hitter = hitter
        self.pitcher = pitcher

    @classmethod
    def supports(cls, set: Set) -> bool:
        """True when the set has a two-way layout."""
        return set in cls.SUPPORTED_SETS

    def render(self) -> Image.Image:
        """Compose the two-way card.

        Returns:
          Card image at the hitter card's canvas size (bordered or regular), ready for final crop.
        """
        is_bordered = self.hitter.image.is_bordered
        layout_class = SplitLayout0001 if self.hitter.set.is_00_01 else BlockLayout0405
        with self._render_context():
            card_image = layout_class(hitter=self.hitter, pitcher=self.pitcher).render()

        if is_bordered:
            return card_image
        padding = self.hitter.set.card_border_padding
        width, height = card_image.size
        return card_image.crop((padding, padding, width - padding, height - padding))

    @contextmanager
    def _render_context(self) -> Iterator[None]:
        """While composing: both sides render in the bordered canvas space and prefer two-way tagged
        auto images. Each card's settings are restored after."""
        originals = [(card, card.image.is_bordered) for card in (self.hitter, self.pitcher)]
        for card, _ in originals:
            card.image.is_bordered = True
            card._is_rendering_two_way = True
        try:
            yield
        finally:
            for card, is_bordered in originals:
                card.image.is_bordered = is_bordered
                card._is_rendering_two_way = False


class TwoWayLayout:
    """Shared canvas helpers for the per-set two-way layouts."""

    def __init__(self, hitter: ShowdownPlayerCard, pitcher: ShowdownPlayerCard) -> None:
        self.hitter = hitter
        self.pitcher = pitcher
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

    @property
    def border_color(self) -> str:
        return colors.BLACK if self.hitter.image.is_dark_mode else colors.WHITE

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
    BAR_DIVIDER = (205, 205, 205)           # tick between the name and the total
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

    def render(self) -> Image.Image:
        self.angle = math.degrees(math.atan2(self.SEAM_END_Y - self.SEAM_START, self.width))
        card_image = self._backgrounds()
        card_image.alpha_composite(self._hitter_photo())
        card_image.alpha_composite(self._divider_bar())
        card_image.alpha_composite(self._pitcher_photo())
        card_image.alpha_composite(self._disclaimer_and_logo())
        card_image.alpha_composite(self._hitter_block())
        card_image.alpha_composite(self._pitcher_block())
        set_image = self.hitter._set_and_year_image()
        card_image.alpha_composite(self.shifted(set_image, *self.bordered_xy(self.hitter, (0, 0))))
        return card_image

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
        top = self.hitter._background_image(include_2000_name_container=False).convert('RGBA')
        with self.secondary_colored(self.pitcher):
            bottom = self.pitcher._background_image(include_2000_name_container=False).convert('RGBA')
            if self.hitter.set == Set._2001:
                bottom.alpha_composite(self._pitcher_half_logo())
        top.paste(bottom, (0, 0), self.half_mask(below=True))
        return top

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

    def _hitter_photo(self) -> Image.Image:
        """Hitter tucked behind the divider (clipped to the top half)."""
        photo = self._player_layer(self.hitter, self.HITTER_PHOTO_XY)
        return Image.composite(photo, self.blank(), self.half_mask(below=False))

    def _pitcher_photo(self) -> Image.Image:
        """Pitcher in the bottom half, cap breaking just over the divider."""
        return self._player_layer(self.pitcher, self.PITCHER_PHOTO_XY)

    def _player_layer(self, card: ShowdownPlayerCard, xy: tuple[int, int]) -> Image.Image:
        """The side's player cutout layer, framed exactly as on its regular card, scaled by PHOTO_SCALE
        and pasted with its canvas origin at `xy`, plus a white outer glow.

        Every card gets the same transform, so placement only depends on how the image is framed for
        its regular card. Off-center or cropped photos get a dedicated (TwoWay) auto image instead.
        """
        original_glow = card.image.glow_multiplier
        card.image.glow_multiplier = 0  # RAW CUTOUT; THE GLOW IS ADDED AFTER SCALING
        try:
            canvas = self.blank()
            for image, layer_xy in card._player_image_layers(include_2000_containers=False):
                canvas.paste(image, layer_xy, image)
        finally:
            card.image.glow_multiplier = original_glow
        return self._with_glow(card, self.shifted(self.scaled(canvas, self.PHOTO_SCALE), *xy))

    def _with_glow(self, card: ShowdownPlayerCard, layer: Image.Image) -> Image.Image:
        """The same white outer glow a regular 00/01 cutout gets (set glow radius x the card's glow multiplier)."""
        radius = int(card.set.player_image_glow_radius * card.image.glow_multiplier)
        if radius <= 0:
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

        name = self.hitter.name_for_visuals.upper()
        total = f"TWO-WAY {self.total_points_text} pt."
        total_font = self.font(self.OBLIQUE, 50)
        name_x, end_x, gap = along(600), along(self.width - self.padding - 20), 55
        name_size = 62
        name_font = self.font('Futura Black', name_size)
        while name_size > 36 and name_x + name_font.getlength(name) + gap + total_font.getlength(total) > end_x:
            name_size -= 2
            name_font = self.font('Futura Black', name_size)

        draw.text((name_x, middle_y), name, font=name_font, fill=colors.WHITE, anchor='lm')
        total_x = name_x + name_font.getlength(name) + gap
        draw.rectangle((total_x - 30, self.BAR_EDGE + 8, total_x - 24, self.BAR_EDGE + self.BAR_CENTER - 8), fill=self.BAR_DIVIDER)
        draw.text((total_x, middle_y), total, font=total_font, fill=colors.WHITE, anchor='lm')

        bar = bar.rotate(-self.angle, expand=True, resample=Image.Resampling.BICUBIC)
        mid_x, mid_y = self.width // 2, int(self.seam_y(self.width / 2))
        return self.shifted(bar, mid_x - bar.width // 2, mid_y - bar.height // 2)

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

    def _disclaimer_and_logo(self) -> Image.Image:
        """Disclaimer moves to the bottom-right, next to the bot logo."""
        canvas = self.blank()
        logo = self.hitter._bot_logo_img()
        logo_x, logo_y = self.bordered_xy(self.hitter, self.hitter.set.template_component_paste_coordinates(TemplateImageComponent.BOT_LOGO))
        disclaimer = self.template('2001-Hitter').crop((380, 2000, 1190, 2160))
        canvas.alpha_composite(disclaimer, (logo_x - 20 - disclaimer.width, 1995))
        canvas.paste(logo, (logo_x, logo_y), logo)
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
        panel = self._chart_panel(self.hitter, self.hitter._template_image(), (1155, 1375, 1505, 1925))
        canvas.alpha_composite(panel, (self.CHART_EDGE_MARGIN, 690 - self.UP))
        return canvas

    def _position_bars(self) -> Image.Image:
        """The hitter's native position/points bars with their native text, moved to the left side."""
        sizing = '-'.join('LARGE' if len(position) > 4 else 'SMALL' for position, _ in self.hitter.positions_and_defense_img_order)
        bars = self.blank()
        bars.alpha_composite(self.template(f'0001-Hitter-{sizing}'), (self.padding, self.padding))
        metadata, color = self.hitter._metadata_image(include_speed_and_hand=False)
        bars.alpha_composite(self.layer(metadata, (self.padding, self.padding), color))
        bars_top = self.template(f'0001-Hitter-{sizing}').getbbox()[1] + self.padding
        mid_row = bars.split()[-1].crop((0, bars_top + self.POSITION_BAR_MID_OFFSET, self.width, bars_top + self.POSITION_BAR_MID_OFFSET + 1))
        position_bar_left = mid_row.getbbox()[0]
        bars_target_top = self.HITTERBOX_Y + self.HITTERBOX_BOTTOM_Y + self.BARS_GAP
        return self.shifted(bars, self.HITTERBOX_BALL_LEFT_X - position_bar_left, bars_target_top - bars_top)

    # ---------- PITCHER (BOTTOM-RIGHT) ----------

    def _pitcher_block(self) -> Image.Image:
        """The pitcher's native command block and metadata, lowered, plus its chart."""
        canvas = self.blank()
        template = self.pitcher._template_image().convert('RGBA')
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
    # BADGE TEMPLATE, ITS NATIVE (REGULAR CARD) POSITION ON THE BORDERED CANVAS, AND THE NATIVE MIDDLE Y. KEYED BY is_pitcher
    BADGES: dict[bool, tuple[str, tuple[int, int], int]] = {
        False: ('0405-ONBASE', (123, 1635), 1728),
        True: ('0405-CONTROL', (126, 1605), 1705),
    }
    BADGE_DX = -10
    CONDENSED = 'Helvetica Neue 77 Bold Condensed'

    def render(self) -> Image.Image:
        self.name_band_dy = self.HITTER_BLOCK_Y - self.NATIVE_META_Y
        card_image = self._photos()
        card_image.alpha_composite(self._bands())
        card_image.alpha_composite(self._text())
        return card_image

    # ---------- PHOTOS ----------

    def _photo(self, card: ShowdownPlayerCard) -> Image.Image:
        """The side's regular full-bleed photo, built at the regular card size so it's framed exactly
        like the side's own card. Off-center players get a dedicated (TwoWay) image in the library."""
        card.image.is_bordered = False
        try:
            photo = card._background_image().convert('RGBA')
            for image, xy in card._player_image_layers():
                photo.paste(image, xy, image)
        finally:
            card.image.is_bordered = True
        return photo

    def _photos(self) -> Image.Image:
        canvas = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
        for card, dx, is_hitter in ((self.pitcher, self.PITCHER_PHOTO_DX, False), (self.hitter, self.HITTER_PHOTO_DX, True)):
            layer = self.shifted(self._photo(card), self.padding + dx, self.padding)
            if is_hitter:
                mask = Image.new('L', (self.width, self.height), 0)
                ImageDraw.Draw(mask).polygon([(0, 0), (self.SEAM_TOP_X, 0), (self.SEAM_BOTTOM_X, self.height), (0, self.height)], fill=255)
                layer = Image.composite(layer, self.blank(), mask)
            canvas.alpha_composite(layer)

        draw = ImageDraw.Draw(canvas)
        draw.line([(self.SEAM_TOP_X, 0), (self.SEAM_BOTTOM_X, self.height)], fill=(10, 10, 10), width=22)
        draw.line([(self.SEAM_TOP_X + 14, 0), (self.SEAM_BOTTOM_X + 14, self.height)], fill=(240, 240, 240), width=5)

        # REGULAR BORDERED CARDS KEEP THE PHOTO INSIDE THE BORDER
        if self.hitter.image.is_bordered:
            frame = Image.new('RGBA', (self.width, self.height), self.border_color)
            ImageDraw.Draw(frame).rectangle((self.padding, self.padding, self.width - self.padding - 1, self.height - self.padding - 1), fill=(0, 0, 0, 0))
            canvas.alpha_composite(frame)
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
        bottom_y = self.PITCHER_BLOCK_Y + 3 * self.ROW
        canvas.alpha_composite(hitter_template.crop((0, bottom_y, self.width, self.height)), (0, bottom_y))
        ImageDraw.Draw(canvas).rectangle((0, self.PITCHER_BLOCK_Y - 3, self.width, self.PITCHER_BLOCK_Y + 6), fill=(0, 0, 0))

        # COMMAND BADGES (0405-ONBASE / 0405-CONTROL) WITH THE SIDE'S COMMAND NUMBER, CENTERED ON THEIR BLOCK
        for card, block_y in ((self.hitter, self.HITTER_BLOCK_Y), (self.pitcher, self.PITCHER_BLOCK_Y)):
            badge_name, (native_x, native_y), native_middle_y = self.BADGES[card.is_pitcher]
            dx, dy = self.BADGE_DX, block_y + 3 * self.ROW // 2 - native_middle_y
            canvas.alpha_composite(self.template(badge_name), (native_x + dx, native_y + dy))
            player_type = 'Pitcher' if card.is_pitcher else 'Hitter'
            command = self.template(f'{card.set.template_year}-{player_type}-{card.chart.command}')
            canvas.alpha_composite(self.shifted(command, self.padding + dx, self.padding + dy))
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
        if not self.hitter.image.hide_team_logo:
            logo, logo_xy = self.hitter._team_logo_image()
            canvas.alpha_composite(self.shifted(self.layer(logo, self.bordered_xy(self.hitter, logo_xy), logo), 0, self.name_band_dy))

        # TOTAL POINTS AFTER THE NAME
        draw = ImageDraw.Draw(canvas)
        label_font, total_font = self.font(self.CONDENSED, 34), self.font(self.CONDENSED, 58)
        total_y = 1655 + self.name_band_dy + 62
        label_x = name_bbox[2] + name_dx + 40
        draw.text((label_x, total_y), 'TWO-WAY', font=label_font, fill=(225, 225, 225), anchor='lm')
        draw.text((label_x + label_font.getlength('TWO-WAY') + 14, total_y), f'{self.total_points_text} PT.', font=total_font, fill=colors.WHITE, anchor='lm')

        # EACH SIDE'S METADATA + ICONS IN ITS OWN BLOCK
        for card, block_y in ((self.hitter, self.HITTER_BLOCK_Y), (self.pitcher, self.PITCHER_BLOCK_Y)):
            dy = block_y - self.NATIVE_META_Y
            metadata, color = card._metadata_image()
            metadata_xy = self.bordered_xy(card, card.set.template_component_paste_coordinates(TemplateImageComponent.METADATA))
            canvas.alpha_composite(self.shifted(self.layer(metadata, metadata_xy, color), 0, dy))
            canvas.alpha_composite(self.shifted(card._add_icons_to_image(self.blank()), 0, dy))

        set_image = self.hitter._set_and_year_image()
        canvas.alpha_composite(self.shifted(set_image, *self.bordered_xy(self.hitter, (0, 0))))

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
