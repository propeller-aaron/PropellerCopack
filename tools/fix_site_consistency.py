"""One-off consistency fixes after v3 migration."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "PropellerCopack v.3"

OLD_HERO = """				<h2 class="mb-4 h1-style">
					POWDER MANUFACTURING
				</h2>
				<h2 class="mb-4 h2-bloc-1-style">
					From Concept to Delivery…<i>ON TIME!</i>
				</h2>
				<div class="blockquote">
					<p class="p-style">
						Propeller is a full-service nutritional co-packer helping brands turn product ideas into finished goods through formulation, packaging design, regulatory compliance, blending, filling options, and fulfillment services.<br>
					</p>
				</div>"""

NEW_HERO = """				<h1 class="mb-4 h1-style">
					POWDER MANUFACTURING
				</h1>
				<h2 class="mb-4 h2-bloc-1-style">
					From Concept to Delivery…<i>ON TIME!</i>
				</h2>
				<div>
					<p class="p-style">
						Propeller offers a modern manufacturing facility specializing in dry food, powder filling, grains, and supplement products.<br>We formulate, design, source, blend, pack, and ship. Every step, one solution.<br>
					</p>
				</div>"""

OLD_HERO_LINKED = OLD_HERO.replace(
    "through formulation, packaging design, regulatory compliance, blending, filling options, and fulfillment services.",
    "through <a href=\"../formulation/\">formulation</a>, <a href=\"../packaging-design/\">packaging design</a>, <a href=\"../quality-compliance/\">regulatory compliance</a>, blending, <a href=\"../stick-pack-packaging/\">filling options</a>, and fulfillment services.",
)

OLD_HERO_PACKAGING = OLD_HERO.replace(
    "through formulation, packaging design, regulatory compliance, blending, filling options, and fulfillment services.",
    "through formulation, <a href=\"../packaging-design/\">packaging</a> design, regulatory compliance, blending, filling options, and fulfillment services.",
)

PATCHED_PAGES = [
    "40000-sq-ft-facility",
    "bottles-and-jars",
    "customer-service",
    "distribution",
    "sachet-packaging",
    "stand-up-pouches",
    "stick-pack-packaging",
]


def harmonize_heroes() -> None:
    for slug in PATCHED_PAGES:
        path = ROOT / slug / "index.html"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if OLD_HERO_LINKED in text:
            text = text.replace(OLD_HERO_LINKED, NEW_HERO)
        elif OLD_HERO_PACKAGING in text:
            text = text.replace(OLD_HERO_PACKAGING, NEW_HERO)
        elif OLD_HERO in text:
            text = text.replace(OLD_HERO, NEW_HERO)
        else:
            print(f"skip hero (pattern not found): {slug}")
            continue
        path.write_text(text, encoding="utf-8")
        print(f"harmonized hero: {slug}")


def ensure_kitting_page() -> None:
    target = ROOT / "kitting-and-assembly" / "index.html"
    target.parent.mkdir(exist_ok=True)
    if not target.is_file():
        shutil.copy2(ROOT / "custom-projects" / "index.html", target)
        text = target.read_text(encoding="utf-8")
        text = text.replace("/custom-projects/", "/kitting-and-assembly/")
        text = re.sub(r"<title>[^<]*</title>", "<title>Kitting and Assembly</title>", text)
        target.write_text(text, encoding="utf-8")
        print("created kitting-and-assembly/index.html")


def main() -> None:
    from apply_v3_from_src import merge_page

    ensure_kitting_page()
    merge_page(ROOT / "custom-projects" / "index.html", SRC / "custom-product-development" / "index.html")
    merge_page(ROOT / "kitting-and-assembly" / "index.html", SRC / "kitting-and-assembly" / "index.html")
    harmonize_heroes()
    print("consistency fixes complete")


if __name__ == "__main__":
    main()
