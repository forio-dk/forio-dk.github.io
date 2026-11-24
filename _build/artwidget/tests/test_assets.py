import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from config import VENDOR_DIR

from assets import Picture, favicons, forio_mark, og_jpeg, responsive_webp, transcode_video


def gradient(path: Path, size: tuple[int, int], mode: str = "RGB") -> Path:
    image = Image.linear_gradient("L").resize(size).convert(mode)
    image.save(path)
    return path


class AssetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.shot = gradient(self.tmp / "shot.png", (1080, 2160))

    def test_responsive_webp(self):
        picture = responsive_webp(self.shot, self.tmp / "out", "/x", "s", (200, 400))
        self.assertEqual(picture, Picture("/x/s-200.webp", "/x/s-200.webp 200w, /x/s-400.webp 400w", 200, 400))
        for width, height in ((200, 400), (400, 800)):
            with Image.open(self.tmp / "out" / f"s-{width}.webp") as image:
                self.assertEqual((image.format, image.size), ("WEBP", (width, height)))

    def test_responsive_webp_deterministic(self):
        responsive_webp(self.shot, self.tmp / "a", "/x", "s", (200,))
        responsive_webp(self.shot, self.tmp / "b", "/x", "s", (200,))
        self.assertEqual((self.tmp / "a" / "s-200.webp").read_bytes(), (self.tmp / "b" / "s-200.webp").read_bytes())

    def test_no_upscaling(self):
        with self.assertRaises(ValueError):
            responsive_webp(self.shot, self.tmp / "out", "/x", "s", (200, 2000))

    def test_og_jpeg(self):
        source = gradient(self.tmp / "feature.png", (1024, 500), "RGBA")
        og_jpeg(source, self.tmp / "img" / "og.jpg")
        with Image.open(self.tmp / "img" / "og.jpg") as image:
            self.assertEqual((image.format, image.size, image.mode), ("JPEG", (1024, 500), "RGB"))

    def test_favicons(self):
        favicons(gradient(self.tmp / "icon.png", (512, 512), "RGBA"), self.tmp / "img")
        for name, size in (("favicon-32.png", (32, 32)), ("apple-touch-icon.png", (180, 180))):
            with Image.open(self.tmp / "img" / name) as image:
                self.assertEqual((image.format, image.size), ("PNG", size))


class VideoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.source = cls.tmp / "src.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc=size=1080x1920:rate=30:duration=2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        str(cls.source)], check=True)
        cls.out = cls.tmp / "video" / "preview.mp4"
        cls.poster = cls.tmp / "video" / "preview-poster.webp"
        transcode_video(cls.source, cls.out, cls.poster)

    def test_transcode_video(self):
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(self.out)],
                               check=True, capture_output=True, text=True)
        streams = json.loads(probe.stdout)["streams"]
        self.assertEqual([(s["codec_type"], s["width"], s["height"]) for s in streams], [("video", 720, 1280)])
        data = self.out.read_bytes()
        self.assertLess(data.index(b"moov"), data.index(b"mdat"))
        with Image.open(self.poster) as image:
            self.assertEqual((image.format, image.size), ("WEBP", (720, 1280)))

    def test_transcode_skips_existing(self):
        before = self.out.stat().st_mtime_ns
        transcode_video(self.source, self.out, self.poster)
        self.assertEqual(self.out.stat().st_mtime_ns, before)


class ForioMarkTest(unittest.TestCase):
    """The Forio logo: a cream serif F hung in a gold frame on the navy wall."""

    FONT = VENDOR_DIR / "fonts" / "playfair-display-latin-600-normal.ttf"

    def test_rounded_mark(self):
        mark = forio_mark(self.FONT, 100)
        self.assertEqual((mark.size, mark.mode), ((100, 100), "RGBA"))
        self.assertEqual(mark.getpixel((1, 1))[3], 0)  # rounded corner
        r, g, b, a = mark.getpixel((22, 50))  # left side of the frame
        self.assertTrue(r > 180 and g > 120 and b < 110 and a == 255, (r, g, b, a))
        self.assertEqual(mark.getpixel((30, 72))[:3], (0x1B, 0x33, 0x58))  # inside the frame, below the F's foot
        cream = sum(1 for x in range(35, 65) for y in range(35, 67) if mark.getpixel((x, y))[0] > 230)
        self.assertGreater(cream, 60)  # the F

    def test_square_mark(self):
        self.assertEqual(forio_mark(self.FONT, 100, rounded=False).getpixel((1, 1))[3], 255)
