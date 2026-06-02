"""Ensure Contact3 header phone graphic uses tel: link to toll-free number."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTACT3_PICTURE_LINK = re.compile(
    r'<a href="#(?:bloc-5|bloc-6)">(\s*<picture>[\s\S]*?Contact3\.[\s\S]*?</picture>\s*)</a>'
)
CONTACT3_TEL = "tel:+18007888689"
EXCLUDE = {"seo", "status", "img", "js", "css", "fonts", "includes", "tools", "src", "worker"}


def fix_contact3_link(html: str) -> tuple[str, bool]:
    updated = CONTACT3_PICTURE_LINK.sub(
        f'<a href="{CONTACT3_TEL}">\\1</a>',
        html,
    )
    updated = updated.replace(
        'alt="Contact" width="338" height="110">',
        'alt="Call 800-788-8689" width="338" height="110">',
    )
    return updated, updated != html


def main() -> None:
    paths = [ROOT / "index.html"] + [
        p for p in ROOT.glob("*/index.html") if p.parent.name not in EXCLUDE
    ]
    changed = 0
    for path in sorted(paths):
        original = path.read_text(encoding="utf-8")
        updated, did_change = fix_contact3_link(original)
        if did_change:
            path.write_text(updated, encoding="utf-8")
            changed += 1
            print(f"updated: {path.relative_to(ROOT)}")
    print(f"done: {changed} page(s) updated")


if __name__ == "__main__":
    main()
