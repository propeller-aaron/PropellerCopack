"""Batch update inner marketing pages: SEO meta, contact form, lang, scripts."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BRAND_SUFFIX = " | Propeller Co-Pack"

PAGE_META: dict[str, tuple[str, str]] = {
    "40000-sq-ft-facility": (
        "40,000 Sq. Ft. Facility",
        "Powder manufacturing and co-packing in a 40,000 sq. ft. Utah facility—production, packaging, storage, and logistics under one roof.",
    ),
    "bottles-and-jars": (
        "Bottles & Jars",
        "Bottle and jar filling for powders, capsules, and liquids. Co-packing, labeling, and packout with Propeller Co-Pack.",
    ),
    "custom-projects": (
        "Custom Projects",
        "Custom projects and small-batch production for growing brands. Propeller Co-Pack Utah co-packer.",
    ),
    "customer-service": (
        "Customer Service",
        "Support for your co-packing program from onboarding through production. Contact Propeller Co-Pack.",
    ),
    "distribution": (
        "Distribution",
        "Distribution support from production to market. Propeller Co-Pack coordinates logistics with your brand.",
    ),
    "formulation": (
        "Custom Formulations",
        "Custom formulations for powders and nutritional products—concept through production-ready recipes. Propeller Co-Pack.",
    ),
    "fulfillment": (
        "Fulfillment",
        "Fulfillment and logistics for supplement and food brands. Storage, handling, and distribution support from Propeller Co-Pack in Utah.",
    ),
    "ingredient-solutions": (
        "Ingredient Solutions",
        "Ingredient sourcing and solutions for powder and supplement brands—quality, documentation, and supply alignment. Propeller Co-Pack.",
    ),
    "loading-docks": (
        "Loading Docks",
        "Receiving and shipping with dock access for materials and finished goods. Utah manufacturing facility.",
    ),
    "low-moqs": (
        "Low MOQs",
        "Minimum order quantities built for growing brands. Propeller Co-Pack Utah co-packer.",
    ),
    "manufacturing": (
        "Manufacturing",
        "Contract powder manufacturing for supplements and foods—production controls, equipment, and scale. Propeller Co-Pack Utah.",
    ),
    "packaging-design": (
        "Packaging Design",
        "Packaging design for production—pouches, cartons, labels, and shelf-ready formats. Propeller Co-Pack.",
    ),
    "powder-blending": (
        "Powder Blending",
        "Contract powder blending for supplements and foods. Consistent batches, documentation, and production controls with Propeller Co-Pack.",
    ),
    "product-development": (
        "Product Development",
        "Product development for new products and line extensions in powders and supplements. Propeller Co-Pack Utah.",
    ),
    "product-testing": (
        "Product Testing",
        "Quality and testing coordination as part of your co-packing program. Propeller Co-Pack.",
    ),
    "quality-compliance": (
        "Quality & Compliance",
        "Regulatory alignment and documentation for food and supplement manufacturing. Propeller Co-Pack.",
    ),
    "sachet-packaging": (
        "Sachet Packaging",
        "Single-serve sachet filling for powders and supplements. Co-packing with Propeller Co-Pack.",
    ),
    "stand-up-pouches": (
        "Stand Up Pouches",
        "Stand-up pouch filling and co-packing for retail-ready products. Propeller Co-Pack Utah.",
    ),
    "stick-pack-packaging": (
        "Stick Pack Packaging",
        "Stick pack filling for on-the-go nutrition and functional blends. Propeller Co-Pack contract manufacturing.",
    ),
    "turn-key-co-packing": (
        "Turn-Key Co-Packing",
        "End-to-end manufacturing from formulation through fulfillment. Full-service co-packer Propeller Co-Pack.",
    ),
    "white-label": (
        "White Label",
        "White label and private label powder manufacturing for your brand. Propeller Co-Pack Utah.",
    ),
}

CONTACT_BLOCK = """			<div class="col-md-6 text-start">
				<div>
<div class="propeller-form-wrap">
  <form id="contactForm">
    <div class="propeller-form-group">
      <label for="name">Name</label>
      <input id="name" name="name" type="text" required />
    </div>

    <div class="propeller-form-group">
      <label for="company">Company</label>
      <input id="company" name="company" type="text" required />
    </div>

    <div class="propeller-form-group">
      <label for="phone">Phone</label>
      <input id="phone" name="phone" type="tel" required />
    </div>

    <div class="propeller-form-group">
      <label for="email">Email</label>
      <input id="email" name="email" type="email" required />
    </div>

    <div class="propeller-form-group">
      <label for="message">Message</label>
      <textarea id="message" name="message" required></textarea>
    </div>

    <div class="propeller-checkbox-row">
      <input id="marketingOptIn" name="marketingOptIn" type="checkbox" />
      <label for="marketingOptIn">
        Check this box to receive Propeller updates. Opt out at any time.
      </label>
    </div>

    <button class="propeller-submit" type="submit">Submit</button>
  </form>

  <p id="status" aria-live="polite"></p>
