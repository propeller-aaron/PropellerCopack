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

TWO_H1_SLUGS = (
    "40000-sq-ft-facility",
    "bottles-and-jars",
    "customer-service",
    "distribution",
    "sachet-packaging",
    "stand-up-pouches",
    "stick-pack-packaging",
)


def demote_bloc1_banner(text: str) -> tuple[str, bool]:
    return re.subn(
        r'(<div class="bloc bgc-6037 d-bloc b-divider" id="bloc-1">[\s\S]*?)'
        r"<h1 class=\"mb-4 h1-style\">([\s\S]*?)</h1>",
        r'\1<h2 class="mb-4 h1-style">\2</h2>',
        text,
        count=1,
    )


def fix_three_h1_headings(text: str) -> tuple[str, list[str], int]:
    changes: list[str] = []

    text, n1 = demote_bloc1_banner(text)
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


def fix_two_h1_headings(text: str) -> tuple[str, list[str], int]:
    changes: list[str] = []
    text, n1 = demote_bloc1_banner(text)
    if n1:
        changes.append("bloc-1 h1->h2")
    h1_count = len(re.findall(r"<h1\b", text, re.I))
    return text, changes, h1_count


def fix_homepage_headings(text: str) -> tuple[str, list[str], int]:
    changes: list[str] = []
    text, n1 = re.subn(
        r'<h1 class="mb-4 h1-bloc-6-style">([\s\S]*?)</h1>',
        r'<h2 class="mb-4 h1-bloc-6-style">\1</h2>',
        text,
        count=1,
    )
    if n1:
        changes.append("contact h1->h2")
    h1_count = len(re.findall(r"<h1\b", text, re.I))
    return text, changes, h1_count


def fix_headings(text: str) -> tuple[str, list[str], int]:
    return fix_three_h1_headings(text)


def apply_fix(
    label: str,
    path: Path,
    fixer,
) -> None:
    original = path.read_text(encoding="utf-8")
    updated, changes, h1_count = fixer(original)
    if updated == original:
        print(f"{label}: no change (h1={h1_count})")
        return
    path.write_text(updated, encoding="utf-8")
    print(f"{label}: {', '.join(changes)} (h1={h1_count})")


def main() -> None:
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in {"all", "three-h1"}:
        for slug in THREE_H1_SLUGS:
            apply_fix(slug, ROOT / slug / "index.html", fix_three_h1_headings)
    if mode in {"all", "two-h1"}:
        for slug in TWO_H1_SLUGS:
            apply_fix(slug, ROOT / slug / "index.html", fix_two_h1_headings)
    if mode in {"all", "homepage"}:
        apply_fix("/", ROOT / "index.html", fix_homepage_headings)


if __name__ == "__main__":
    main()
