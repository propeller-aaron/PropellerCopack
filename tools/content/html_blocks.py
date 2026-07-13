"""Extract and apply editable HTML content blocks."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Callable

BLOCK_MARKER = re.compile(r"^\[\[block:([^\]]+)\]\]\s*$")


def bloc_body(page_html: str, bloc_id: str) -> str | None:
    match = re.search(
        rf'<!-- {re.escape(bloc_id)} -->[\s\S]*?id="{re.escape(bloc_id)}"[^>]*>([\s\S]*?)'
        rf"<!-- {re.escape(bloc_id)} END -->",
        page_html,
    )
    return match.group(1) if match else None


def replace_bloc_body(page_html: str, bloc_id: str, new_body: str) -> tuple[str, bool]:
    pattern = (
        rf'(<!-- {re.escape(bloc_id)} -->[\s\S]*?id="{re.escape(bloc_id)}"[^>]*>)'
        rf"([\s\S]*?)"
        rf"(<!-- {re.escape(bloc_id)} END -->)"
    )

    def replacer(match: re.Match[str]) -> str:
        return match.group(1) + new_body + match.group(3)

    updated, count = re.subn(pattern, replacer, page_html, count=1)
    return updated, count == 1


def normalize_compare_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u2026", "...")
    return text.strip()


def inner_html_to_text(fragment: str) -> str:
    text = fragment.strip()
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>\s*<p[^>]*>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def text_to_inner_html(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    parts: list[str] = []
    for index, line in enumerate(lines):
        if index:
            parts.append("<br>")
        parts.append(html.escape(line, quote=False))
    return "".join(parts)


def extract_first(pattern: str, source: str) -> str:
    match = re.search(pattern, source, flags=re.I | re.S)
    return inner_html_to_text(match.group(1)) if match else ""


def replace_first(pattern: str, source: str, new_inner: str) -> tuple[str, bool]:
    def replacer(match: re.Match[str]) -> str:
        return match.group(1) + new_inner + match.group(3)

    updated, count = re.subn(pattern, replacer, source, count=1, flags=re.I | re.S)
    return updated, count == 1


@dataclass(frozen=True)
class BlockSpec:
    block_id: str
    label: str
    extract: Callable[[str], str]
    apply: Callable[[str, str], tuple[str, bool]]


def _meta_title_extract(page_html: str) -> str:
    match = re.search(r"<title>([\s\S]*?)</title>", page_html, flags=re.I)
    return inner_html_to_text(match.group(1)) if match else ""


def _meta_title_apply(page_html: str, text: str) -> tuple[str, bool]:
    return replace_first(
        r"(<title>)([\s\S]*?)(</title>)",
        page_html,
        html.escape(text.strip(), quote=False),
    )


def _meta_description_extract(page_html: str) -> str:
    match = re.search(
        r'<meta\s+name="description"\s+content="([^"]*)"',
        page_html,
        flags=re.I,
    )
    return html.unescape(match.group(1)) if match else ""


def _meta_description_apply(page_html: str, text: str) -> tuple[str, bool]:
    escaped = html.escape(text.strip(), quote=True)
    updated, changed = replace_first(
        r'(<meta\s+name="description"\s+content=")([^"]*)(")',
        page_html,
        escaped,
    )
    if changed:
        return updated, True

    updated, changed = replace_first(
        r'(<meta\s+property="og:description"\s+content=")([^"]*)(")',
        updated,
        escaped,
    )
    updated, changed2 = replace_first(
        r'(<meta\s+name="twitter:description"\s+content=")([^"]*)(")',
        updated,
        escaped,
    )
    return updated, changed or changed2


def _bloc_heading_extract(page_html: str, bloc_id: str, tag: str, class_fragment: str) -> str:
    body = bloc_body(page_html, bloc_id)
    if not body:
        return ""
    return extract_first(
        rf"<{tag}[^>]*class=\"[^\"]*{class_fragment}[^\"]*\"[^>]*>([\s\S]*?)</{tag}>",
        body,
    )


def _bloc_heading_apply(
    page_html: str,
    bloc_id: str,
    tag: str,
    class_fragment: str,
    text: str,
) -> tuple[str, bool]:
    body = bloc_body(page_html, bloc_id)
    if body is None:
        return page_html, False
    new_body, changed = replace_first(
        rf"(<{tag}[^>]*class=\"[^\"]*{class_fragment}[^\"]*\"[^>]*>)([\s\S]*?)(</{tag}>)",
        body,
        text_to_inner_html(text),
    )
    if not changed:
        return page_html, False
    return replace_bloc_body(page_html, bloc_id, new_body)


def _bloc_paragraph_extract(page_html: str, bloc_id: str, class_fragment: str) -> str:
    body = bloc_body(page_html, bloc_id)
    if not body:
        return ""
    return extract_first(
        rf"<p[^>]*class=\"[^\"]*{class_fragment}[^\"]*\"[^>]*>([\s\S]*?)</p>",
        body,
    )


def _bloc_paragraph_apply(
    page_html: str,
    bloc_id: str,
    class_fragment: str,
    text: str,
) -> tuple[str, bool]:
    body = bloc_body(page_html, bloc_id)
    if body is None:
        return page_html, False

    pattern = rf"(<p[^>]*class=\"[^\"]*{class_fragment}[^\"]*\"[^>]*>)([\s\S]*?)(</p>)"
    match = re.search(pattern, body, flags=re.I | re.S)
    if not match:
        return page_html, False

    old_inner = match.group(2)
    trailing_br = bool(re.search(r"<br\s*/?>\s*$", old_inner, flags=re.I))
    new_inner = text_to_inner_html(text)
    if trailing_br and new_inner and not re.search(r"<br\s*/?>\s*$", new_inner, flags=re.I):
        new_inner += "<br>"

    new_body = body[: match.start()] + match.group(1) + new_inner + match.group(3) + body[match.end() :]
    if new_body == body:
        return page_html, False
    return replace_bloc_body(page_html, bloc_id, new_body)


def _bloc_img_alt_extract(page_html: str, bloc_id: str, occurrence: int = 0) -> str:
    body = bloc_body(page_html, bloc_id)
    if not body:
        return ""
    matches = list(re.finditer(r'<img[^>]*alt="([^"]*)"', body, flags=re.I))
    if occurrence >= len(matches):
        return ""
    return html.unescape(matches[occurrence].group(1))


def _bloc_img_alt_apply(
    page_html: str,
    bloc_id: str,
    text: str,
    occurrence: int = 0,
) -> tuple[str, bool]:
    body = bloc_body(page_html, bloc_id)
    if body is None:
        return page_html, False

    matches = list(re.finditer(r'(<img[^>]*alt=")([^"]*)(")', body, flags=re.I))
    if occurrence >= len(matches):
        return page_html, False

    match = matches[occurrence]
    escaped = html.escape(text.strip(), quote=True)
    new_body = (
        body[: match.start()]
        + match.group(1)
        + escaped
        + match.group(3)
        + body[match.end() :]
    )
    return replace_bloc_body(page_html, bloc_id, new_body)


def _bloc_link_text_extract(page_html: str, bloc_id: str, index: int) -> str:
    body = bloc_body(page_html, bloc_id)
    if not body:
        return ""
    links = list(re.finditer(r'<a class="link-style"[^>]*>([\s\S]*?)</a>', body, flags=re.I))
    if index >= len(links):
        return ""
    return inner_html_to_text(links[index].group(1))


def _bloc_link_text_apply(
    page_html: str,
    bloc_id: str,
    index: int,
    text: str,
) -> tuple[str, bool]:
    body = bloc_body(page_html, bloc_id)
    if body is None:
        return page_html, False

    links = list(re.finditer(r'(<a class="link-style"[^>]*>)([\s\S]*?)(</a>)', body, flags=re.I))
    if index >= len(links):
        return page_html, False

    match = links[index]
    new_body = (
        body[: match.start()]
        + match.group(1)
        + html.escape(text.strip(), quote=False)
        + match.group(3)
        + body[match.end() :]
    )
    return replace_bloc_body(page_html, bloc_id, new_body)


def inner_page_blocks() -> list[BlockSpec]:
    return [
        BlockSpec("meta:title", "Browser tab title", _meta_title_extract, _meta_title_apply),
        BlockSpec(
            "meta:description",
            "SEO meta description",
            _meta_description_extract,
            _meta_description_apply,
        ),
        BlockSpec(
            "bloc-7:h1",
            "Page hero title (H1)",
            lambda html: _bloc_heading_extract(html, "bloc-7", "h1", "h2-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-7", "h1", "h2-style", text),
        ),
        BlockSpec(
            "bloc-7:body",
            "Page body paragraph",
            lambda html: _bloc_paragraph_extract(html, "bloc-7", "p-4-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-7", "p-4-style", text),
        ),
        BlockSpec(
            "bloc-7:img-alt",
            "Hero image alt text",
            lambda html: _bloc_img_alt_extract(html, "bloc-7", 0),
            lambda html, text: _bloc_img_alt_apply(html, "bloc-7", text, 0),
        ),
    ]


def shared_inner_banner_blocks() -> list[BlockSpec]:
    return [
        BlockSpec(
            "bloc-1:title",
            "Inner page banner title",
            lambda html: _bloc_heading_extract(html, "bloc-1", "h2", "h1-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-1", "h2", "h1-style", text),
        ),
        BlockSpec(
            "bloc-1:subtitle",
            "Inner page banner subtitle",
            lambda html: _bloc_heading_extract(html, "bloc-1", "h2", "h2-bloc-1-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-1", "h2", "h2-bloc-1-style", text),
        ),
        BlockSpec(
            "bloc-1:body",
            "Inner page banner paragraph",
            lambda html: _bloc_paragraph_extract(html, "bloc-1", "p-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-1", "p-style", text),
        ),
    ]


def shared_contact_inner_blocks() -> list[BlockSpec]:
    return [
        BlockSpec(
            "bloc-5:title",
            "Contact section title",
            lambda html: _bloc_heading_extract(html, "bloc-5", "h2", "h1-33469-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-5", "h2", "h1-33469-style", text),
        ),
        BlockSpec(
            "bloc-5:body",
            "Contact section paragraph",
            lambda html: _bloc_paragraph_extract(html, "bloc-5", "p-15-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-5", "p-15-style", text),
        ),
    ]


def shared_footer_blocks() -> list[BlockSpec]:
    return [
        BlockSpec(
            "bloc-11:office-title",
            "Footer office column title",
            lambda html: _bloc_heading_extract(html, "bloc-11", "h2", "h2-office-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-11", "h2", "h2-office-style", text),
        ),
        BlockSpec(
            "bloc-11:office-body",
            "Footer office address",
            lambda html: _bloc_paragraph_extract(html, "bloc-11", "p-bloc-11-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-11", "p-bloc-11-style", text),
        ),
        BlockSpec(
            "bloc-11:manufacturing-title",
            "Footer manufacturing column title",
            lambda html: _bloc_heading_extract(html, "bloc-11", "h2", "h2-warehouse-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-11", "h2", "h2-warehouse-style", text),
        ),
        BlockSpec(
            "bloc-11:manufacturing-body",
            "Footer manufacturing address",
            lambda html: _bloc_paragraph_extract(html, "bloc-11", "p-7-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-11", "p-7-style", text),
        ),
        BlockSpec(
            "bloc-11:contact-title",
            "Footer contact column title",
            lambda html: _bloc_heading_extract(html, "bloc-11", "h2", "h2-contact-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-11", "h2", "h2-contact-style", text),
        ),
        BlockSpec(
            "bloc-11:contact-body",
            "Footer contact details",
            lambda html: _bloc_paragraph_extract(html, "bloc-11", "p-8-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-11", "p-8-style", text),
        ),
    ]


def homepage_blocks() -> list[BlockSpec]:
    blocks: list[BlockSpec] = [
        BlockSpec("meta:title", "Browser tab title", _meta_title_extract, _meta_title_apply),
        BlockSpec(
            "meta:description",
            "SEO meta description",
            _meta_description_extract,
            _meta_description_apply,
        ),
        BlockSpec(
            "bloc-1:h1",
            "Homepage hero title (H1)",
            lambda html: _bloc_heading_extract(html, "bloc-1", "h1", "h1-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-1", "h1", "h1-style", text),
        ),
        BlockSpec(
            "bloc-1:subtitle",
            "Homepage hero subtitle",
            lambda html: _bloc_heading_extract(html, "bloc-1", "h2", "h2-bloc-1-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-1", "h2", "h2-bloc-1-style", text),
        ),
        BlockSpec(
            "bloc-1:body",
            "Homepage hero paragraph",
            lambda html: _bloc_paragraph_extract(html, "bloc-1", "p-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-1", "p-style", text),
        ),
        BlockSpec(
            "bloc-3:title",
            "Packaging section title",
            lambda html: _bloc_heading_extract(html, "bloc-3", "h2", "h3-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-3", "h2", "h3-style", text),
        ),
        BlockSpec(
            "bloc-6:title",
            "Homepage contact title",
            lambda html: _bloc_heading_extract(html, "bloc-6", "h2", "h1-bloc-6-style"),
            lambda html, text: _bloc_heading_apply(html, "bloc-6", "h2", "h1-bloc-6-style", text),
        ),
        BlockSpec(
            "bloc-6:body",
            "Homepage contact paragraph",
            lambda html: _bloc_paragraph_extract(html, "bloc-6", "p-bloc-6-style"),
            lambda html, text: _bloc_paragraph_apply(html, "bloc-6", "p-bloc-6-style", text),
        ),
    ]

    feature_cards = [
        ("card-1", "h3-1-feature-title-style", "Custom Formulations"),
        ("card-2", "h3-feature-title-style", "Product Development"),
        ("card-3", "h3-3-style", "Manufacturing"),
    ]
    for card_id, class_fragment, default_label in feature_cards:
        blocks.append(
            BlockSpec(
                f"bloc-2:{card_id}:title",
                f"Feature card title ({default_label})",
                lambda html, cf=class_fragment: _bloc_heading_extract(html, "bloc-2", "h3", cf),
                lambda html, text, cf=class_fragment: _bloc_heading_apply(
                    html, "bloc-2", "h3", cf, text
                ),
            )
        )
        blocks.append(
            BlockSpec(
                f"bloc-2:{card_id}:img-alt",
                f"Feature card image alt ({default_label})",
                lambda html, idx=int(card_id.split("-")[1]) - 1: _bloc_img_alt_extract(
                    html, "bloc-2", idx
                ),
                lambda html, text, idx=int(card_id.split("-")[1]) - 1: _bloc_img_alt_apply(
                    html, "bloc-2", text, idx
                ),
            )
        )

    packaging_cards = [
        ("card-1", "h3-john-doe-style", "Sachets"),
        ("card-2", "h3-stick-packs-style", "Stick Packs"),
        ("card-3", "h3-1-style", "Stand Up Pouches"),
        ("card-4", "h3-2-style", "Bottles / Jars"),
    ]
    for card_id, class_fragment, default_label in packaging_cards:
        blocks.append(
            BlockSpec(
                f"bloc-3:{card_id}:title",
                f"Packaging card title ({default_label})",
                lambda html, cf=class_fragment: _bloc_heading_extract(html, "bloc-3", "h4", cf),
                lambda html, text, cf=class_fragment: _bloc_heading_apply(
                    html, "bloc-3", "h4", cf, text
                ),
            )
        )
        blocks.append(
            BlockSpec(
                f"bloc-3:{card_id}:img-alt",
                f"Packaging card image alt ({default_label})",
                lambda html, idx=int(card_id.split("-")[1]) - 1: _bloc_img_alt_extract(
                    html, "bloc-3", idx
                ),
                lambda html, text, idx=int(card_id.split("-")[1]) - 1: _bloc_img_alt_apply(
                    html, "bloc-3", text, idx
                ),
            )
        )

    for index in range(15):
        blocks.append(
            BlockSpec(
                f"bloc-4:link-{index + 1}",
                f"Homepage service link {index + 1}",
                lambda html, i=index: _bloc_link_text_extract(html, "bloc-4", i),
                lambda html, text, i=index: _bloc_link_text_apply(html, "bloc-4", i, text),
            )
        )

    return blocks


def blocks_by_id(specs: list[BlockSpec]) -> dict[str, BlockSpec]:
    return {spec.block_id: spec for spec in specs}