</div>
				</div>
			</div>"""

FORM_PATTERN = re.compile(
    r'<div class="col-md-6 text-start">\s*<form id="form_[^"]*"[\s\S]*?</form>\s*</div>',
    re.MULTILINE,
)


def inject_og_tags(html: str, title: str, description: str, canonical_url: str) -> str:
    if 'property="og:title"' in html:
        return html
    og_block = f"""\t<meta property="og:title" content="{title}">
\t<meta property="og:description" content="{description}">
\t<meta property="og:url" content="{canonical_url}">
\t<meta property="og:type" content="website">
\t<meta property="og:image" content="https://propellercopack.com/img/Propeller-Nutri-3.png">
\t<meta property="og:locale" content="en_US">
\t<meta name="twitter:card" content="summary_large_image">
\t<meta name="twitter:title" content="{title}">
\t<meta name="twitter:description" content="{description}">
\t<meta name="twitter:image" content="https://propellercopack.com/img/Propeller-Nutri-3.png">
"""
    return html.replace(
        '\t<meta name="robots" content="index, follow">\n',
        '\t<meta name="robots" content="index, follow">\n' + og_block,
        1,
    )


def process_file(path: Path) -> None:
    slug = path.parent.name
    if slug not in PAGE_META:
        print(f"skip (no meta): {path}")
        return

    title_part, description = PAGE_META[slug]
    full_title = title_part + BRAND_SUFFIX
    canonical_url = f"https://propellercopack.com/{slug}/"

    text = path.read_text(encoding="utf-8")

    text = text.replace("<html>", '<html lang="en">', 1)
    text = re.sub(r"<title>[^<]*</title>", f"<title>{full_title}</title>", text, count=1)
    text = re.sub(
        r'<meta name="description" content=""[^>]*>',
        f'<meta name="description" content="{description}">',
        text,
        count=1,
    )

    canon_m = re.search(
        r'<link rel="canonical" href="(https://propellercopack\.com/[^"]+)">', text
    )
    og_url = canon_m.group(1) if canon_m else canonical_url
    text = inject_og_tags(text, full_title, description, og_url)

    if "contact-form.css" not in text:
        text = text.replace(
            '\t<link rel="stylesheet" type="text/css" href="../css/all.min.css">\n',
            '\t<link rel="stylesheet" type="text/css" href="../css/all.min.css">\n'
            '\t<link rel="stylesheet" type="text/css" href="../css/contact-form.css">\n',
            1,
        )

    text = text.replace(
        "blending, flexible filling options,",
        "blending, filling options,",
    )

    if "propeller-form-wrap" not in text:
        text, n = FORM_PATTERN.subn(CONTACT_BLOCK, text, count=1)
        if n != 1:
            print(f"WARN form replace count={n}: {path}")

    text = text.replace(
        '<script src="../js/jqBootstrapValidation.js"></script>\n\n',
        "",
    )
    text = text.replace(
        '<script src="../js/jqBootstrapValidation.js"></script>\r\n\r\n',
        "",
    )
    text = text.replace('<script src="../js/formHandler.js?6181"></script>\n', "")
    text = text.replace('<script src="../js/formHandler.js?6181"></script>\r\n', "")

    if "propeller-contact.js" not in text:
        text = text.replace(
            '<script src="../js/blocs.min.js?2597"></script>\n',
            '<script src="../js/blocs.min.js?2597"></script>\n'
            '<script src="../js/propeller-contact.js" defer></script>\n',
            1,
        )

    text = text.replace('alt="Square%20Logo%20Small"', 'alt="Propeller Copack logo"')

    path.write_text(text, encoding="utf-8")
    print(f"updated: {path.relative_to(ROOT)}")


def main() -> None:
    for folder in sorted(ROOT.iterdir()):
        if not folder.is_dir():
            continue
        idx = folder / "index.html"
        if not idx.is_file():
            continue
        if folder.name in ("css", "js", "img", "fonts", "includes", "tools"):
            continue
        process_file(idx)


if __name__ == "__main__":
    main()
