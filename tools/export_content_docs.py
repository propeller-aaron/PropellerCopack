"""Export current website text into Word documents."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from content.html_blocks import (  # noqa: E402
    BlockSpec,
    homepage_blocks,
    inner_page_blocks,
    shared_contact_inner_blocks,
    shared_footer_blocks,
    shared_inner_banner_blocks,
)
from content.pages import (  # noqa: E402
    PAGES_DIR,
    ROOT,
    SHARED_DIR,
    iter_inner_page_paths,
    iter_page_paths,
    page_doc_path,
    page_slug,
    page_url,
)
from content.word_io import write_document  # noqa: E402


def extract_blocks(page_html: str, specs: list[BlockSpec]) -> list[tuple[BlockSpec, str]]:
    return [(spec, spec.extract(page_html)) for spec in specs]


def export_shared() -> int:
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    inner_pages = iter_inner_page_paths()
    if not inner_pages:
        return 0

    sample_inner = inner_pages[0].read_text(encoding="utf-8")
    write_document(
        SHARED_DIR / "inner-banner.docx",
        title="Shared: Inner page banner",
        subtitle="Applies to all 23 service pages (bloc-1).",
        blocks=extract_blocks(sample_inner, shared_inner_banner_blocks()),
        notes=[
            "This banner appears at the top of every service page.",
            "Edit once here; changes apply to all inner pages when you run apply_content_docs.py.",
        ],
    )

    write_document(
        SHARED_DIR / "contact-inner.docx",
        title="Shared: Service page contact section",
        subtitle="Applies to all 23 service pages (bloc-5).",
        blocks=extract_blocks(sample_inner, shared_contact_inner_blocks()),
        notes=[
            "Contact form itself is managed in HubSpot and is not edited here.",
        ],
    )

    sample_any = iter_page_paths()[0].read_text(encoding="utf-8")
    write_document(
        SHARED_DIR / "footer.docx",
        title="Shared: Site footer",
        subtitle="Applies to all 24 public pages (bloc-11).",
        blocks=extract_blocks(sample_any, shared_footer_blocks()),
    )
    return 3


def export_pages() -> int:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    homepage = ROOT / "index.html"
    homepage_html = homepage.read_text(encoding="utf-8")
    write_document(
        page_doc_path("homepage"),
        title="Homepage",
        subtitle="URL: /",
        blocks=extract_blocks(homepage_html, homepage_blocks()),
        notes=[
            "Homepage feature/packaging cards and service links are editable here.",
            "Link destinations (URLs) are not changed from Word—only link labels.",
        ],
    )
    count += 1

    specs = inner_page_blocks()
    for path in iter_inner_page_paths():
        slug = page_slug(path)
        page_html = path.read_text(encoding="utf-8")
        write_document(
            page_doc_path(slug),
            title=f"Service page: {slug.replace('-', ' ').title()}",
            subtitle=f"URL: {page_url(path)}",
            blocks=extract_blocks(page_html, specs),
            notes=[
                "Banner and contact/footer copy live in content/shared/*.docx.",
            ],
        )
        count += 1

    return count


def main() -> None:
    shared_count = export_shared()
    page_count = export_pages()
    print(f"Exported {shared_count} shared document(s) to {SHARED_DIR.relative_to(ROOT)}")
    print(f"Exported {page_count} page document(s) to {PAGES_DIR.relative_to(ROOT)}")
    print("Edit the .docx files, save, then run: python tools/apply_content_docs.py")


if __name__ == "__main__":
    main()
