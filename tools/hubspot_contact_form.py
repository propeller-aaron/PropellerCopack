"""HubSpot contact form embed used site-wide."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HUBSPOT_SCRIPT = (
    '<script src="https://js-na2.hsforms.net/forms/embed/246245836.js" defer></script>'
)
HUBSPOT_FRAME = (
    '<div class="hs-form-frame" data-region="na2" '
    'data-form-id="892ca546-e4a6-4194-84a9-995725d68f76" '
    'data-portal-id="246245836"></div>'
)

# Inner pages: form column wrapper used by v3 migration tooling.
CONTACT_BLOCK = f"""			<div class="col-md-6 text-start">
				<div>
{HUBSPOT_FRAME}
				</div>
			</div>"""

# Homepage bloc-6 form column content.
HOMEPAGE_FORM_INNER = HUBSPOT_FRAME

PROPELLER_FORM_RE = re.compile(
    r'<div class="propeller-form-wrap">[\s\S]*?<p id="status"[^>]*>[\s\S]*?</p>\s*</div>',
    re.MULTILINE,
)
ORPHANED_PROP_FORM_RE = re.compile(
    r'(<div class="hs-form-frame"[^>]*></div>)\s*'
    r'(?:<div class="propeller-form-group">[\s\S]*?'
    r'<p id="status"[^>]*>[\s\S]*?</p>\s*</div>)',
    re.MULTILINE,
)
PROPELLER_SCRIPT_RE = re.compile(
    r'<script src="(?:\./|\.\./)js/propeller-contact\.js" defer></script>\s*',
    re.MULTILINE,
)
INLINE_HUBSPOT_SCRIPT_RE = re.compile(
    r'<script src="https://js-na2\.hsforms\.net/forms/embed/246245836\.js" defer></script>\s*',
    re.MULTILINE,
)

EXCLUDE = {"seo", "status", "it", "img", "js", "css", "fonts", "includes", "tools", "src", "worker"}


def replace_form_markup(html: str) -> tuple[str, bool]:
    changed = False
    updated, n = PROPELLER_FORM_RE.subn(HUBSPOT_FRAME, html)
    if n:
        changed = True
    html = updated

    updated, n = ORPHANED_PROP_FORM_RE.subn(r"\1", html)
    if n:
        changed = True
    html = updated

    # Remove duplicate inline HubSpot script if form block already included it.
    if html.count(HUBSPOT_SCRIPT) > 1:
        html = INLINE_HUBSPOT_SCRIPT_RE.sub("", html, count=html.count(HUBSPOT_SCRIPT) - 1)
        changed = True

    return html, changed


def replace_form_script(html: str, *, is_root: bool) -> tuple[str, bool]:
    del is_root
    changed = False
    if PROPELLER_SCRIPT_RE.search(html):
        html = PROPELLER_SCRIPT_RE.sub("", html)
        changed = True

    if HUBSPOT_SCRIPT not in html:
        html = html.replace(
            "<!-- Additional JS END -->",
            f"{HUBSPOT_SCRIPT}\n<!-- Additional JS END -->",
            1,
        )
        changed = True

    return html, changed


def apply_to_html(html: str, *, is_root: bool = False) -> tuple[str, bool]:
    html, markup_changed = replace_form_markup(html)
    html, script_changed = replace_form_script(html, is_root=is_root)
    return html, markup_changed or script_changed


def apply_to_file(path: Path) -> bool:
    is_root = path.name == "index.html" and path.parent == ROOT
    original = path.read_text(encoding="utf-8")
    updated, changed = apply_to_html(original, is_root=is_root)
    if not changed:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    paths = [ROOT / "index.html"] + [
        p for p in sorted(ROOT.glob("*/index.html")) if p.parent.name not in EXCLUDE
    ]
    updated = 0
    for path in paths:
        if apply_to_file(path):
            print(f"updated: {path.relative_to(ROOT)}")
            updated += 1
    print(f"done: {updated} page(s) updated")


if __name__ == "__main__":
    main()
