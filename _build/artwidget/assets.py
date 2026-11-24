"""Image and video processing for the Art Widget home page: WebP sets, share images, favicons, the preview video."""
import io
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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

    Does nothing when both files exist and are newer than the source, since x264 output is not worth re-encoding on
    every build.
    """
    if all(path.is_file() and path.stat().st_mtime_ns >= src.stat().st_mtime_ns for path in (out, poster)):
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


def forio_mark(font: Path, size: int, rounded: bool = True) -> Image.Image:
    """The Forio logo: a cream serif F hung in a gold frame on the navy wall of the Art Widget page.

    Drawn at four times the size and scaled down, in a 100-unit square; rounded=False fills the corners, for icons
    (like Apple's touch icon) that the system rounds itself.
    """
    scale = size * 4
    unit = scale / 100

    def box(x0: float, y0: float, x1: float, y1: float) -> tuple[int, int, int, int]:
        return round(x0 * unit), round(y0 * unit), round(x1 * unit), round(y1 * unit)

    wall = Image.new("RGB", (1, 2))
    wall.putpixel((0, 0), (0x2C, 0x52, 0x82))
    wall.putpixel((0, 1), (0x13, 0x28, 0x41))
    image = wall.resize((scale, scale), Image.BILINEAR).convert("RGBA")
    draw = ImageDraw.Draw(image)

    frame = box(20, 18, 80, 82)
    image.paste(diagonal_gold(frame[2] - frame[0], frame[3] - frame[1]), frame[:2])
    draw.rectangle(box(26, 24, 74, 76), fill=(0x6E, 0x4A, 0x12))
    draw.rectangle(box(27, 25, 73, 75), fill=(0x1B, 0x33, 0x58))
    draw.text((50 * unit, 66 * unit), "F", font=ImageFont.truetype(str(font), round(40 * unit)),
              fill=(0xFF, 0xF6, 0xE0), anchor="ms")

    if rounded:
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, scale - 1, scale - 1), radius=round(22 * unit), fill=255)
        image.putalpha(mask)
    return image.resize((size, size), Image.LANCZOS)


def diagonal_gold(width: int, height: int) -> Image.Image:
    """The gold of the picture frames: light at the top left, dark at the bottom right, as in the store graphics."""
    stops = [(0.0, (0xF8, 0xDE, 0x94)), (0.5, (0xD9, 0xA4, 0x41)), (1.0, (0x9E, 0x6A, 0x18))]
    ramp = Image.new("RGB", (256, 1))
    for i in range(256):
        t = i / 255
        (t0, c0), (t1, c1) = next((a, b) for a, b in zip(stops, stops[1:]) if t <= b[0])
        f = (t - t0) / (t1 - t0)
        ramp.putpixel((i, 0), tuple(round(a + (b - a) * f) for a, b in zip(c0, c1)))
    x = Image.linear_gradient("L").rotate(90).resize((width, height))  # 0 at the left, 255 at the right
    y = Image.linear_gradient("L").resize((width, height))  # 0 at the top, 255 at the bottom
    t = Image.blend(x, y, 0.5)
    return Image.merge("RGB", [band.point(lambda v, c=c: ramp.getpixel((v, 0))[c]) for c, band in enumerate([t] * 3)])
