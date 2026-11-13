"""Render a one-slide (1080x1350) dark-mode "what's new" graphic for a release, for socials.

Content comes from a JSON file (see the keys `ReleaseNotesSocial.context` reads); the screenshot
is any PNG/JPEG of the app, shown bleeding off the sheet's top-right corner. Writes
`release_notes.html` and `release_notes_1.png` to the output folder.

    .venv/bin/python .claude/skills/patch-notes/scripts/release_social.py \
        --content notes.json --screenshot shot.png --out-dir out/
"""

import argparse
import json
from io import BytesIO
from pathlib import Path

from PIL import Image

from mlb_showdown_bot.core.simulation.social_report import _REPO_ROOT, SocialSheetReport

_DARK_LOGO_PATH = _REPO_ROOT / "frontend" / "public" / "images" / "logos" / "logo-dark.png"
# EMBEDDED AT 2x ITS ~640px DISPLAY WIDTH, CROPPED TO THE TOP OF THE APP.
_ART_WIDTH = 1000
_CARD_WIDTH = 720
_SCREENSHOT_WIDTH = 1600
_SCREENSHOT_MAX_HEIGHT = 1400


class ReleaseNotesSocial(SocialSheetReport):
    SHEET_COUNT = 1
    TEMPLATE_NAME = "release_notes_social.html.j2"

    def __init__(self, content: dict, screenshot_path: Path | None) -> None:
        super().__init__()
        self.content = content
        self.screenshot_path = screenshot_path

    def _screenshot_src(self) -> str:
        if not self.screenshot_path:
            return ""
        with Image.open(self.screenshot_path) as image:
            image = image.convert("RGB")
            scale = _SCREENSHOT_WIDTH / image.width
            image = image.resize((_SCREENSHOT_WIDTH, round(image.height * scale)), Image.Resampling.LANCZOS)
            image = image.crop((0, 0, _SCREENSHOT_WIDTH, min(image.height, _SCREENSHOT_MAX_HEIGHT)))
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=95)
        return self.bytes_data_uri(buffer.getvalue(), "image/jpeg")

    def _cards(self) -> list[dict]:
        """Showcase cards (`cards` in the content JSON: `path`, `label`, optional `caption` and `keep`,
        the top fraction of the image to keep - use it to crop off footer text before it ships)."""
        cards = []
        for card in self.content.get("cards", []):
            with Image.open(Path(card["path"]).expanduser()) as image:
                image = image.convert("RGB")
                image = image.crop((0, 0, image.width, round(image.height * card.get("keep", 1.0))))
                image = image.resize((_CARD_WIDTH, round(image.height * _CARD_WIDTH / image.width)), Image.Resampling.LANCZOS)
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=95)
            cards.append(dict(src=self.bytes_data_uri(buffer.getvalue(), "image/jpeg"), label=card["label"], caption=card.get("caption", "")))
        return cards

    def _features(self) -> list[dict]:
        """Feature tiles; a tile may carry `image` (`path`, optional `box` = left/top/right/bottom crop
        in pixels), shown on the right of a `wide` tile."""
        features = []
        for feature in self.content["features"]:
            feature = dict(feature)
            art = feature.pop("image", None)
            if art:
                with Image.open(Path(art["path"]).expanduser()) as image:
                    image = image.convert("RGB")
                    if art.get("box"):
                        image = image.crop(tuple(art["box"]))
                    image = image.resize((_ART_WIDTH, round(image.height * _ART_WIDTH / image.width)), Image.Resampling.LANCZOS)
                    buffer = BytesIO()
                    image.save(buffer, format="JPEG", quality=95)
                feature["art_src"] = self.bytes_data_uri(buffer.getvalue(), "image/jpeg")
            features.append(feature)
        return features

    def context(self) -> dict:
        return dict(
            cards=self._cards(),
            logo_dark_src=self.data_uri(_DARK_LOGO_PATH, "image/png"),
            screenshot_src=self._screenshot_src(),
            version=self.content["version"],
            eyebrow=self.content.get("eyebrow", "What's new"),
            headline=f"{self.content['headline_lead']} {self.content['headline_accent']}",
            headline_lead=self.content["headline_lead"],
            headline_accent=self.content["headline_accent"],
            subhead=self.content.get("subhead", ""),
            status_plates=self.content.get("status_plates", []),
            features=self._features(),
            also=self.content.get("also", []),
            tagline=self.content.get("tagline", ""),
            url=self.content.get("url", "showdownbot.com"),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--content", type=Path, required=True)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = ReleaseNotesSocial(json.loads(args.content.read_text()), args.screenshot)
    html_path = args.out_dir / "release_notes.html"
    html_path.write_text(report.render())
    skipped = ReleaseNotesSocial.write_images(html_path=html_path, image_paths=ReleaseNotesSocial.image_paths(args.out_dir, "release_notes", "png"), scale=2)
    print(skipped or f"Wrote {args.out_dir / 'release_notes_1.png'}")


if __name__ == "__main__":
    main()
