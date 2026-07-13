"""Public page discovery helpers."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content"
PAGES_DIR = CONTENT_DIR / "pages"
SHARED_DIR = CONTENT_DIR / "shared"
SKIP = {"css", "js", "img", "fonts", "includes", "tools", "seo", "status", "worker", "src", "content"}


def iter_page_paths() -> list[Path]:
    pages = [ROOT / "index.html"]
    pages.extend(
        sorted(p / "index.html" for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP)
    )
    return [p for p in pages if p.is_file()]


def iter_inner_page_paths() -> list[Path]:
    return [p for p in iter_page_paths() if p.parent != ROOT]


def page_slug(path: Path) -> str:
    if path.parent == ROOT:
        return "homepage"
    return path.parent.name


def page_url(path: Path) -> str:
    if path.parent == ROOT:
        return "/"
    return f"/{path.parent.name}/"


def page_doc_path(slug: str) -> Path:
    return PAGES_DIR / f"{slug}.docx"
