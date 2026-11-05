import base64
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

_TEMPLATE_DIR = Path(__file__).parent / "templates"
# ONE SHEET (MATCHES `html.pdf .sheet` IN _social_base.html.j2), AND THE EXTRA WINDOW HEIGHT
# `write_images` CAPTURES BEFORE CROPPING TO IT.
_SHEET_SIZE = (1080, 1350)
_CAPTURE_HEADROOM = 200

# BRAND ASSETS, EMBEDDED AS DATA URIS SO THE RENDERED PAGE IS ONE SELF-CONTAINED FILE. THE LOGO
# AND THE DESIGN-LANGUAGE FONTS (frontend/DESIGN.md "Type": THE METRIC-NORMALIZED DISPLAY FACES AND
# INTER FOR BODY COPY) ARE THE FRONTEND'S OWN, READ STRAIGHT FROM THE REPO RATHER THAN COPIED INTO
# THE PACKAGE - THESE REPORTS ARE LOCAL CLI TOOLS RUN FROM A CHECKOUT.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LOGO_PATH = _REPO_ROOT / "frontend" / "public" / "images" / "logos" / "logo-light.png"
_FRONTEND_FONT_DIR = _REPO_ROOT / "frontend" / "src" / "assets" / "fonts"
_FONT_PATH = _FRONTEND_FONT_DIR / "HelveticaNeueCondensedHeavyOblique.otf"
_UPRIGHT_FONT_PATH = _FRONTEND_FONT_DIR / "HelveticaNeueBoldCondensed.ttf"
# INTER COMES FROM THE FRONTEND'S `@fontsource-variable/inter` PACKAGE, SO IT'S ONLY THERE AFTER AN
# `npm install`; WITHOUT IT THE PAGE FALLS BACK TO THE SYSTEM SANS.
_BODY_FONT_PATH = _REPO_ROOT / "frontend" / "node_modules" / "@fontsource-variable" / "inter" / "files" / "inter-latin-wght-normal.woff2"
# UPRIGHT EXTRA BLACK FOR THE POSTSEASON HERO TITLE - HEAVY LIKE THE WORDMARK ABOVE IT.
_TITLE_FONT_PATH = Path(__file__).parent.parent / "card" / "fonts" / "HelveticaNeueLtStd107ExtraBlack.otf"

# WHERE TO LOOK FOR A CHROME/CHROMIUM BINARY FOR PDF EXPORT. `CHROME_PATH` WINS WHEN SET.
_CHROME_CANDIDATES = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


class SocialSheetReport:
    """Base for the self-contained, socials-ready HTML reports (inline CSS, assets and one small
    fit-to-page script), laid out at a fixed 1080px width so they can be screenshotted straight
    to socials. Templates extend `_social_base.html.j2`, which carries the frontend's light-theme
    tokens and the shared sheet/slide machinery.

    Opened as `<page>.html#pdf`, the page splits into `SHEET_COUNT` 1080x1350 (4:5) sheets;
    `write_pdf` prints that view through headless Chrome into a PDF where each page doubles as a
    carousel slide. `write_images` captures the same sheets as separate PNG/JPEG files
    (`#pdf-N` isolates sheet N) for posting a page on its own.
    """

    # NUMBER OF `.sheet` ELEMENTS THE SUBCLASS'S TEMPLATE RENDERS.
    SHEET_COUNT = 1
    TEMPLATE_NAME: str = ""

    def __init__(self) -> None:
        self.env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=select_autoescape(["html", "j2"]))

    @staticmethod
    def bytes_data_uri(data: bytes, mime: str) -> str:
        return f"data:{mime};base64,{base64.b64encode(data).decode()}"

    @classmethod
    def data_uri(cls, path: Path, mime: str) -> str:
        return cls.bytes_data_uri(path.read_bytes(), mime)

    def context(self) -> dict:
        """Template variables beyond the brand assets - overridden by each report."""
        return {}

    def render(self) -> str:
        return self.env.get_template(self.TEMPLATE_NAME).render(
            logo_src=self.data_uri(_LOGO_PATH, "image/png"),
            font_src=self.data_uri(_FONT_PATH, "font/otf"),
            title_font_src=self.data_uri(_TITLE_FONT_PATH, "font/otf"),
            upright_font_src=self.data_uri(_UPRIGHT_FONT_PATH, "font/ttf"),
            body_font_src=self.data_uri(_BODY_FONT_PATH, "font/woff2") if _BODY_FONT_PATH.exists() else "",
            **self.context(),
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
        the caller."""
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
    def image_paths(cls, out_dir: Path, stem: str, image_format: str) -> list[Path]:
        """One path per sheet, e.g. `summary_1.png`, `summary_2.png` - `SHEET_COUNT` of them."""
        return [out_dir / f"{stem}_{page}.{image_format}" for page in range(1, cls.SHEET_COUNT + 1)]

    @classmethod
    def write_images(cls, html_path: Path, image_paths: list[Path]) -> Optional[str]:
        """Screenshot each sheet as its own image, one per path in `image_paths` (page 1 to
        `image_paths[0]`, page 2 to `image_paths[1]`, ...) - `SHEET_COUNT` of them. The format
        (PNG/JPEG) is whatever each path's extension says; headless Chrome picks it up from that.
        Returns None on success, or a reason every image was skipped - like `write_pdf`, image
        export is optional and never fails the caller."""
        if len(image_paths) != cls.SHEET_COUNT:
            raise ValueError(f"write_images needs exactly {cls.SHEET_COUNT} path(s), got {len(image_paths)}")
        chrome = cls.find_chrome()
        if chrome is None:
            return "Chrome not found (set CHROME_PATH to enable image export)"
        html_uri = html_path.resolve().as_uri()
        for page, image_path in enumerate(image_paths, start=1):
            # `#pdf-N` HIDES EVERY SHEET BUT THE ONE BEING CAPTURED (SEE THE BASE TEMPLATE'S
            # SCRIPT), SO THAT SHEET SITS AT THE TOP OF THE PAGE. HEADLESS CHROME CAN PAINT A
            # VIEWPORT SHORTER THAN `--window-size` (LEAVING THE SHEET'S BOTTOM BLANK), SO CAPTURE A
            # TALLER WINDOW AND CROP BACK DOWN TO THE SHEET.
            command = [
                chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                f"--window-size={_SHEET_SIZE[0]},{_SHEET_SIZE[1] + _CAPTURE_HEADROOM}", "--virtual-time-budget=10000",
                f"--screenshot={image_path.resolve()}", f"{html_uri}#pdf-{page}",
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, timeout=120)
            except (subprocess.SubprocessError, OSError) as error:
                return f"Chrome image export failed on page {page}: {error}"
            if not image_path.exists():
                return f"Chrome ran but produced no image for page {page}"
            with Image.open(image_path) as screenshot:
                sheet = screenshot.crop((0, 0, *_SHEET_SIZE))
            sheet.save(image_path)
        return None
