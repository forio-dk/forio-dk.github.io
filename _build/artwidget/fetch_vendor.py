"""Downloads the fonts, Google Play badges and artworks listed in config.VENDOR into vendor/, once, and copies
the app icons listed in config.LOCAL_VENDOR from the sibling repositories.

Run from the repository root: python -X utf8 _build/artwidget/fetch_vendor.py [--force]
The files are committed, so the generator never needs the network; --force downloads them all again.
"""
import argparse
import shutil
import sys
import urllib.request

from config import LOCAL_VENDOR, ROOT, VENDOR, VENDOR_DIR

USER_AGENT = "artwork-fetch/1.0"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def write_sources() -> None:
    lines = ["# Vendor sources", "", "Downloaded once by `fetch_vendor.py`; each file and its source URL.", ""]
    lines += [f"- `{name}`: {url}" for name, url in VENDOR.items()]
    lines += ["", "## Copied from sibling repositories", ""]
    lines += [f"- `{name}`: ../{source}" for name, source in LOCAL_VENDOR.items()]
    (VENDOR_DIR / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="download every file again")
    args = parser.parse_args(argv)
    for name, url in VENDOR.items():
        path = VENDOR_DIR / name
        if path.is_file() and not args.force:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(download(url))
        print(f"downloaded {name}")
    for name, source in LOCAL_VENDOR.items():
        path = VENDOR_DIR / name
        if path.is_file() and not args.force:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT.parent / source, path)
        print(f"copied {name}")
    write_sources()
    return 0


if __name__ == "__main__":
    sys.exit(main())
