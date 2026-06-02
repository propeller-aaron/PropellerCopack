"""Apply PropellerCopack v.3 design/content from src/ to the production site root."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "PropellerCopack v.3"

# v.3 export slugs -> live site slugs (preserve existing SEO URLs)
SLUG_MAP: dict[str, str] = {
    "3pl-logistics": "fulfillment",
    "contract-manufacturing": "manufacturing",
    "custom-formulation-and-testing": "product-testing",
    "custom-product-development": "custom-projects",
    "distribution-center": "distribution-center",
    "ingredient-solutions": "ingredient-solutions",
    "kitting-and-assembly": "kitting-and-assembly",
    "new-product-development": "product-development",
    "packaging-design": "packaging-design",
    "powder-blending": "powder-blending",
    "product-reformulation": "formulation",
    "quality-and-compliance": "quality-compliance",
    "startup-friendly-low-moqs": "low-moqs",
    "turnkey-solutions": "turn-key-co-packing",
    "white-label": "white-label",
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

INLINE_FORM_STYLE = re.compile(
    r"<style>\s*\.propeller-form-wrap[\s\S]*?</style>\s*",
    re.MULTILINE,
)

INLINE_FORM_SCRIPT = re.compile(
    r"<script>\s*const WORKER_SEND_ENDPOINT[\s\S]*?</script>\s*",
    re.MULTILINE,
)

HEAD_RE = re.compile(r"<head>[\s\S]*?</head>", re.IGNORECASE)
BODY_RE = re.compile(r"(<body[^>]*>)([\s\S]*)(</body>)", re.IGNORECASE)

ROOT_SCRIPTS = """<!-- Additional JS --><script src="./js/jquery.min.js"></script>


<script src="./js/bootstrap.bundle.min.js?3128"></script>
<script src="./js/blocs.min.js?2597"></script>
<script src="./js/propeller-contact.js" defer></script>
<script src="./js/lazysizes.min.js" defer></script>
<!-- Additional JS END -->"""

INNER_SCRIPTS = """<!-- Additional JS --><script src="../js/jquery.min.js"></script>


