#!/usr/bin/env python3
"""Regenerate favicon.svg (letters converted to outlines, so no font is needed to display it) and every PNG/ICO from it. Needs chromium (headless) and Pillow.
Usage: python3 scripts/make_favicons.py"""
import pathlib, subprocess, tempfile
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = ROOT / "favicon.svg"
import glob, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONT = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"  # what Georgia falls back to here
TEXT, SIZE, CX, BASE = "RP", 34, 32, 44  # same layout as the original <text>

def outline_svg():
    f = TTFont(FONT); gs = f.getGlyphSet(); cmap = f.getBestCmap(); k = SIZE / f["head"].unitsPerEm
    width = sum(f["hmtx"][cmap[ord(c)]][0] for c in TEXT) * k
    x = CX - width / 2; pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    for c in TEXT:
        g = cmap[ord(c)]
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, BASE)))
        x += f["hmtx"][g][0] * k
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#000000"/>'
            f'<path fill="#fff" d="{pen.getCommands()}"/></svg>\n')

SVG.write_text(outline_svg())
# Playwright's headless shell (the snap chromium cannot write outside its sandbox)
CHROME = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))[0]

def render(size, out):
    with tempfile.TemporaryDirectory() as t:
        html = pathlib.Path(t) / "i.html"
        html.write_text(f'<html><body style="margin:0;background:transparent"><img src="{SVG.as_uri()}" width="{size}" height="{size}" style="display:block"></body></html>')
        subprocess.run([CHROME, "--headless", "--no-sandbox", "--hide-scrollbars",
                        "--default-background-color=00000000", f"--window-size={size},{size}",
                        f"--screenshot={out}", "--allow-file-access-from-files", html.as_uri()],
                       check=True, capture_output=True)

def native(size, out):
    """Render at 8x then downscale (LANCZOS): sharp edges, transparent rounded corners."""
    big = 8 * size
    with tempfile.TemporaryDirectory() as t:
        p = pathlib.Path(t) / "big.png"; render(big, p)
        Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS).save(out)

for s, name in ((48, "favicon-48x48.png"), (96, "favicon-96x96.png"), (192, "favicon-192x192.png"), (180, "apple-touch-icon.png")):
    native(s, ROOT / name)
ico = []
for s in (16, 32, 48):
    p = pathlib.Path(tempfile.mkdtemp()) / f"{s}.png"; native(s, p); ico.append(Image.open(p))
ico[2].save(ROOT / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])

# iOS rounds the corners itself: give the touch icon an opaque black square
t = Image.open(ROOT / "apple-touch-icon.png"); bg = Image.new("RGBA", t.size, (0, 0, 0, 255)); bg.alpha_composite(t)
bg.convert("RGB").save(ROOT / "apple-touch-icon.png")
