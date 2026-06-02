"""Demote extra H1s on v3 service pages; keep bloc-7 service title as sole H1."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THREE_H1_SLUGS = (
    "custom-projects",
    "formulation",
    "fulfillment",
    "ingredient-solutions",
    "kitting-and-assembly",
    "loading-docks",
    "low-moqs",
    "manufacturing",
    "packaging-design",
    "powder-blending",
    "product-development",
    "product-testing",
    "quality-compliance",
    "turn-key-co-packing",
    "white-label",
)


def fix_headings(text: str) -> tuple[str, list[str], int]:
    changes: list[str] = []

    text, n1 = re.subn(
        r'(<div class="bloc bgc-6037 d-bloc b-divider" id="bloc-1">[\s\S]*?)'
        r"<h1 class=\"mb-4 h1-style\">([\s\S]*?)</h1>",
        r'\1<h2 class="mb-4 h1-style">\2</h2>',
        text,
        count=1,
    )
    if n1:
        changes.append("bloc-1 h1->h2")

    text, n2 = re.subn(
        r'<h1 class="mb-4 h1-33469-style">([\s\S]*?)</h1>',
        r'<h2 class="mb-4 h1-33469-style">\1</h2>',
        text,
        count=1,
    )
    if n2:
        changes.append("contact h1->h2")

    h1_count = len(re.findall(r"<h1\b", text, re.I))
    return text, changes, h1_count


def main(slugs: tuple[str, ...] = THREE_H1_SLUGS) -> None:
    for slug in slugs:
        path = ROOT / slug / "index.html"
        original = path.read_text(encoding="utf-8")
        updated, changes, h1_count = fix_headings(original)
        if updated == original:
            print(f"{slug}: no change (h1={h1_count})")
            continue
        path.write_text(updated, encoding="utf-8")
        print(f"{slug}: {', '.join(changes)} (h1={h1_count})")


if __name__ == "__main__":
    main()
