"""
Extract logo and product photos from the Propeller mockup PNG.
Requires Pillow. Run from repo root: python tools/extract_design_assets.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    src = resolve_source()
    if src != MOCKUP_COPY:
        shutil.copy2(src, MOCKUP_COPY)
        src = MOCKUP_COPY

    im = Image.open(src).convert("RGBA")
    w, h = im.size
    assert (w, h) == (403, 1024), f"Unexpected size {w}x{h}, update crop boxes"

    # --- Logo (header white bar only; stop before sage hero at ~y 55)
    crop_logo = im.crop((4, 4, min(260, w - 1), 44))
    crop_logo.save(OUT / "logo-lockup.png")

    # Icon-only mark (~square region over green circle in header)
    crop_icon = im.crop((8, 10, 52, 50))
    crop_icon.save(OUT / "logo-mark.png")

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

    # --- Team section background (blurred warehouse photo in mockup)
    im.crop((0, 608, w, 738)).save(OUT / "team-background.png")

    # --- Team headshots (warehouse band ~y 615–735)
    ty0, ty1 = 618, 728
    tw = w // 3
    for i in range(3):
        xa = 8 + i * tw
        xb = min(w - 8, (i + 1) * tw - 8)
        face = im.crop((xa, ty0, xb, ty1))
        # circular crop approx: square centered, slightly inset for chin room
        fw, fh = face.size
        side = min(fw, fh) - 4
        ox = (fw - side) // 2
        oy = 4
        face_sq = face.crop((ox, oy, ox + side, oy + side))
        face_sq.save(OUT / f"team-0{i + 1}.png")

    print("Wrote assets to", OUT)
    for p in sorted(OUT.glob("*.png")):
        print(" ", p.name, p.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
