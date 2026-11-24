"""Writing the generated files: only when their content changed, so a second build leaves git status clean."""
import shutil
from pathlib import Path

from PIL import Image

from assets import Picture, responsive_webp
from config import SHARED, SHARED_URL, VENDOR_DIR, App, Lang


def write_text(path: Path, text: str) -> bool:
    """Writes UTF-8 text with \n line endings, only when the content differs. Returns whether it wrote."""
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def copy_file(src: Path, dst: Path) -> None:
    if dst.is_file() and dst.read_bytes() == src.read_bytes():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def prune(folder: Path, keep: set[Path]) -> None:
    """Deletes the files in folder that this build did not write (keep), such as a removed screenshot's images."""
    if folder.is_dir():
        for path in folder.iterdir():
            if path.is_file() and path not in keep:
                path.unlink()


def app_webp(app: App, src: Path, folder: str, stem: str, widths: tuple[int, ...]) -> Picture:
    """A WebP set under <app>/assets/<folder>, served at the matching URL."""
    return responsive_webp(src, app.assets / folder, f"{app.assets_url}/{folder}", stem, widths)


def shared_webp(src: Path, folder: str, stem: str, widths: tuple[int, ...]) -> Picture:
    """A WebP set under assets/<folder>, served at the matching URL."""
    return responsive_webp(src, SHARED / folder, f"{SHARED_URL}/{folder}", stem, widths)


def badge(lang: Lang) -> Picture:
    """The language's Get it on Google Play badge, in assets/badges/, which every app's pages share."""
    dst = SHARED / "badges" / f"{lang.code}.png"
    copy_file(VENDOR_DIR / "badges" / f"{lang.code}.png", dst)
    with Image.open(dst) as image:
        return Picture(f"{SHARED_URL}/badges/{lang.code}.png", "", image.width, image.height)
