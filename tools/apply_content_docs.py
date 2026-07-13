"""Apply Word document edits back to website HTML pages."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from content.html_blocks import (  # noqa: E402
    BlockSpec,
    blocks_by_id,
    homepage_blocks,
    inner_page_blocks,
    normalize_compare_text,
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
)
from content.word_io import parse_document  # noqa: E402


def apply_blocks_to_html(
    page_html: str,
    doc_blocks: list,
    specs: list[BlockSpec],
) -> tuple[str, list[str]]:
    lookup = blocks_by_id(specs)
    changed_ids: list[str] = []

    for doc_block in doc_blocks:
        spec = lookup.get(doc_block.block_id)
        if spec is None:
            continue
        current = normalize_compare_text(spec.extract(page_html))
        incoming = normalize_compare_text(doc_block.text)
        if current == incoming:
            continue
        page_html, changed = spec.apply(page_html, doc_block.text)
        if changed:
            changed_ids.append(doc_block.block_id)

    return page_html, changed_ids


def apply_shared_doc(
    doc_path: Path,
    specs: list[BlockSpec],
    targets: list[Path],
) -> list[str]:
    if not doc_path.is_file():
        return []

    doc_blocks = parse_document(doc_path)
    messages: list[str] = []

    for target in targets:
        page_html = target.read_text(encoding="utf-8")
        updated, changed_ids = apply_blocks_to_html(page_html, doc_blocks, specs)
        if changed_ids:
            target.write_text(updated, encoding="utf-8")
            rel = target.relative_to(ROOT).as_posix()
            messages.append(f"{doc_path.name} -> {rel}: {', '.join(changed_ids)}")

    return messages


def apply_page_doc(doc_path: Path, specs: list[BlockSpec], target: Path) -> list[str]:
    if not doc_path.is_file():
        return []

    doc_blocks = parse_document(doc_path)
    page_html = target.read_text(encoding="utf-8")
    updated, changed_ids = apply_blocks_to_html(page_html, doc_blocks, specs)
    if not changed_ids:
        return []

    target.write_text(updated, encoding="utf-8")
    rel = target.relative_to(ROOT).as_posix()
    return [f"{doc_path.name} -> {rel}: {', '.join(changed_ids)}"]


def main() -> None:
    messages: list[str] = []

    messages.extend(
        apply_shared_doc(
            SHARED_DIR / "inner-banner.docx",
            shared_inner_banner_blocks(),
            iter_inner_page_paths(),
        )
    )
    messages.extend(
        apply_shared_doc(
            SHARED_DIR / "contact-inner.docx",
            shared_contact_inner_blocks(),
            iter_inner_page_paths(),
        )
    )
    messages.extend(
        apply_shared_doc(
            SHARED_DIR / "footer.docx",
            shared_footer_blocks(),
            iter_page_paths(),
        )
    )

    homepage_doc = page_doc_path("homepage")
    homepage_target = ROOT / "index.html"
    messages.extend(apply_page_doc(homepage_doc, homepage_blocks(), homepage_target))

    inner_specs = inner_page_blocks()
    for target in iter_inner_page_paths():
        slug = page_slug(target)
        messages.extend(apply_page_doc(page_doc_path(slug), inner_specs, target))

    if not messages:
        print("No content changes detected in Word documents.")
        return

    print(f"Applied changes from {len(messages)} update(s):")
    for message in messages:
        print(f"  {message}")


if __name__ == "__main__":
    main()
