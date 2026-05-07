"""Fix mistaken image:title Blending entries in sitemap.xml per URL."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"

SLUG_TITLE: dict[str, str] = {
    "packaging-design": "Packaging Design",
    "fda": "FDA",
    "testing": "Testing",
    "customer-service": "Customer Service",
    "low-moqs": "Low MOQs",
    "custom-runs": "Small Custom Runs",
    "dock-doors": "Dock Doors",
    "3pl-services": "3PL Services",
    "distribution": "Distribution",
    "40000-sq-ft": "40,000 Sq. Ft.",
    "randd": "Research & Development",
    "white-label": "White Label",
    "turn-key": "Turn-Key",
}


def main() -> None:
    text = SITEMAP.read_text(encoding="utf-8")
    blocks = re.split(r"(?=<url>)", text)
    out = [blocks[0]]
    for block in blocks[1:]:
        m = re.search(
            r"<loc>https://propellercopack\.com/([^<]*?)/?</loc>", block
        )
        if not m:
            out.append(block)
            continue
        slug = (m.group(1) or "").strip("/")
        if slug in SLUG_TITLE:
            title = SLUG_TITLE[slug]
            block = block.replace(
                "<image:title>Blending</image:title>",
                f"<image:title>{title}</image:title>",
            )
        out.append(block)
    SITEMAP.write_text("".join(out), encoding="utf-8")
    print("sitemap image:title fixes applied")


if __name__ == "__main__":
    main()
