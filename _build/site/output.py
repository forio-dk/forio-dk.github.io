"""Writing the generated files: only when their content changed, so a second build leaves git status clean."""
import shutil
from pathlib import Path

from assets import Picture, responsive_webp
from config import App


def write_text(path: Path, text: str) -> bool:
    """Writes UTF-8 text with \\n line endings, only when the content differs. Returns whether it wrote."""
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


def app_webp(app: App, src: Path, folder: str, stem: str, widths: tuple[int, ...]) -> Picture:
    """A WebP set under <app>/assets/<folder>, served at the matching URL."""
    return responsive_webp(src, app.assets / folder, f"{app.assets_url}/{folder}", stem, widths)
