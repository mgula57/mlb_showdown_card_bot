"""
Release Builder sharing: the 1200x630 share image shown when a release link is pasted into a chat
or social app, and the Open Graph tags that point at it. Chat apps don't run JavaScript, so the
tags are written into the served `index.html` for release paths (see `ReleaseOpenGraph`).
"""

import hashlib
import html
import io
import os
import re
import tempfile
import threading
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ..database.postgres_db import PostgresDB
from .release_images import ReleaseImageStorage

_FONTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'card', 'fonts')

# Sets whose printed logo is red; the rest are navy (frontend `SetBadge`)
_RED_SETS = {'2000', '2001', 'CLASSIC'}


class ReleaseShareImage:
    """Renders a published release's share image (cover cards fanned beside its name, set and counts,
    over the silver card-back field) and stores it with the release's images."""

    WIDTH, HEIGHT = 1200, 630
    # Bump to re-render every share image after a layout change
    VERSION = 2

    SILVER = (226, 230, 234)
    STRIPE = (205, 212, 221)
    NAVY = (26, 59, 95)
    RED = (179, 52, 43)
    INK = (16, 19, 23)
    INK_SECONDARY = (62, 68, 76)
    WHITE = (255, 255, 255)
    CARD_EDGE = (244, 245, 247)

    BAR_HEIGHT = 150
    # Rounded like the printed cards (and the fan on the release tile)
    CARD_RADIUS = 18
    TEXT_LEFT = 64
    TEXT_WIDTH = 540

    def __init__(self, db: PostgresDB) -> None:
        self.db = db
        self.storage = ReleaseImageStorage()

    @staticmethod
    def _font(file_name: str, size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(os.path.join(_FONTS_DIR, file_name), size)

    def _display(self, size: int) -> ImageFont.FreeTypeFont:
        return self._font('HelveticaNeueCondensedHeavyOblique.otf', size)

    def _bold(self, size: int) -> ImageFont.FreeTypeFont:
        return self._font('HelveticaNeueCondensedBold.ttf', size)

    def refresh(self, release_id: str, site_host: str) -> Optional[str]:
        """Render and store the share image if its inputs changed. Returns the stored path (None if
        the release isn't published). The old image is deleted once the new one is recorded."""
        tile = self.db.get_public_release_tile(release_id)
        if tile is None:
            return None
        card_paths = [image['storage_path'] for image in tile.get('preview_images') or [] if image.get('storage_path')][:3]
        lines = self._lines(tile, site_host)
        digest = hashlib.sha1(repr((self.VERSION, lines, card_paths)).encode()).hexdigest()[:16]
        path = f"{ReleaseImageStorage.folder(release_id)}/share/{digest}.jpg"
        if tile.get('share_image_path') == path:
            return path

        image = self.render(lines, [self._download(card_path) for card_path in card_paths])
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as file:
            image.save(file, format='JPEG', quality=88)
            local_path = file.name
        try:
            self.storage.upload(local_path, path)
        finally:
            os.remove(local_path)
        previous = self.db.set_release_share_image(release_id, path)
        if previous and previous != path:
            self.storage.delete([previous])
        return path

    @staticmethod
    def _lines(tile: dict, site_host: str) -> dict:
        """The text on the image: everything that, when it changes, needs a new render."""
        published = [edition for edition in tile.get('editions') or [] if edition.get('is_published')]
        cards = sum(edition.get('card_count') or 0 for edition in published)
        return {
            'name': tile['name'],
            'sets': sorted(tile.get('showdown_sets') or [])[:3],
            'counts': f"{cards} card{'' if cards == 1 else 's'} · {len(published)} edition{'' if len(published) == 1 else 's'}",
            'creator': f"by {tile['creator_username']}" if tile.get('creator_username') else '',
            'link': f"{site_host}/r/{tile['slug']}",
        }

    def _download(self, storage_path: str) -> Optional[Image.Image]:
        try:
            response = requests.get(ReleaseImageStorage.public_url(storage_path), timeout=15)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert('RGBA')
        except Exception:
            # A missing card leaves a gap in the fan rather than failing the publish
            traceback.print_exc()
            return None

    def render(self, lines: dict, cards: list[Optional[Image.Image]]) -> Image.Image:
        image = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.SILVER)
        draw = ImageDraw.Draw(image)
        # Card-back pinstripes
        for x in range(0, self.WIDTH, 30):
            draw.rectangle([x, 0, x + 2, self.HEIGHT], fill=self.STRIPE)

        # Navy bar with the red edge along the bottom
        bar_top = self.HEIGHT - self.BAR_HEIGHT
        draw.rectangle([0, bar_top - 6, self.WIDTH, bar_top], fill=self.RED)
        draw.rectangle([0, bar_top, self.WIDTH, self.HEIGHT], fill=self.NAVY)

        self._draw_sets(draw, lines['sets'])
        y = 128
        draw.text((self.TEXT_LEFT, y), 'A SHOWDOWN BOT RELEASE', font=self._bold(26), fill=self.INK_SECONDARY)
        y += 44
        name_font, name_lines = self._fit_name(lines['name'].upper())
        for line in name_lines:
            draw.text((self.TEXT_LEFT, y), line, font=name_font, fill=self.INK)
            y += int(name_font.size * 0.95)
        draw.text((self.TEXT_LEFT, y + 18), lines['counts'], font=self._bold(32), fill=self.INK_SECONDARY)

        # Byline over the link, both kept left of the card fan
        link_y = bar_top + 84 if lines['creator'] else bar_top + (self.BAR_HEIGHT - 28) // 2
        if lines['creator']:
            draw.text((self.TEXT_LEFT, bar_top + 30), lines['creator'].upper(), font=self._display(40), fill=self.WHITE)
        draw.text((self.TEXT_LEFT, link_y), lines['link'], font=self._bold(28), fill=(200, 212, 226))

        self._draw_fan(image, [card for card in cards if card is not None])
        return image

    def _draw_sets(self, draw: ImageDraw.ImageDraw, sets: list[str]) -> None:
        x = self.TEXT_LEFT
        font = self._display(44)
        for showdown_set in sets:
            label = showdown_set.upper()
            fill = self.RED if label in _RED_SETS else self.NAVY
            draw.text((x, 52), label, font=font, fill=fill, stroke_width=3, stroke_fill=self.WHITE)
            x += int(draw.textlength(label, font=font)) + 24

    def _fit_name(self, name: str) -> tuple[ImageFont.FreeTypeFont, list[str]]:
        """The largest display size at which the name fits the text column: two lines at headline
        sizes, three at the smallest, then cut with an ellipsis."""
        for size in range(104, 46, -6):
            font = self._display(size)
            lines = self._wrap(name, font)
            if len(lines) <= (2 if size > 52 else 3) and all(font.getlength(line) <= self.TEXT_WIDTH for line in lines):
                return font, lines
        font = self._display(46)
        lines = self._wrap(name, font)
        if len(lines) > 3:
            last = lines[2]
            while last and font.getlength(f"{last}…") > self.TEXT_WIDTH:
                last = last.rsplit(' ', 1)[0] if ' ' in last else last[:-1]
            lines = lines[:2] + [f"{last}…"]
        return font, lines

    def _wrap(self, text: str, font: ImageFont.FreeTypeFont) -> list[str]:
        lines, current = [], ''
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if current and font.getlength(candidate) > self.TEXT_WIDTH:
                lines.append(current)
                current = word
            else:
                current = candidate
        return lines + ([current] if current else [])

    @staticmethod
    def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
        return mask

    def _draw_fan(self, image: Image.Image, cards: list[Image.Image]) -> None:
        """Up to three cards, the first in front: the same fan as the release tile."""
        if not cards:
            return
        card_height = 400
        center_x, bottom = 925, self.HEIGHT - 70
        # (x offset, rotation) back to front, so the first card lands on top
        placements = {1: [(0, 0)], 2: [(-60, 8), (60, -8)], 3: [(-105, 10), (105, -10), (0, 0)]}[len(cards)]
        order = list(reversed(cards)) if len(cards) > 1 else cards
        for card, (offset, rotation) in zip(order, placements):
            width = int(card.width * card_height / card.height)
            framed = Image.new('RGBA', (width + 12, card_height + 12), self.CARD_EDGE + (255,))
            # The card inside the edge, both rounded, the inner corner following the outer one
            framed.paste(card.resize((width, card_height), Image.LANCZOS), (6, 6), self._rounded_mask((width, card_height), self.CARD_RADIUS - 6))
            framed.putalpha(self._rounded_mask(framed.size, self.CARD_RADIUS))
            rotated = framed.rotate(rotation, expand=True, resample=Image.BICUBIC)
            shadow = Image.new('RGBA', rotated.size, (0, 0, 0, 0))
            shadow.putalpha(rotated.getchannel('A').point(lambda a: int(a * 0.35)))
            shadow = shadow.filter(ImageFilter.GaussianBlur(10))
            x = center_x + offset - rotated.width // 2
            y = bottom - rotated.height
            image.paste(shadow, (x + 4, y + 12), shadow)
            image.paste(rotated, (x, y), rotated)


