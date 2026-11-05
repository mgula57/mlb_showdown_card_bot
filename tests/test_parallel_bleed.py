"""Bordered Breakout and Booster cards are their non-bordered selves plus a bleed: cut the card area
out of a bordered layer and it matches the non-bordered one.

Usage:
    python tests/test_parallel_bleed.py
"""

import numpy as np
from PIL import Image, ImageDraw

from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.core.card.sets import Set
from mlb_showdown_bot.core.card.stats.stats_period import StatsPeriod, StatsPeriodType
from mlb_showdown_bot.core.shared.team import Team

MAX_CHANGED_PIXELS = 0.001 # ANTI-ALIASING RIGHT AT THE CARD'S EDGE
CHANGED_PIXEL_THRESHOLD = 8


def seeded_noise(size: tuple[int, int], sigma: float) -> Image.Image:
    """Concrete noise is random per render, so it's fixed here to leave only the layout to differ."""
    pixels = np.random.default_rng(size[0] * size[1]).normal(128, sigma, (size[1], size[0]))
    return Image.fromarray(pixels.clip(0, 255).astype('uint8'))


def layers_for(card: ShowdownPlayerCard, size: tuple[int, int]) -> tuple[Image.Image, Image.Image]:
    """A photo with detail everywhere and a player cut, both full bleed when `size` is."""
    height, width = size[1], size[0]
    bleed = (width - card.set.card_size[0]) // 2
    rows, columns = np.mgrid[-bleed:height - bleed, -bleed:width - bleed]
    photo = np.zeros((height, width, 4), 'uint8')
    photo[..., 0], photo[..., 1], photo[..., 3] = columns % 251, rows % 241, 255
    player = Image.new('RGBA', size, (0, 0, 0, 0))
    ImageDraw.Draw(player).ellipse((500 + bleed, 420 + bleed, 1000 + bleed, 920 + bleed), fill=(9, 9, 9, 255))
    return Image.fromarray(photo), player


def changed_pixels(card: ShowdownPlayerCard, render) -> float:
    """Share of the card area that differs between the bordered and non-bordered render."""
    images = {}
    for is_bordered in [False, True]:
        card.image.is_bordered = is_bordered
        size = card.set.card_size_bordered if is_bordered else card.set.card_size
        images[is_bordered] = render(*layers_for(card, size))
    bleed = card.set.card_border_padding
    bordered = images[True].crop((bleed, bleed, images[True].width - bleed, images[True].height - bleed))
    difference = np.abs(np.array(images[False].convert('RGB')).astype(int) - np.array(bordered.convert('RGB')).astype(int))
    return float((difference.max(axis=2) > CHANGED_PIXEL_THRESHOLD).mean())


def build_card(showdown_set: Set) -> ShowdownPlayerCard:
    return ShowdownPlayerCard(
        name='TEST', year='2004', player_type='Hitter', set=showdown_set, bref_id='testpl01', team=Team.HOU,
        stats={'team_ID': 'HOU'}, stats_period=StatsPeriod(year='2004', type=StatsPeriodType.REGULAR_SEASON), build_on_init=False,
    )


def test_card_area_matches_with_and_without_a_border() -> None:
    original_noise = Image.effect_noise
    Image.effect_noise = seeded_noise
    try:
        for showdown_set in [Set._2000, Set._2002, Set._2003, Set._2004, Set.EXPANDED]:
            card = build_card(showdown_set)
            size = showdown_set.card_size
            renders = {
                'BREAKOUT': lambda background, player: card._breakout_frame_image(size=size, background=background, player=player),
                'BOOSTER': lambda background, player: card._booster_frame_image(size=size, background=background),
                'BOOSTER, NO PHOTO': lambda background, player: card._booster_frame_image(size=size),
            }
            for parallel, render in renders.items():
                changed = changed_pixels(card, render)
                assert changed <= MAX_CHANGED_PIXELS, f'{parallel} {showdown_set.value}: {changed:.2%} of the card area changed with a border'
                print(f'  ok  {parallel} {showdown_set.value} ({changed:.3%})')
    finally:
        Image.effect_noise = original_noise


if __name__ == '__main__':
    test_card_area_matches_with_and_without_a_border()
    print('all passed')
