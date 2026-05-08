from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEO_HERO = ROOT / "seo" / "hero-images" / "index.html"
EXCLUDE = {"seo", "img", "js", "css", "fonts", "includes", "tools"}


def collect_service_pages() -> list[Path]:
    return sorted(
        [p for p in ROOT.glob("*/index.html") if p.parent.name not in EXCLUDE],
        key=lambda p: p.parent.name,
    )


def extract_service_data(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    slug = path.parent.name
    service_path = f"../../{slug}/"

    h1 = re.search(r"<h1[^>]*>\s*([^<]+?)\s*</h1>", text, re.I)
    name = h1.group(1).strip() if h1 else slug.replace("-", " ").title()

    # Prefer the main hero image in bloc-7
    block = re.search(r'<div class="bloc[^"]*" id="bloc-7">([\s\S]*?)<!-- bloc-7 END -->', text, re.I)
    scope = block.group(1) if block else text
    img = re.search(r'<img[^>]+(?:data-src|src)="([^"]+)"[^>]*alt="([^"]*)"', scope, re.I)
    if not img:
        return None
    image_url = img.group(1).replace("../", "../../")
    alt_text = img.group(2).strip() or f"{name} hero image"

    return {
        "name": name,
        "path": service_path,
        "imageUrl": image_url,
        "altText": alt_text,
    }


def build_html(services: list[dict]) -> str:
    services_json = json.dumps(services, indent=8)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow, noarchive">
  <title>Service Hero Images - Propeller Co-Pack</title>
  <style>
    :root {{
      --bg: #fff;
      --surface: #f6f8fa;
      --text: #1f2328;
      --muted: #656d76;
      --border: #d0d7de;
      --accent: #0969da;
      --bad: #cf222e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0 auto;
      max-width: 72rem;
      padding: 2rem 1.25rem 3rem;
      font: 16px/1.6 "Segoe UI", system-ui, sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    h1 {{ margin: 0 0 0.4rem; font-size: 1.75rem; }}
    p {{ margin: 0 0 1rem; color: var(--muted); }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 0.95rem;
      margin-top: 1rem;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
      padding: 0.75rem;
    }}
    .card h2 {{
      margin: 0 0 0.35rem;
      font-size: 1rem;
      line-height: 1.35;
    }}
    .meta {{
      margin: 0 0 0.45rem;
      font-size: 0.85rem;
      color: var(--muted);
      word-break: break-all;
    }}
    .hero {{
      width: 100%;
      height: auto;
      display: block;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #4d7946;
    }}
    .error {{
      border-left: 4px solid var(--bad);
      background: #fff5f5;
      color: var(--bad);
      padding: 0.65rem 0.75rem;
      border-radius: 6px;
      margin-top: 1rem;
      white-space: pre-wrap;
    }}
  </style>
</head>
<body>
  <h1>Service Page Hero Images</h1>
  <p>Private internal page. Agent-built hero image inventory sourced from service page <span class="meta">picture</span> tags.</p>
  <p><a href="../">Back to SEO KPI page</a></p>
  <div id="grid" class="grid" aria-live="polite"></div>

  <script>
    (function () {{
      const services = {services_json};
      const grid = document.getElementById("grid");

      function cardMarkup(name, path, imageUrl, altText) {{
        const card = document.createElement("article");
        card.className = "card";

        const heading = document.createElement("h2");
        const link = document.createElement("a");
        link.href = path;
        link.textContent = name || path;
        heading.appendChild(link);

        const pathMeta = document.createElement("p");
        pathMeta.className = "meta";
        pathMeta.textContent = path;

        const imageMeta = document.createElement("p");
        imageMeta.className = "meta";
        imageMeta.textContent = imageUrl;

        const image = document.createElement("img");
        image.className = "hero";
        image.src = imageUrl;
        image.alt = altText || (name + " hero image");
        image.loading = "lazy";

        card.appendChild(heading);
        card.appendChild(pathMeta);
        card.appendChild(imageMeta);
        card.appendChild(image);
        return card;
      }}

      services.forEach(function (service) {{
        grid.appendChild(cardMarkup(service.name, service.path, service.imageUrl, service.altText));
      }});
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    services = []
    for page in collect_service_pages():
        info = extract_service_data(page)
        if info:
            services.append(info)
    SEO_HERO.write_text(build_html(services), encoding="utf-8")
    print(f"hero index rebuilt with {len(services)} services")


if __name__ == "__main__":
    main()
