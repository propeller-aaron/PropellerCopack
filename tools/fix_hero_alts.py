"""Set correct lazyload hero image alt text (fixes mistaken alt=\"Blending\")."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# slug -> hero image alt (topic column img in bloc-7)
ALT: dict[str, str] = {
    "40000-sq-ft-facility": "40,000 square foot manufacturing facility",
    "custom-projects": "Custom product development",
    "customer-service": "Customer service",
    "distribution": "Distribution and logistics",
    "formulation": "Product reformulation",
    "fulfillment": "3PL logistics and fulfillment",
    "ingredient-solutions": "Ingredient solutions",
    "kitting-and-assembly": "Kitting and assembly",
    "loading-docks": "Distribution center loading docks",
    "low-moqs": "Low minimum order quantities",
    "manufacturing": "Contract manufacturing",
    "packaging-design": "Packaging design",
    "powder-blending": "Powder blending",
    "product-development": "New product development",
    "product-testing": "Custom formulation and testing",
    "quality-compliance": "Quality and compliance",
    "turn-key-co-packing": "Turn-key co-manufacturing",
    "white-label": "White label products",
}


def main() -> None:
    for slug, alt in ALT.items():
        path = ROOT / slug / "index.html"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        old = 'class="img-fluid mx-auto d-block lazyload" alt="Blending"'
        new = f'class="img-fluid mx-auto d-block lazyload" alt="{alt}"'
        if old not in text:
            continue
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        print("alt:", slug)


if __name__ == "__main__":
    main()
