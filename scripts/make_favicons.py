#!/usr/bin/env python3
"""Regenerate every favicon from favicon.svg (root). Needs chromium (headless) and Pillow.
Usage: python3 scripts/make_favicons.py"""
import pathlib, subprocess, tempfile
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = ROOT / "favicon.svg"
import glob, os
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
