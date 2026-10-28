"""
Renders one sample card per image parallel and saves two images of each to the frontend: a zoomed-in
crop the custom card builder's Image Parallel dropdown shows as a preview, and the full card shown
when hovering that preview. Base (NONE) is skipped since it has no preview.

Every sample uses the same player, year, and set so the parallel is the only thing that changes.

Usage:
    python -m mlb_showdown_bot.scripts.parallel_samples
    python -m mlb_showdown_bot.scripts.parallel_samples --parallels GALAXY RF
"""

import argparse
import os
import tempfile
from dataclasses import dataclass, field

from PIL import Image

from mlb_showdown_bot.core.card.card_generation import generate_card
from mlb_showdown_bot.core.card.images import ImageParallel, ImageFileFormat

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FRONTEND_OUTPUT_FOLDER = os.path.join(REPO_ROOT, 'frontend', 'public', 'images', 'parallels')


@dataclass(frozen=True)
class SampleVariant:
    """One saved image per parallel: a fractional (left, top, right, bottom) crop of the card, resized to `height`."""

    file_suffix: str
    crop_box: tuple[float, float, float, float]
    height: int


# Zoomed in on the player and background, clear of the header, chart, and name
ZOOMED_VARIANT = SampleVariant(file_suffix='', crop_box=(0.0, 0.07, 0.53, 0.49), height=360)
FULL_CARD_VARIANT = SampleVariant(file_suffix='-full', crop_box=(0.0, 0.0, 1.0, 1.0), height=840)


@dataclass
class ParallelSampleGenerator:
    """Builds the sample card for each parallel and writes its images."""

    name: str = 'Mike Piazza'
    year: str = '2000'
    set: str = '2001'
    output_folder: str = FRONTEND_OUTPUT_FOLDER
    variants: tuple[SampleVariant, ...] = (ZOOMED_VARIANT, FULL_CARD_VARIANT)
    parallels: list[ImageParallel] = field(default_factory=lambda: [p for p in ImageParallel if p != ImageParallel.NONE])

    @staticmethod
    def file_name(parallel: ImageParallel, variant: SampleVariant) -> str:
        """Image file name, keyed by enum name since some values (e.g. "B&W") aren't path-safe."""
        return f"{parallel.name.lower().replace('_', '-')}{variant.file_suffix}.webp"

    def render_card(self, parallel: ImageParallel, render_folder: str) -> str:
        """Render the full card for a parallel and return its path."""
        file_name = f'{parallel.name}.png'
        result = generate_card(
            name=self.name,
            year=self.year,
            set=self.set,
            image_parallel=parallel.value,
            image_output_folder_path=render_folder,
            image_output_file_name=file_name,
            image_file_format=ImageFileFormat.PNG,
        )
        if result.get('error'):
            raise Exception(result['error'])
        return os.path.join(render_folder, file_name)

    def save_variant(self, card_image: Image.Image, parallel: ImageParallel, variant: SampleVariant) -> str:
        """Crop and resize the rendered card for one variant and save it as webp."""
        width, height = card_image.size
        left, top, right, bottom = variant.crop_box
        cropped = card_image.crop((int(left * width), int(top * height), int(right * width), int(bottom * height)))
        scale = variant.height / cropped.height
        resized = cropped.resize((round(cropped.width * scale), variant.height), Image.LANCZOS)
        output_path = os.path.join(self.output_folder, self.file_name(parallel, variant))
        resized.save(output_path, format='WEBP', quality=82, method=6)
        return output_path

    def run(self) -> None:
        os.makedirs(self.output_folder, exist_ok=True)
        with tempfile.TemporaryDirectory() as render_folder:
            for parallel in self.parallels:
                try:
                    card_path = self.render_card(parallel, render_folder)
                    with Image.open(card_path) as card_image:
                        for variant in self.variants:
                            output_path = self.save_variant(card_image, parallel, variant)
                            print(f'{parallel.name}: {os.path.relpath(output_path, REPO_ROOT)}')
                except Exception as e:
                    print(f'{parallel.name}: FAILED - {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Render image parallel sample images for the card builder.')
    parser.add_argument('--parallels', nargs='*', help='ImageParallel names to render (default: all)')
    parser.add_argument('--output', default=FRONTEND_OUTPUT_FOLDER, help='Folder the images are written to')
    args = parser.parse_args()

    generator = ParallelSampleGenerator(output_folder=args.output)
    if args.parallels:
        generator.parallels = [ImageParallel[name] for name in args.parallels]
    generator.run()