<script src="../js/bootstrap.bundle.min.js?3128"></script>
<script src="../js/blocs.min.js?2597"></script>
<script src="../js/propeller-contact.js" defer></script>
<script src="../js/lazysizes.min.js" defer></script>
<!-- Additional JS END -->"""


def copy_assets() -> None:
    shutil.copy2(SRC / "style.css", ROOT / "style.css")

    for name in ("bootstrap.min.css", "all.min.css"):
        shutil.copy2(SRC / "css" / name, ROOT / "css" / name)

    for name in (
        "jquery.min.js",
        "bootstrap.bundle.min.js",
        "blocs.min.js",
        "lazysizes.min.js",
    ):
        shutil.copy2(SRC / "js" / name, ROOT / "js" / name)

    shutil.copy2(SRC / "favicon.png", ROOT / "favicon.png")

    for img in (SRC / "img").iterdir():
        if img.is_file():
            shutil.copy2(img, ROOT / "img" / img.name)

    print("assets copied from src")


def rewrite_slug_hrefs(html: str, *, is_root: bool) -> str:
    prefix = "./" if is_root else "../"
    for src_slug, main_slug in sorted(SLUG_MAP.items(), key=lambda x: -len(x[0])):
        html = html.replace(f'href="{prefix}{src_slug}/"', f'href="{prefix}{main_slug}/"')
        html = html.replace(f"href='{prefix}{src_slug}/'", f"href='{prefix}{main_slug}/'")
        html = html.replace(
            f"https://propellercopack.com/{src_slug}/",
            f"https://propellercopack.com/{main_slug}/",
        )

    if is_root:
        html = re.sub(
            r'(<a class="link-style" href="\./">Product Reformulation</a>)',
            r'<a class="link-style" href="./formulation/">Product Reformulation</a>',
            html,
        )
    else:
        html = re.sub(
            r'(<a class="link-style" href="\.\./">Product Reformulation</a>)',
            r'<a class="link-style" href="../formulation/">Product Reformulation</a>',
            html,
        )
    return html


CONTACT3_PICTURE_LINK = re.compile(
    r'<a href="#(?:bloc-5|bloc-6)">(\s*<picture>[\s\S]*?Contact3\.[\s\S]*?</picture>\s*)</a>'
)
CONTACT3_TEL = "tel:+18007888689"


def update_contact_header(html: str, *, is_root: bool) -> str:
    del is_root  # Contact3 graphic always dials toll-free number shown in the image
    html = html.replace("Contact2.webp", "Contact3.webp")
    html = html.replace("Contact2.png", "Contact3.png")
    html = CONTACT3_PICTURE_LINK.sub(
        f'<a href="{CONTACT3_TEL}">\\1</a>',
        html,
    )
    html = html.replace(
        'alt="Contact" width="338" height="110">',
        'alt="Call 800-788-8689" width="338" height="110">',
    )
    return html


HOMEPAGE_FORM_WRAP = re.compile(
    r'<div class="propeller-form-wrap">[\s\S]*?</div>\s*(?=</div>\s*</div>\s*</div>\s*</div>\s*<!-- bloc-6 END -->)',
    re.MULTILINE,
)

HOMEPAGE_FORM_INNER = """<div class="propeller-form-wrap">
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
</div>"""


def fix_homepage_bloc6_structure(body: str) -> str:
    """Ensure bloc-6 form column closes before the footer."""
    broken = "</div></div>\n\t\t</div>\n\t</div>\n</div>\n<!-- bloc-6 END -->"
    fixed = (
        "</div>\n\t\t\t\t</div>\n\t\t\t</div>\n\t\t</div>\n\t</div>\n</div>\n<!-- bloc-6 END -->"
    )
    if broken in body:
        body = body.replace(broken, fixed)
        print("  fixed homepage bloc-6 div structure")
    return body


def replace_forms(html: str, *, is_root: bool = False) -> str:
    html = INLINE_FORM_STYLE.sub("", html)
    html = INLINE_FORM_SCRIPT.sub("", html)
    if is_root:
        html, home_count = HOMEPAGE_FORM_WRAP.subn(HOMEPAGE_FORM_INNER, html, count=1)
        if home_count:
            print(f"  replaced homepage contact form")
        html = fix_homepage_bloc6_structure(html)
    html, count = FORM_PATTERN.subn(CONTACT_BLOCK, html)
    if count:
        print(f"  replaced {count} legacy form(s)")
    return html


def fix_footer(html: str) -> str:
    html = html.replace('alt="Square%20Logo%20Small"', 'alt="Propeller Copack logo"')
    html = re.sub(
        r"Phone: \(801\) 221-5999<br>Toll Free: \(800\) 788-8689<br>",
        'Phone: <a href="tel:+18012215999">(801) 221-5999</a><br>'
        'Toll Free: <a href="tel:+18007888689">(800) 788-8689</a><br>',
        html,
    )
    return html


def replace_scripts(html: str, *, is_root: bool) -> str:
    scripts = ROOT_SCRIPTS if is_root else INNER_SCRIPTS
    return re.sub(
        r"<!-- Additional JS -->[\s\S]*?<!-- Additional JS END -->",
        scripts,
        html,
        count=1,
    )


def add_homepage_feature_links(body: str) -> str:
    linked = """<!-- bloc-2 -->
