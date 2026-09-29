import base64
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .postseason_batch import ROUND_LABELS, NotableGameTag, PostseasonBatchSummary

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_TEMPLATE_NAME = "postseason_batch_summary.html.j2"

# BRAND ASSETS, EMBEDDED AS DATA URIS SO THE RENDERED PAGE IS ONE SELF-CONTAINED FILE. THE FONT
# IS THE SAME CONDENSED HEAVY OBLIQUE THE FRONTEND SHIPS AS `ShowdownSetItalic`.
# THE LOGO IS THE FRONTEND'S OWN LIGHT-MODE WORDMARK, READ STRAIGHT FROM THE REPO RATHER THAN
# COPIED INTO THE PACKAGE - THIS REPORT IS A LOCAL CLI TOOL RUN FROM A CHECKOUT.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LOGO_PATH = _REPO_ROOT / "frontend" / "public" / "images" / "logos" / "logo-light.png"
_FONT_DIR = Path(__file__).parent.parent / "card" / "fonts"
_FONT_PATH = _FONT_DIR / "HelveticaNeueCondensedHeavyOblique.otf"
# UPRIGHT EXTRA BLACK FOR THE HERO TITLE - HEAVY LIKE THE WORDMARK ABOVE IT.
_TITLE_FONT_PATH = _FONT_DIR / "HelveticaNeueLtStd107ExtraBlack.otf"

_NOTABLE_LABELS = {
    NotableGameTag.WALK_OFF.value: "Walk-offs",
    NotableGameTag.EXTRA_INNINGS.value: "Extra-inning games",
    NotableGameTag.BLOWOUT.value: "Blowouts (7+ runs)",
}


# WHERE TO LOOK FOR A CHROME/CHROMIUM BINARY FOR PDF EXPORT. `CHROME_PATH` WINS WHEN SET.
_CHROME_CANDIDATES = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


class PostseasonBatchReport:
    """Renders a `PostseasonBatchSummary` as a single self-contained HTML page (inline CSS, assets
    and one small fit-to-page script), laid out at a fixed 1080px width so it can be screenshotted straight to
    socials. Styled after the frontend's light theme and showdown-blue/red brand colors.

    Opened as `summary.html#pdf`, the page splits into two 1080x1350 (4:5) sheets; `write_pdf`
    prints that view through headless Chrome into a two-page PDF where each page doubles as a
    carousel slide. `write_images` captures the same two sheets as separate PNG/JPEG files
    (`#pdf-1`/`#pdf-2` isolate one sheet each) for posting a page on its own.
    """

    # NUMBER OF `.sheet` ELEMENTS THE TEMPLATE RENDERS - MUST MATCH THE `#pdf-1`/`#pdf-2` HASHES
    # THE TEMPLATE'S SCRIPT UNDERSTANDS.
    SHEET_COUNT = 2

    def __init__(self, summary: PostseasonBatchSummary) -> None:
        self.summary = summary
        self.env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=select_autoescape(["html", "j2"]))

    @staticmethod
    def _data_uri(path: Path, mime: str) -> str:
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"

    def render(self) -> str:
        summary = self.summary
        contenders = [t for t in summary.teams if t.titles > 0]
        max_title_pct = max((t.title_pct for t in contenders), default=1) or 1
        leagues = sorted({t.league for t in summary.teams if t.league})
        return self.env.get_template(_TEMPLATE_NAME).render(
            s=summary,
            contenders=contenders,
            max_title_pct=max_title_pct,
            pennant_races={
                league: sorted([t for t in summary.teams if t.league == league], key=lambda t: -t.pennant_pct)
                for league in leagues
            },
            round_labels=ROUND_LABELS,
            notable_labels=_NOTABLE_LABELS,
            logo_src=self._data_uri(_LOGO_PATH, "image/png"),
            font_src=self._data_uri(_FONT_PATH, "font/otf"),
            title_font_src=self._data_uri(_TITLE_FONT_PATH, "font/otf"),
        )

    @staticmethod
    def find_chrome() -> Optional[str]:
        for candidate in [os.environ.get("CHROME_PATH")] + _CHROME_CANDIDATES:
            if not candidate:
                continue
            path = shutil.which(candidate) or (candidate if Path(candidate).is_file() else None)
            if path:
                return path
        return None

    @classmethod
    def write_pdf(cls, html_path: Path, pdf_path: Path) -> Optional[str]:
        """Print the rendered HTML to `pdf_path` with headless Chrome. Returns None on success, or
        a reason the PDF was skipped - PDF export is optional, so a missing Chrome never fails
        the batch."""
        chrome = cls.find_chrome()
        if chrome is None:
            return "Chrome not found (set CHROME_PATH to enable PDF export)"
        # `#pdf` SWITCHES THE PAGE INTO SLIDE MODE; THE VIRTUAL TIME BUDGET LETS ITS FIT-TO-PAGE
        # SCRIPT (WHICH WAITS ON FONT LOADING) FINISH BEFORE CHROME PRINTS.
        command = [
            chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
            "--virtual-time-budget=10000", f"--print-to-pdf={pdf_path.resolve()}", html_path.resolve().as_uri() + "#pdf",
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=120)
        except (subprocess.SubprocessError, OSError) as error:
            return f"Chrome PDF export failed: {error}"
        return None if pdf_path.exists() else "Chrome ran but produced no PDF"

    @classmethod
    def write_images(cls, html_path: Path, image_paths: list[Path]) -> Optional[str]:
        """Screenshot each summary sheet as its own image, one per path in `image_paths` (page 1
        to `image_paths[0]`, page 2 to `image_paths[1]`, ...) - `SHEET_COUNT` of them. The format
        (PNG/JPEG) is whatever each path's extension says; headless Chrome picks it up from that.
        Returns None on success, or a reason every image was skipped - like `write_pdf`, image
        export is optional and never fails the batch."""
        if len(image_paths) != cls.SHEET_COUNT:
            raise ValueError(f"write_images needs exactly {cls.SHEET_COUNT} path(s), got {len(image_paths)}")
        chrome = cls.find_chrome()
        if chrome is None:
            return "Chrome not found (set CHROME_PATH to enable image export)"
        html_uri = html_path.resolve().as_uri()
        for page, image_path in enumerate(image_paths, start=1):
            # `#pdf-N` HIDES EVERY SHEET BUT THE ONE BEING CAPTURED (SEE THE TEMPLATE'S SCRIPT) -
            # THE 1080x1350 WINDOW THEN FRAMES EXACTLY THAT SHEET, NO SCROLLING OR CROPPING NEEDED.
            command = [
                chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--window-size=1080,1350", "--virtual-time-budget=10000",
                f"--screenshot={image_path.resolve()}", f"{html_uri}#pdf-{page}",
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, timeout=120)
            except (subprocess.SubprocessError, OSError) as error:
                return f"Chrome image export failed on page {page}: {error}"
            if not image_path.exists():
                return f"Chrome ran but produced no image for page {page}"
        return None