class ReleaseOpenGraph:
    """Link-preview tags for release pages (`/r/<slug>...` and `/release-builder/<id>...`), filled
    into the app's `index.html`. Lookups are cached per release, and a published release with no
    share image yet gets one rendered in the background for the next preview."""

    PATH_PATTERN = re.compile(
        r'^(?:r/(?P<slug>[^/?#]+)|release-builder/(?P<id>[0-9a-fA-F-]{36}))'
        r'(?:/(?P<edition>[^/?#]+)(?:/(?P<card>[^/?#]+))?)?/?$'
    )
    CACHE_TTL = timedelta(minutes=5)
    _cache: dict[str, tuple[Optional[dict], datetime]] = {}
    _rendering: set[str] = set()
    _lock = threading.Lock()

    @classmethod
    def page(cls, path: str, index_html: str, base_url: str) -> Optional[str]:
        """`index_html` with this release's tags, or None for any other path (or a release that
        isn't published), which is then served as is."""
        match = cls.PATH_PATTERN.match(path)
        if not match:
            return None
        tile = cls._tile(match.group('slug'), match.group('id'))
        if tile is None:
            return None
        site_host = base_url.split('://', 1)[-1].rstrip('/')
        if not tile.get('share_image_path'):
            cls._render_in_background(tile['id'], site_host)
        # A card link previews the card itself; one that no longer resolves falls back to the release
        card = cls._card(tile, match.group('edition'), match.group('card')) if match.group('card') else None
        if card:
            return cls.inject(index_html, cls.card_tags(tile, card, match.group('edition'), base_url.rstrip('/')))
        return cls.inject(index_html, cls.tags(tile, base_url.rstrip('/')))

    @classmethod
    def _tile(cls, slug: Optional[str], release_id: Optional[str]) -> Optional[dict]:
        key = slug or release_id
        now = datetime.now(timezone.utc)
        with cls._lock:
            cached = cls._cache.get(key)
        if cached and now - cached[1] < cls.CACHE_TTL:
            return cached[0]
        with PostgresDB() as db:
            release_id = release_id or db.get_release_id_by_slug(slug)
            tile = db.get_public_release_tile(release_id) if release_id else None
        with cls._lock:
            cls._cache[key] = (tile, now)
        return tile

    @classmethod
    def _card(cls, tile: dict, edition_slug: str, card_ref: str) -> Optional[dict]:
        key = f"card:{tile['id']}/{edition_slug}/{card_ref}"
        now = datetime.now(timezone.utc)
        with cls._lock:
            cached = cls._cache.get(key)
        if cached and now - cached[1] < cls.CACHE_TTL:
            return cached[0]
        with PostgresDB() as db:
            card = db.get_public_release_card(tile['id'], edition_slug, card_ref)
        with cls._lock:
            cls._cache[key] = (card, now)
        return card

    @classmethod
    def _render_in_background(cls, release_id: str, site_host: str) -> None:
        with cls._lock:
            if release_id in cls._rendering:
                return
            cls._rendering.add(release_id)

        def run() -> None:
            try:
                with PostgresDB() as db:
                    ReleaseShareImage(db).refresh(release_id, site_host)
                with cls._lock:
                    # The next preview picks up the new image
                    for key in [key for key, (tile, _) in cls._cache.items() if tile and tile.get('id') == release_id]:
                        del cls._cache[key]
            except Exception:
                traceback.print_exc()
            finally:
                with cls._lock:
                    cls._rendering.discard(release_id)

        threading.Thread(target=run, name=f'release-share-{release_id[:8]}', daemon=True).start()

    @classmethod
    def card_tags(cls, tile: dict, card: dict, edition_slug: str, base_url: str) -> str:
        """Tags for one card's link: its name and number, with the card's own render as the image."""
        number = f" #{card['card_number']}" if card.get('card_number') is not None else ''
        byline = f" by {tile['creator_username']}" if tile.get('creator_username') else ''
        image_path = card.get('storage_path') or tile.get('share_image_path')
        return cls._tag_lines(
            title=f"{card.get('name') or 'Card'} · {tile['name']}{number}",
            description=f"From the {card['edition_name']} edition of {tile['name']}, a custom MLB Showdown set{byline}.",
            url=f"{base_url}/r/{tile['slug']}/{edition_slug}/{card['id']}",
            image_url=ReleaseImageStorage.public_url(image_path) if image_path else None,
            # The card render is portrait; only the share image has a known size
            image_size=None if card.get('storage_path') else (ReleaseShareImage.WIDTH, ReleaseShareImage.HEIGHT),
        )

    @staticmethod
    def tags(tile: dict, base_url: str) -> str:
        published = [edition for edition in tile.get('editions') or [] if edition.get('is_published')]
        cards = sum(edition.get('card_count') or 0 for edition in published)
        title = f"{tile['name']} · {cards} card{'' if cards == 1 else 's'}"
        sets = ', '.join(sorted(tile.get('showdown_sets') or []))
        byline = f" by {tile['creator_username']}" if tile.get('creator_username') else ''
        description = (tile.get('description') or '').strip() or f"A custom {sets + ' ' if sets else ''}MLB Showdown set{byline}."
        description += f" {len(published)} edition{'' if len(published) == 1 else 's'}. Browse it or build a team from it."
        image_path = tile.get('share_image_path')
        return ReleaseOpenGraph._tag_lines(
            title=title, description=description, url=f"{base_url}/r/{tile['slug']}",
            image_url=ReleaseImageStorage.public_url(image_path) if image_path else None,
            image_size=(ReleaseShareImage.WIDTH, ReleaseShareImage.HEIGHT),
        )

    @staticmethod
    def _tag_lines(title: str, description: str, url: str, image_url: Optional[str], image_size: Optional[tuple[int, int]]) -> str:
        meta = {
            'og:type': 'website',
            'og:site_name': 'Showdown Bot',
            'og:title': title,
            'og:description': description,
            'og:url': url,
            'og:image': image_url,
            'og:image:width': str(image_size[0]) if image_url and image_size else None,
            'og:image:height': str(image_size[1]) if image_url and image_size else None,
            'twitter:card': 'summary_large_image' if image_url else 'summary',
        }
        lines = [f"<title>{html.escape(title)} | Showdown Bot</title>", f'<meta name="description" content="{html.escape(description)}" />']
        lines += [
            f'<meta {"name" if key.startswith("twitter:") else "property"}="{key}" content="{html.escape(value)}" />'
            for key, value in meta.items() if value
        ]
        lines.append(f'<link rel="canonical" href="{html.escape(url)}" />')
        return '\n    '.join(lines)

    @staticmethod
    def inject(index_html: str, tags: str) -> str:
        """Swap the page's default title and description for the release's tags."""
        page = re.sub(r'<title>.*?</title>', '', index_html, count=1, flags=re.S)
        page = re.sub(r'<meta\s+name="description"[^>]*>', '', page, count=1)
        return page.replace('</head>', f"    {tags}\n  </head>", 1)
