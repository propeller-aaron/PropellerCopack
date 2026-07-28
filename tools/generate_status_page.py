"""Generate unified site status page (src deploy + SEO + hero inventory)."""
from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

SRC = ROOT / "src" / "PropellerCopack v.3"
STATUS_HTML = ROOT / "status" / "index.html"
DEPLOY_CACHE = ROOT / "status" / "deploy-status.json"
AUDIT_CACHE = ROOT / "seo" / "audit-cache.json"
HERO_INDEX = ROOT / "status" / "hero-images" / "index.html"
EXCLUDE = {"seo", "status", "img", "js", "css", "fonts", "includes", "tools", "src", "worker"}

try:
    from apply_v3_from_src import SLUG_MAP
except ImportError:  # pragma: no cover
    SLUG_MAP = {}


def file_fingerprint(path: Path) -> str:
    if not path.is_file():
        return "missing"
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:12]


def src_version_id() -> str:
    parts = [
        file_fingerprint(SRC / "index.html"),
        file_fingerprint(SRC / "style.css"),
        str(len(list(SRC.glob("*/index.html")))),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def src_last_modified() -> str:
    if not SRC.is_dir():
        return "—"
    mtimes = [p.stat().st_mtime for p in SRC.rglob("*") if p.is_file()]
    if not mtimes:
        return "—"
    return datetime.fromtimestamp(max(mtimes)).strftime("%Y-%m-%d %H:%M")


def collect_live_pages() -> list[str]:
    slugs = sorted(
        p.parent.name for p in ROOT.glob("*/index.html") if p.parent.name not in EXCLUDE
    )
    return slugs


def public_page_count(service_slugs: list[str]) -> int:
    return len(service_slugs) + 1  # include homepage


def deploy_status() -> dict:
    src_pages = sorted(p.name for p in SRC.glob("*/") if (p / "index.html").is_file())
    live_pages = collect_live_pages()
    mapped_targets = sorted(set(SLUG_MAP.values()))

    mapping_rows = []
    for src_slug, live_slug in sorted(SLUG_MAP.items()):
        src_path = SRC / src_slug / "index.html"
        live_path = ROOT / live_slug / "index.html"
        src_fp = file_fingerprint(src_path)
        live_fp = file_fingerprint(live_path)
        status = "synced"
        if not live_path.is_file():
            status = "missing live page"
        elif not src_path.is_file():
            status = "missing src page"
        elif src_fp != "missing" and live_fp != "missing":
            # Body may differ after SEO merge; compare mtime as rough staleness signal
            src_mtime = src_path.stat().st_mtime
            live_mtime = live_path.stat().st_mtime
            if live_mtime < src_mtime:
                status = "live older than src"
        mapping_rows.append(
            {
                "src_slug": src_slug,
                "live_slug": live_slug,
                "src_exists": src_path.is_file(),
                "live_exists": live_path.is_file(),
                "status": status,
            }
        )

    live_only = sorted(set(live_pages) - set(mapped_targets))
    src_only = sorted(set(src_pages) - set(SLUG_MAP.keys()))

    out = {
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "src_label": "PropellerCopack v.3",
        "src_path": "src/PropellerCopack v.3/",
        "src_version_id": src_version_id(),
        "src_last_modified": src_last_modified(),
        "src_page_count": len(src_pages),
        "live_service_count": len(live_pages),
        "live_public_count": public_page_count(live_pages),
        "mapped_page_count": len(SLUG_MAP),
        "mapping_rows": mapping_rows,
        "live_only_pages": live_only,
        "src_only_pages": src_only,
    }
    DEPLOY_CACHE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def hero_summary() -> dict:
    text = HERO_INDEX.read_text(encoding="utf-8") if HERO_INDEX.is_file() else ""
    count = text.count('"name":')
    return {
        "path": "status/hero-images/index.html",
        "service_count": count,
        "exists": HERO_INDEX.is_file(),
    }


def render_deploy_section(deploy: dict) -> str:
    map_rows = []
    for row in deploy["mapping_rows"]:
        cls = "status-ok-label" if row["status"] == "synced" else "status-muted"
        map_rows.append(
            f'<tr><td><code>{html.escape(row["src_slug"])}</code></td>'
            f'<td><code>/{html.escape(row["live_slug"])}/</code></td>'
            f'<td class="{cls}">{html.escape(row["status"])}</td></tr>'
        )

    live_only = ", ".join(f"/{s}/" for s in deploy["live_only_pages"]) or "—"
    src_only = ", ".join(f"/{s}/" for s in deploy["src_only_pages"]) or "—"

    return f"""
  <section id="src-deploy" class="status-panel">
    <h2>Src deployment (v3)</h2>
    <p class="status-detail">Design source: <strong>{html.escape(deploy["src_label"])}</strong> at <code>{html.escape(deploy["src_path"])}</code></p>
    <div class="status-table-wrap">
      <table class="status-table">
        <tbody>
          <tr><th scope="row">Deployment version ID</th><td><code>{html.escape(deploy["src_version_id"])}</code></td></tr>
          <tr><th scope="row">Src last modified</th><td>{html.escape(deploy["src_last_modified"])}</td></tr>
          <tr><th scope="row">Src pages</th><td>{deploy["src_page_count"]}</td></tr>
          <tr><th scope="row">Live service pages</th><td>{deploy["live_service_count"]}</td></tr>
          <tr><th scope="row">Live public pages</th><td>{deploy["live_public_count"]} (includes homepage)</td></tr>
          <tr><th scope="row">Mapped slugs</th><td>{deploy["mapped_page_count"]}</td></tr>
          <tr><th scope="row">Live-only pages</th><td>{html.escape(live_only)}</td></tr>
          <tr><th scope="row">Src-only pages</th><td>{html.escape(src_only)}</td></tr>
        </tbody>
      </table>
    </div>
    <h3>Src → live slug map</h3>
    <div class="status-table-wrap">
      <table class="status-table">
        <thead><tr><th scope="col">Src slug</th><th scope="col">Live URL</th><th scope="col">Status</th></tr></thead>
        <tbody>
          {''.join(map_rows)}
        </tbody>
      </table>
    </div>
    <p class="status-muted">Apply src to live site: <code>python tools/apply_v3_from_src.py</code></p>
  </section>
"""


def render_hero_section(hero: dict) -> str:
    if not hero["exists"]:
        return """
  <section id="hero-status" class="status-panel">
    <h2>Hero image library</h2>
    <p class="status-muted">Hero index not generated. Run <code>python tools/rebuild_hero_index.py</code>.</p>
  </section>
"""
    return f"""
  <section id="hero-status" class="status-panel">
    <h2>Hero image library</h2>
    <p class="status-detail"><strong>{hero["service_count"]}</strong> service hero entries indexed from live page <code>picture</code> tags.</p>
    <p><a href="./hero-images/">Open hero image library →</a></p>
    <p class="status-muted">Regenerate: <code>python tools/rebuild_hero_index.py</code></p>
  </section>
"""


NAV_ITEMS = [
    ("overview", "Overview"),
    ("findings", "Findings"),
    ("pages", "Pages"),
    ("deployment", "Deployment"),
    ("hero-library", "Hero library"),
]


def build_nav_html(counts: dict) -> str:
    items = []
    for tab_id, label in NAV_ITEMS:
        count = counts.get(tab_id)
        count_html = f'<span class="status-nav-count">{count}</span>' if count is not None else ""
        items.append(
            f'<li><button type="button" class="status-nav-btn" data-tab-target="{tab_id}">'
            f"<span>{html.escape(label)}</span>{count_html}</button></li>"
        )
    return "".join(items)


def build_page(deploy: dict, seo: dict, hero: dict) -> str:
    from status_design import STATUS_CSS, STATUS_JS

    counts = {
        "overview": seo["page_count"],
        "findings": seo["finding_count"],
        "pages": seo["page_count"],
        "deployment": deploy["mapped_page_count"],
        "hero-library": hero["service_count"] if hero["exists"] else None,
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow, noarchive">
  <title>SEO Status - Propeller Co-Pack</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font: 16px/1.6 "Segoe UI", system-ui, sans-serif;
      color: #2c2c2c;
      background: #fff;
    }}
    a {{ color: #0b3a5b; }}
    {STATUS_CSS}
  </style>
</head>
<body>
  <div class="status-app">
    <aside class="status-sidebar">
      <a class="status-brand" href="#overview">
        <span class="status-brand-title">Propeller Co-Pack</span>
        <span class="status-brand-sub">Site status dashboard</span>
      </a>
      <ul class="status-nav">{build_nav_html(counts)}</ul>
      <div class="status-sidebar-footer">
        <p>Generated {html.escape(seo["generated"])}</p>
        <p>Regenerate everything:</p>
        <code>python tools/refresh_seo_all.py</code>
      </div>
    </aside>
    <main class="status-main">
      <header class="status-topbar">
        <div>
          <p class="status-topbar-title">Internal tooling · not indexed</p>
          <p class="status-topbar-meta">{seo["page_count"]} pages · {seo["finding_count"]} findings · click any metric for culprits and fix prompts</p>
        </div>
        <div class="status-topbar-score">
          <span class="status-topbar-score-value">{seo["score"]}</span>
          <span class="status-topbar-score-label">SEO score /100</span>
        </div>
      </header>
      <div class="status-panels">
        <div class="status-shell">
          <section class="status-tab-panel" data-tab-panel="overview" tabindex="-1">{seo["overview_html"]}</section>
          <section class="status-tab-panel" data-tab-panel="findings" tabindex="-1">{seo["findings_html"]}</section>
          <section class="status-tab-panel" data-tab-panel="pages" tabindex="-1">{seo["pages_html"]}</section>
          <section class="status-tab-panel" data-tab-panel="deployment" tabindex="-1">{render_deploy_section(deploy)}</section>
          <section class="status-tab-panel" data-tab-panel="hero-library" tabindex="-1">{render_hero_section(hero)}</section>
          {seo["shared_html"]}
        </div>
      </div>
    </main>
  </div>
  <script>{STATUS_JS}</script>
</body>
</html>
"""


def main() -> None:
    from generate_seo_report import build_seo_sections, load_audit

    deploy = deploy_status()
    hero = hero_summary()
    seo = build_seo_sections(load_audit())
    STATUS_HTML.parent.mkdir(parents=True, exist_ok=True)
    STATUS_HTML.write_text(build_page(deploy, seo, hero), encoding="utf-8")
    print(f"wrote {STATUS_HTML.relative_to(ROOT)}")
    print(f"wrote {DEPLOY_CACHE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
