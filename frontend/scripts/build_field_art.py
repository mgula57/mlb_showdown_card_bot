"""Builds the game field art (`public/images/games/Field 3D.webp`) from the source render
(`public/images/teams/Field 3D.jpg`, 2752x1536 on a flat dark backdrop).

- The backdrop becomes transparent (with the antialiased edge un-mixed from it), so the field sits
  on any page surface in either theme.
- The fan's far corners, which reach past the field box `GameField` lays players out in, fade out
  sideways, and the foul ground the render cuts off at its bottom edge fades out too, so wherever
  a host clips the art there's no hard line.
- The result is cropped to what's left. Prints the crop and the field box in the cropped image,
  which `ART` in `GameField.tsx` needs.

Run from the repo root: `.venv/bin/python frontend/scripts/build_field_art.py`
"""
from pathlib import Path

import numpy as np
from PIL import Image

PUBLIC = Path(__file__).resolve().parents[1] / 'public' / 'images'
SOURCE = PUBLIC / 'teams' / 'Field 3D.jpg'
OUTPUT = PUBLIC / 'games' / 'Field 3D.webp'

BACKDROP = np.array([29, 33, 40], dtype=float)
# Colour distance from the backdrop: at or under LOW is backdrop, at or over HIGH is field.
LOW, HIGH = 8.0, 40.0

# Measured on the source: the white base markers and the plate.
SECOND_Y, PLATE_X, PLATE_Y = 666, 1377, 1319
# Where `GameField` puts second and home in its 703x369 field box (percent of the box).
BOX_SECOND_Y, BOX_HOME = 18.4, (49.9, 85.4)
BOX_ASPECT = 703 / 369

# Side fade: opaque inside the box, fully gone this far out from the image edge.
SIDE_FADE_OUTER = 80
# Bottom fade over the cut-off foul ground, in source rows.
BOTTOM_FADE = (1462, 1536)


def smoothstep(t: np.ndarray) -> np.ndarray:
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def main() -> None:
    rgb = np.asarray(Image.open(SOURCE).convert('RGB')).astype(float)
    height, width, _ = rgb.shape

    # The field box in source pixels, from where second and home sit in it.
    box_h = (PLATE_Y - SECOND_Y) / ((BOX_HOME[1] - BOX_SECOND_Y) / 100)
    box_top = SECOND_Y - box_h * BOX_SECOND_Y / 100
    box_w = box_h * BOX_ASPECT
    box_left = PLATE_X - box_w * BOX_HOME[0] / 100

    distance = np.abs(rgb - BACKDROP).max(axis=2)
    alpha = smoothstep((distance - LOW) / (HIGH - LOW))
    # Un-mix the backdrop from partly covered edge pixels so they don't keep a dark fringe.
    safe = np.maximum(alpha, 1e-3)[..., None]
    rgb = np.clip((rgb - (1 - safe) * BACKDROP) / safe, 0, 255)

    xs = np.arange(width, dtype=float)
    left_fade = smoothstep((xs - SIDE_FADE_OUTER) / (box_left - SIDE_FADE_OUTER))
    right_edge = box_left + box_w
    right_fade = smoothstep(((width - SIDE_FADE_OUTER) - xs) / ((width - SIDE_FADE_OUTER) - right_edge))
    ys = np.arange(height, dtype=float)
    bottom_fade = smoothstep((BOTTOM_FADE[1] - ys) / (BOTTOM_FADE[1] - BOTTOM_FADE[0]))
    alpha = alpha * np.minimum(left_fade, right_fade)[None, :] * bottom_fade[:, None]

    rows = np.where(alpha.max(axis=1) > 0.01)[0]
    cols = np.where(alpha.max(axis=0) > 0.01)[0]
    top, bottom, left, right = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1

    rgba = np.dstack([rgb, alpha * 255]).round().astype(np.uint8)[top:bottom, left:right]
    Image.fromarray(rgba, 'RGBA').save(OUTPUT, 'WEBP', quality=88, method=6)

    print(f"wrote {OUTPUT.relative_to(PUBLIC.parent.parent)} ({OUTPUT.stat().st_size // 1024} KB)")
    print(f"ART = {{ width: {right - left}, height: {bottom - top}, "
          f"left: {box_left - left:.1f}, top: {box_top - top:.1f}, "
          f"right: {box_left + box_w - left:.1f}, bottom: {box_top + box_h - top:.1f} }}")


if __name__ == '__main__':
    main()
