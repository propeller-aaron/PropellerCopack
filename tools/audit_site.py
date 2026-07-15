"""Audit main site HTML pages for structural and integration issues."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"css", "js", "img", "fonts", "includes", "tools", "seo", "status", "it", "worker", "src"}


def iter_pages() -> list[Path]:
    pages = [ROOT / "index.html"]
    pages.extend(
        sorted(p / "index.html" for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP)
    )
    return [p for p in pages if p.is_file()]


def audit_page(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    issues: list[str] = []

    if "</div></div>" in text and "bloc-6" in text:
        issues.append("collapsed closing divs near bloc-6")

    bloc6_end = text.find("<!-- bloc-6 END -->")
    bloc11_start = text.find('id="bloc-11"')
    if bloc6_end != -1 and bloc11_start != -1 and bloc11_start < bloc6_end:
        issues.append("bloc-11 nested inside bloc-6")

    pc = re.search(
        r'<div class="page-container">([\s\S]*?)</div>\s*<!-- Main container END -->',
        text,
    )
    if pc:
        chunk = pc.group(1)
        opens = len(re.findall(r"<div[\s>]", chunk))
        closes = chunk.count("</div>")
        if opens != closes:
            issues.append(f"div mismatch in page-container ({opens} open, {closes} close)")

    if "Contact2." in text:
        issues.append("still uses Contact2 image")
    if "jqBootstrapValidation" in text:
        issues.append("legacy jqBootstrapValidation script")
    if "formHandler.js" in text and "hsforms.net" not in text:
        issues.append("legacy formHandler without HubSpot embed")
    if 'class="hs-form-frame"' not in text:
        issues.append("missing HubSpot contact form")
    if "js-na2.hsforms.net/forms/embed/246245836.js" not in text:
        issues.append("missing HubSpot form script")
    if 'alt="Blending"' in text and "powder-blending" not in rel:
        issues.append('hero alt still "Blending"')
    if "Contact3." not in text:
        issues.append("missing Contact3 header image")

    return issues


def check_homepage_links() -> list[str]:
    text = (ROOT / "index.html").read_text(encoding="utf-8")
    issues: list[str] = []
    hrefs = re.findall(r'href="(\./[^"#]+/)"', text)
    for href in sorted(set(hrefs)):
        path = ROOT / href[2:] / "index.html"
        if not path.is_file():
            issues.append(f"index.html: broken link {href}")
    return issues


def main() -> None:
    pages = iter_pages()
    all_issues: list[tuple[str, list[str]]] = []
    for path in pages:
        issues = audit_page(path)
        if issues:
            all_issues.append((path.relative_to(ROOT).as_posix(), issues))

    for issue in check_homepage_links():
        all_issues.append(("index.html", [issue.split(": ", 1)[-1]]))

    print(f"Checked {len(pages)} pages")
    if not all_issues:
        print("No issues found")
        return

    for rel, issues in all_issues:
        for issue in issues:
            print(f"{rel}: {issue}")


if __name__ == "__main__":
    main()
