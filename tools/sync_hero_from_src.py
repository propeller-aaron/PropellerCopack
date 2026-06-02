"""Sync bloc-7 hero sections and image assets from PropellerCopack v.3 src."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "PropellerCopack v.3"

from apply_v3_from_src import SLUG_MAP, rewrite_slug_hrefs  # noqa: E402
from fix_hero_alts import ALT as HERO_ALTS  # noqa: E402

BLOC7_RE = re.compile(r"<!-- bloc-7 -->[\s\S]*?<!-- bloc-7 END -->", re.IGNORECASE)

# Correct hero image + alt when src export still points at the wrong asset.
HERO_OVERRIDES: dict[str, tuple[str, str]] = {
    "ingredient-solutions": (
        "../img/Ingredients.png",
        "Ingredient solutions",
    ),
}


def copy_images() -> None:
    count = 0
    for img in (SRC / "img").iterdir():
        if img.is_file():
            shutil.copy2(img, ROOT / "img" / img.name)
            count += 1
    print(f"copied {count} images from src")


def apply_hero_override(block: str, slug: str) -> str:
    if slug not in HERO_OVERRIDES:
        return block
    png_path, alt = HERO_OVERRIDES[slug]
    webp_path = png_path.replace(".png", ".webp")
    picture = (
        f'<picture><source type="image/webp" srcset="../img/lazyload-ph.png" '
        f'data-srcset="{webp_path}">'
        f'<img src="../img/lazyload-ph.png" data-src="{png_path}" '
        f'class="img-fluid mx-auto d-block lazyload" alt="{alt}" '
        f'width="364" height="364"></picture>'
    )
    return re.sub(
        r"<picture>[\s\S]*?</picture>",
        picture,
        block,
        count=1,
    )


def fix_bloc7_alt(block: str, slug: str) -> str:
    alt = HERO_ALTS.get(slug)
    if not alt:
        return block

    def repl(match: re.Match[str]) -> str:
        return f'{match.group(1)}{alt}{match.group(2)}'

    return re.sub(
        r'(<picture>[\s\S]*?<img[^>]+alt=")[^"]*(")',
        repl,
        block,
        count=1,
    )


def sync_bloc7(live_slug: str, src_slug: str) -> bool:
    live_path = ROOT / live_slug / "index.html"
    src_path = SRC / src_slug / "index.html"
    if not live_path.is_file() or not src_path.is_file():
        print(f"skip missing: {live_slug} / {src_slug}")
        return False

    live_html = live_path.read_text(encoding="utf-8")
    src_html = src_path.read_text(encoding="utf-8")

    src_match = BLOC7_RE.search(src_html)
    live_match = BLOC7_RE.search(live_html)
    if not src_match:
        print(f"skip no bloc-7 in src: {src_slug}")
        return False
    if not live_match:
        print(f"skip no bloc-7 on live: {live_slug}")
        return False

    block = rewrite_slug_hrefs(src_match.group(0), is_root=False)
    block = apply_hero_override(block, live_slug)
    block = fix_bloc7_alt(block, live_slug)

    updated = live_html[: live_match.start()] + block + live_html[live_match.end() :]
    if updated == live_html:
        print(f"unchanged: {live_slug}")
        return False

    live_path.write_text(updated, encoding="utf-8")
    print(f"synced bloc-7: {live_slug} <- {src_slug}")
    return True


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Source folder not found: {SRC}")

    copy_images()
    synced = 0
    for src_slug, live_slug in sorted(SLUG_MAP.items()):
        if sync_bloc7(live_slug, src_slug):
            synced += 1
    print(f"done: {synced} mapped page(s) updated")


if __name__ == "__main__":
    main()