<div class="bloc bgc-6037 d-bloc" id="bloc-2">
	<div class="container bloc-lg bloc-sm-lg">
		<div class="row">
			<div class="col-md-4">
				<a href="./formulation/" class="text-decoration-none text-reset d-block">
				<picture><source type="image/webp" srcset="img/lazyload-ph.png" data-srcset="img/Ingredients.webp"><img src="img/lazyload-ph.png" data-src="img/Ingredients.png" class="img-fluid mx-auto d-block lazyload" alt="Custom Formulations" width="312" height="312"></picture>
				<h3 class="mg-md h3-1-feature-title-style text-lg-center mx-auto d-block text-center">
					Custom Formulations
				</h3>
				</a>
			</div>
			<div class="col-md-4">
				<a href="./product-development/" class="text-decoration-none text-reset d-block">
				<picture><source type="image/webp" srcset="img/lazyload-ph.png" data-srcset="img/Formulation.webp"><img src="img/lazyload-ph.png" data-src="img/Formulation.png" class="img-fluid mx-auto d-block lazyload" alt="Product Development" width="312" height="312"></picture>
				<h3 class="mg-md h3-feature-title-style text-lg-center mx-auto d-block text-center">
					Product Development
				</h3>
				</a>
			</div>
			<div class="col-md-4">
				<a href="./manufacturing/" class="text-decoration-none text-reset d-block">
				<picture><source type="image/webp" srcset="img/lazyload-ph.png" data-srcset="img/Conveyor%20Belt.webp"><img src="img/lazyload-ph.png" data-src="img/Conveyor%20Belt.png" class="img-fluid img-manufacturi-style mx-auto d-block lazyload" alt="Manufacturing" width="312" height="312"></picture>
				<h3 class="mg-md h3-3-style text-lg-center mx-auto d-block text-center">
					Manufacturing
				</h3>
				</a>
			</div>
		</div>
	</div>
</div>
<!-- bloc-2 END -->

<!-- bloc-3 -->
<div class="bloc bgc-5265 d-bloc" id="bloc-3">
	<div class="container bloc-lg">
		<div class="row">
			<div class="col text-center">
				<h2 class="mg-md h3-style">
					CUSTOM PACKAGING OPTIONS<br>
				</h2>
			</div>
		</div>
		<div class="row voffset">
			<div class="col-lg-3 col-md-6 text-center">
				<a href="./sachet-packaging/" class="text-decoration-none text-reset d-block">
				<picture><source type="image/webp" srcset="img/lazyload-ph.png" data-srcset="img/Sachet%20Line%20Art%20%28White%29.webp"><img src="img/lazyload-ph.png" data-src="img/Sachet%20Line%20Art%20%28White%29.png" class="img-fluid mx-auto d-block lazyload" alt="Sachet line art (white)" width="267" height="267"></picture>
				<h4 class="mg-md h3-john-doe-style">
					Sachets
				</h4>
				</a>
			</div>
			<div class="col-lg-3 col-md-6 text-center">
				<a href="./stick-pack-packaging/" class="text-decoration-none text-reset d-block">
				<picture><source type="image/webp" srcset="img/lazyload-ph.png" data-srcset="img/Stick%20Line%20Art%20%28White%29.webp"><img src="img/lazyload-ph.png" data-src="img/Stick%20Line%20Art%20%28White%29.png" class="img-fluid mx-auto d-block lazyload" alt="Stick line art (white)" width="267" height="258"></picture>
				<h4 class="mg-md h3-stick-packs-style">
					Stick Packs
				</h4>
				</a>
			</div>
			<div class="col-lg-3 col-md-6 text-center">
				<a href="./stand-up-pouches/" class="text-decoration-none text-reset d-block">
				<picture><source type="image/webp" srcset="img/lazyload-ph.png" data-srcset="img/Pouch%20Line%20Art%20%28White%29.webp"><img src="img/lazyload-ph.png" data-src="img/Pouch%20Line%20Art%20%28White%29.png" class="img-fluid mx-auto d-block lazyload" alt="Pouch line art (white)" width="267" height="267"></picture>
				<h4 class="mg-md h3-1-style">
					Stand Up Pouches
				</h4>
				</a>
			</div>
			<div class="col-lg-3 col-md-6 text-center">
				<a href="./bottles-and-jars/" class="text-decoration-none text-reset d-block">
				<picture><source type="image/webp" srcset="img/lazyload-ph.png" data-srcset="img/Jar%20Line%20Art%20%28White%29.webp"><img src="img/lazyload-ph.png" data-src="img/Jar%20Line%20Art%20%28White%29.png" class="img-fluid mx-auto d-block lazyload" alt="Jar line art (white)" width="267" height="267"></picture>
				<h4 class="mg-md h3-2-style">
					Bottles / Jars
				</h4>
				</a>
			</div>
		</div>
	</div>
