"""Image and video processing for the Art Widget home page: WebP sets, share images, favicons, the preview video."""
import io
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

WEBP = {"format": "WEBP", "quality": 80, "method": 6}


@dataclass(frozen=True)
class Picture:
    src: str  # URL of the smallest file
    srcset: str  # "<url> <w>w, ..." in ascending width; empty for a single file
    width: int  # pixel size of the smallest file
    height: int


def responsive_webp(src: Path, out_dir: Path, url_dir: str, stem: str, widths: tuple[int, ...]) -> Picture:
    """Writes <out_dir>/<stem>-<w>.webp for each width, keeping the aspect ratio; never upscales."""
    widths = tuple(sorted(widths))
    out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as image:
        image = image.convert("RGBA" if has_alpha(image) else "RGB")
        if widths[-1] > image.width:
            raise ValueError(f"{src.name} is {image.width} px wide, narrower than {widths[-1]}")
        sizes = []
        for width in widths:
            height = round(image.height * width / image.width)
            image.resize((width, height), Image.LANCZOS).save(out_dir / f"{stem}-{width}.webp", **WEBP)
            sizes.append((width, height))
    urls = [f"{url_dir}/{stem}-{width}.webp" for width in widths]
    srcset = ", ".join(f"{url} {width}w" for url, width in zip(urls, widths))
    return Picture(urls[0], srcset, *sizes[0])


def has_alpha(image: Image.Image) -> bool:
    return image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info)


def og_jpeg(src: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as image:
        image.convert("RGB").save(out, format="JPEG", quality=85, optimize=True)


def favicons(src: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as image:
        image = image.convert("RGBA")
        for name, size in (("favicon-32.png", 32), ("apple-touch-icon.png", 180)):
            image.resize((size, size), Image.LANCZOS).save(out_dir / name, format="PNG", optimize=True)


def transcode_video(src: Path, out: Path, poster: Path) -> None:
    """Re-encodes the preview video at 720x1280 without sound, and writes its frame at 1 s as the poster.

    Does nothing when both files exist, since x264 output is not worth re-encoding on every build.
    """
    if out.is_file() and poster.is_file():
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-an", "-vf", "scale=720:1280:flags=lanczos",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(out)], check=True)
    frame = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1", "-i", str(out), "-frames:v", "1",
                            "-f", "image2pipe", "-vcodec", "png", "-"], check=True, capture_output=True).stdout
    with Image.open(io.BytesIO(frame)) as image:
        image.convert("RGB").save(poster, **WEBP)
