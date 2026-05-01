"""
Extract logo and product photos from the Propeller mockup PNG.
Requires Pillow. Run from repo root: python tools/extract_design_assets.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

try:
    _LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    _LANCZOS = Image.LANCZOS  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
MOCKUP_COPY = OUT / "mockup-original.png"
# Fallback: Cursor workspace copy (same filename pattern as design upload)
CURSOR_SRC = Path(
    r"C:\Users\aaron\.cursor\projects\d-Development-PropellerCopack-PropellerCopack"
    r"\assets\c__Users_aaron_AppData_Roaming_Cursor_User_workspaceStorage_cdfea3a0ced06cfc0f8dca991f4c79a5_images_PropellerCopack-f41ded6d-6183-4a15-a9fb-faf5a8d8d737.png"
)


def resolve_source() -> Path:
    if MOCKUP_COPY.is_file():
        return MOCKUP_COPY
    if CURSOR_SRC.is_file():
        return CURSOR_SRC
    raise SystemExit(
        f"Place mockup-original.png in {OUT} or restore Cursor asset at:\n  {CURSOR_SRC}"
    )


def extract_logo_lockups(im: Image.Image, w: int, h: int) -> None:
    """
    Largest native crop from the header (logo only, excluding nav links on the right),
    plus a high-res upscale for sharp display at larger sizes. The source mockup is
    low-res; upscale uses Lanczos (no new detail, but many more pixels).
    """
    rgb = im.convert("RGB")
    px = rgb.load()
    # Header band; stop before sage hero (~y 58+)
    band_top, band_bottom = 0, min(58, h)
    # Ignore right-side nav: logo stays left of this x (mockup is 403px wide)
    x_nav_start = min(int(w * 0.62), w - 1)
    threshold = 248
    min_x, min_y = w, h
    max_x = max_y = 0
    for y in range(band_top, band_bottom):
        for x in range(0, x_nav_start):
            r, g, b = px[x, y]
            if r + g + b < threshold * 3:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    pad = 6
    min_x = max(0, min_x - pad)
    min_y = max(0, min_y - pad)
    max_x = min(w - 1, max_x + pad)
    max_y = min(band_bottom - 1, max_y + pad)

    lockup = im.crop((min_x, min_y, max_x + 1, max_y + 1))
    lockup.save(OUT / "logo-lockup.png")

    scale = 4
    large_w = lockup.width * scale
    large_h = lockup.height * scale
    lockup_large = lockup.resize((large_w, large_h), _LANCZOS)
    lockup_large.save(OUT / "logo-lockup-large.png")

    # Icon-only: left-hand circular mark (square crop)
    side = min(lockup.height, max(lockup.width // 4, 40))
    lockup.crop((0, 0, min(side, lockup.width), lockup.height)).save(OUT / "logo-mark.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    src = resolve_source()
    if src != MOCKUP_COPY:
        shutil.copy2(src, MOCKUP_COPY)
        src = MOCKUP_COPY

    im = Image.open(src).convert("RGBA")
    w, h = im.size
    assert (w, h) == (403, 1024), f"Unexpected size {w}x{h}, update crop boxes"

    extract_logo_lockups(im, w, h)

    # --- Services: three card photos (3-column layout on this mockup)
    # Vertical band where cards sit (below hero green, above fulfillment blue ~y 345)
    y0, y1 = 132, 338
    cols = (
        (6, 128),  # ingredient
        (132, 252),  # formulation
        (256, 396),  # packaging
    )
    # Photo is upper portion of each card (~top 78% of card height ≈ top 160px of band)
    img_bottom = y0 + 155
    names = ("service-ingredients", "service-formulation", "service-packaging")
    for (xa, xb), name in zip(cols, names, strict=True):
        box = (xa, y0, min(xb, w - 1), min(img_bottom, y1))
        im.crop(box).save(OUT / f"{name}.png")

    # Full-width services background (powder bowls) — strip behind cards
    im.crop((0, y0, w, y1)).save(OUT / "services-background.png")

    # --- Fulfillment: 8 circular product shots (blue section ~y 345–615)
    fy0, fy1 = 348, 612
    band = im.crop((0, fy0, w, fy1))
    bw, bh = band.size
    cell_w = bw // 4
    cell_h = bh // 2
    pad_x = max(6, cell_w // 10)
    pad_y = max(6, cell_h // 10)
    for row in range(2):
        for col in range(4):
            cx0 = col * cell_w + pad_x
            cy0 = row * cell_h + pad_y
            cx1 = (col + 1) * cell_w - pad_x
            cy1 = (row + 1) * cell_h - pad_y
            sq = band.crop((cx0, cy0, cx1, cy1))
            # center square (product fills circle inside cell)
            sw, sh = sq.size
            side = min(sw, sh)
            ox = (sw - side) // 2
            oy = (sh - side) // 2
            shot = sq.crop((ox, oy, ox + side, oy + side))
            idx = row * 4 + col + 1
            shot.save(OUT / f"product-fulfillment-{idx:02d}.png")

    print("Wrote assets to", OUT)
    for p in sorted(OUT.glob("*.png")):
        print(" ", p.name, p.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