</div>
<!-- bloc-3 END -->"""
    updated, count = re.subn(
        r"<!-- bloc-2 -->[\s\S]*?<!-- bloc-3 END -->",
        linked,
        body,
        count=1,
    )
    if count:
        print("  added homepage feature/packaging links")
    return updated


def transform_body(body: str, *, is_root: bool) -> str:
    body = rewrite_slug_hrefs(body, is_root=is_root)
    body = update_contact_header(body, is_root=is_root)
    body = replace_forms(body, is_root=is_root)
    if is_root:
        body = add_homepage_feature_links(body)
    body = fix_footer(body)
    body = replace_scripts(body, is_root=is_root)
    return body


def merge_page(main_path: Path, src_path: Path, *, is_root: bool = False) -> None:
    main_html = main_path.read_text(encoding="utf-8")
    src_html = src_path.read_text(encoding="utf-8")

    head_match = HEAD_RE.search(main_html)
    body_match = BODY_RE.search(src_html)
    html_open = re.search(r"<!doctype html>\s*<html[^>]*>", main_html, re.IGNORECASE)
    if not head_match or not body_match or not html_open:
        print(f"WARN: could not merge {main_path}")
        return

    body_open, body_content, body_close = body_match.groups()
    body_content = transform_body(body_content, is_root=is_root)
    merged = (
        f"{html_open.group(0)}\n"
        f"{head_match.group(0)}\n"
        f"{body_open}{body_content}{body_close}\n"
        "</html>\n"
    )

    main_path.write_text(merged, encoding="utf-8")
    print(f"merged: {main_path.relative_to(ROOT)}")


def patch_unmapped_pages() -> None:
    mapped_targets = set(SLUG_MAP.values()) | {"index.html"}
    skip_dirs = {
        "css",
        "js",
        "img",
        "fonts",
        "includes",
        "tools",
        "seo",
        "status",
        "worker",
        "src",
    }

    for folder in sorted(ROOT.iterdir()):
        if not folder.is_dir() or folder.name in skip_dirs:
            continue
        idx = folder / "index.html"
        if not idx.is_file() or folder.name in mapped_targets:
            continue

        text = idx.read_text(encoding="utf-8")
        updated = update_contact_header(text, is_root=False)
        updated = replace_scripts(updated, is_root=False)
        if updated != text:
            idx.write_text(updated, encoding="utf-8")
            print(f"patched header/scripts: {idx.relative_to(ROOT)}")


def update_index_meta() -> None:
    src_index = (SRC / "index.html").read_text(encoding="utf-8")
    main_index = ROOT / "index.html"
    text = main_index.read_text(encoding="utf-8")

    for attr in ("keywords", "description"):
        m = re.search(
            rf'<meta name="{attr}" content="([^"]*)"',
            src_index,
        )
        if m:
            text = re.sub(
                rf'<meta name="{attr}" content="[^"]*"',
                f'<meta name="{attr}" content="{m.group(1)}"',
                text,
                count=1,
            )

    main_index.write_text(text, encoding="utf-8")
    print("updated index meta from src")


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Source folder not found: {SRC}")

    copy_assets()

    merge_page(ROOT / "index.html", SRC / "index.html", is_root=True)

    for src_slug, main_slug in SLUG_MAP.items():
        src_page = SRC / src_slug / "index.html"
        main_page = ROOT / main_slug / "index.html"
        if not src_page.is_file():
            print(f"skip missing src page: {src_slug}")
            continue
        if not main_page.is_file():
            print(f"skip missing main page: {main_slug}")
            continue
        merge_page(main_page, src_page, is_root=False)

    patch_unmapped_pages()
    update_index_meta()
    print("v3 migration complete")


if __name__ == "__main__":
    main()
