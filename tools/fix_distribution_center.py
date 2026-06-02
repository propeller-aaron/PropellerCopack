"""Split Distribution Center (/distribution-center/) from Loading Docks (/loading-docks/)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "PropellerCopack v.3"
BLOC7_RE = re.compile(r"<!-- bloc-7 -->[\s\S]*?<!-- bloc-7 END -->", re.IGNORECASE)

LOADING_DOCKS_BLOC7 = """<!-- bloc-7 -->
<div class="bloc bgc-6037 d-bloc b-divider" id="bloc-7">
	<div class="container bloc-lg">
		<div class="row">
			<div class="col-sm-8 text-start">
				<h1 class="mb-4 h2-style">
					Loading Docks
				</h1>
				<p class="p-4-style">
					Our Utah facility provides dock access for receiving raw materials and shipping finished goods. Truck-high dock doors, grade-level doors, and yard space support efficient inbound and outbound logistics for co-packing programs.
				</p>
			</div>
			<div class="col-sm-4 text-start">
				<picture><source type="image/webp" srcset="../img/lazyload-ph.png" data-srcset="../img/Dock%20Doors.webp"><img src="../img/lazyload-ph.png" data-src="../img/Dock%20Doors.png" class="img-fluid mx-auto d-block lazyload" alt="Loading docks" width="364" height="364"></picture>
			</div>
		</div>
	</div>
</div>
<!-- bloc-7 END -->"""


def ensure_distribution_center_page() -> None:
    from apply_v3_from_src import merge_page

    target = ROOT / "distribution-center" / "index.html"
    target.parent.mkdir(exist_ok=True)
    if not target.is_file():
        shutil.copy2(ROOT / "loading-docks" / "index.html", target)
        text = target.read_text(encoding="utf-8")
        text = text.replace("/loading-docks/", "/distribution-center/")
        target.write_text(text, encoding="utf-8")
        print("seeded distribution-center from loading-docks")

    merge_page(target, SRC / "distribution-center" / "index.html")
    print("merged distribution-center from src")


def restore_loading_docks_page() -> None:
    path = ROOT / "loading-docks" / "index.html"
    text = path.read_text(encoding="utf-8")
    match = BLOC7_RE.search(text)
    if not match:
        print("WARN: no bloc-7 on loading-docks")
        return
    text = text[: match.start()] + LOADING_DOCKS_BLOC7 + text[match.end() :]
    path.write_text(text, encoding="utf-8")
    print("restored loading-docks bloc-7 (Loading Docks)")


def fix_homepage_link() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    old = 'href="./loading-docks/">Distribution Center'
    new = 'href="./distribution-center/">Distribution Center'
    if old not in text:
        print("homepage link already fixed or missing")
        return
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("fixed homepage Distribution Center link")


def fix_inner_links() -> None:
    """Point mistaken loading-docks links at distribution-center where label says Distribution Center."""
    pattern = re.compile(
        r'href="\.\./loading-docks/"([^>]*>)\s*Distribution Center',
        re.IGNORECASE,
    )
    for path in ROOT.glob("*/index.html"):
        if path.parent.name in {"seo", "status", "tools", "src", "loading-docks"}:
            continue
        text = path.read_text(encoding="utf-8")
        updated = pattern.sub(r'href="../distribution-center/"\1Distribution Center', text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            print(f"fixed inner link: {path.parent.name}")


def apply_seo_and_h1() -> None:
    from update_inner_seo import process_file
    from fix_h1_hierarchy import fix_three_h1_headings, apply_fix

    process_file(ROOT / "distribution-center" / "index.html")
    apply_fix("distribution-center", ROOT / "distribution-center" / "index.html", fix_three_h1_headings)

    path = ROOT / "distribution-center" / "index.html"
    text = path.read_text(encoding="utf-8")
    desc = (
        "40,000 sq. ft. distribution center in Utah—warehousing, cross-docking, "
        "fulfillment, and carrier integrations for growing brands."
    )
    text = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{desc}">',
        text,
        count=1,
    )
    text = text.replace(
        '<meta property="og:title" content="Loading Docks | Propeller Co-Pack">',
        '<meta property="og:title" content="Distribution Center | Propeller Co-Pack">',
    )
    text = text.replace(
        '<meta name="twitter:title" content="Loading Docks | Propeller Co-Pack">',
        '<meta name="twitter:title" content="Distribution Center | Propeller Co-Pack">',
    )
    for prop in ("og:description", "twitter:description"):
        text = re.sub(
            rf'<meta (?:property|name)="{prop}" content="[^"]*">',
            f'<meta {"property" if prop.startswith("og") else "name"}="{prop}" content="{desc}">',
            text,
            count=1,
        )
    if 'alt="Blending"' in text:
        text = text.replace(
            'class="img-fluid mx-auto d-block lazyload" alt="Blending"',
            'class="img-fluid mx-auto d-block lazyload" alt="Distribution center"',
            1,
        )
    path.write_text(text, encoding="utf-8")
    print("applied SEO + H1 + hero alt on distribution-center")


def add_sitemap_entry() -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    if "distribution-center/" in text:
        print("sitemap already has distribution-center")
        return
    marker = "<loc>https://propellercopack.com/loading-docks/</loc>"
    block = """<url>
	<loc>https://propellercopack.com/distribution-center/</loc>
	<lastmod>2026-06-02</lastmod>
	<changefreq>Weekly</changefreq>
	<priority>0.5</priority>
	<image:image>
	<image:loc>https://propellercopack.com/img/Dock%20Doors.png</image:loc>
	<image:title>Distribution Center</image:title>
	</image:image>
	<image:image>
	<image:loc>https://propellercopack.com/img/Dock%20Doors.webp</image:loc>
	<image:title>Distribution Center</image:title>
	</image:image>
</url>
"""
    if marker not in text:
        print("WARN: sitemap insert point not found")
        return
    if "distribution-center/" in text:
        print("sitemap already has distribution-center")
        return
    text = text.replace(
        f"<url>\n\t{marker}",
        block + f"<url>\n\t{marker}",
        1,
    )
    path.write_text(text, encoding="utf-8")
    print("added distribution-center to sitemap")


def main() -> None:
    ensure_distribution_center_page()
    restore_loading_docks_page()
    fix_homepage_link()
    fix_inner_links()
    apply_seo_and_h1()
    add_sitemap_entry()
    print("distribution-center fix complete")


if __name__ == "__main__":
    main()
