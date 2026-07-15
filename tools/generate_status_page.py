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
EXCLUDE = {"seo", "status", "it", "img", "js", "css", "fonts", "includes", "tools", "src", "worker"}

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
        cls = "good" if row["status"] == "synced" else "warn"
        map_rows.append(
            f'<tr><td><span class="mono">{html.escape(row["src_slug"])}</span></td>'
            f'<td><span class="mono">/{html.escape(row["live_slug"])}/</span></td>'
            f'<td class="{cls}">{html.escape(row["status"])}</td></tr>'
        )

    live_only = ", ".join(f"/{s}/" for s in deploy["live_only_pages"]) or "—"
    src_only = ", ".join(f"/{s}/" for s in deploy["src_only_pages"]) or "—"

    return f"""
  <section id="src-deploy">
    <h2>Src deployment (v3)</h2>
    <p>Design source: <strong>{html.escape(deploy["src_label"])}</strong> at <span class="mono">{html.escape(deploy["src_path"])}</span></p>
    <table>
      <tbody>
        <tr><th>Deployment version ID</th><td><span class="mono">{html.escape(deploy["src_version_id"])}</span></td></tr>
        <tr><th>Src last modified</th><td>{html.escape(deploy["src_last_modified"])}</td></tr>
        <tr><th>Src pages</th><td>{deploy["src_page_count"]}</td></tr>
        <tr><th>Live service pages</th><td>{deploy["live_service_count"]}</td></tr>
        <tr><th>Live public pages</th><td>{deploy["live_public_count"]} (includes homepage)</td></tr>
        <tr><th>Mapped slugs</th><td>{deploy["mapped_page_count"]}</td></tr>
        <tr><th>Live-only pages</th><td>{html.escape(live_only)}</td></tr>
        <tr><th>Src-only pages</th><td>{html.escape(src_only)}</td></tr>
      </tbody>
    </table>

    <h3>Src → live slug map</h3>
    <table>
      <thead><tr><th>Src slug</th><th>Live URL</th><th>Status</th></tr></thead>
      <tbody>
        {''.join(map_rows)}
      </tbody>
    </table>
    <p class="muted">Apply src to live site: <span class="mono">python tools/apply_v3_from_src.py</span></p>
  </section>
"""


def render_hero_section(hero: dict) -> str:
    if not hero["exists"]:
        return """
  <section id="hero-status">
    <h2>Hero image library</h2>
    <p class="bad">Hero index not generated. Run <span class="mono">python tools/rebuild_hero_index.py</span>.</p>
  </section>
"""
    return f"""
  <section id="hero-status">
    <h2>Hero image library</h2>
    <p><strong>{hero["service_count"]}</strong> service hero entries indexed from live page <span class="mono">picture</span> tags.</p>
    <p><a href="./hero-images/">Open hero image library →</a></p>
    <p class="muted">Regenerate: <span class="mono">python tools/rebuild_hero_index.py</span></p>
  </section>
"""


def build_page(deploy: dict, seo_html: str, hero: dict) -> str:
    now = deploy["generated_on"]
    audit_date = json.loads(AUDIT_CACHE.read_text(encoding="utf-8"))["generated_on"] if AUDIT_CACHE.is_file() else "—"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow, noarchive">
  <title>Site Status - Propeller Co-Pack</title>
  <style>
    :root {{
      --bg: #fff;
      --surface: #f6f8fa;
      --text: #1f2328;
      --muted: #656d76;
      --border: #d0d7de;
      --accent: #0969da;
      --good: #1a7f37;
      --warn: #9a6700;
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
    h1 {{ margin: 0 0 0.35rem; font-size: 1.85rem; }}
    h2 {{
      margin: 2rem 0 0.75rem;
      padding-bottom: 0.25rem;
      border-bottom: 1px solid var(--border);
      color: var(--accent);
      font-size: 1.2rem;
    }}
    h3 {{ margin: 1.25rem 0 0.5rem; font-size: 1.05rem; color: var(--text); }}
    p {{ margin: 0 0 0.85rem; color: var(--muted); }}
    p.muted {{ font-size: 0.92rem; }}
    ul {{ margin: 0 0 1rem; padding-left: 1.25rem; color: var(--muted); }}
    li {{ margin-bottom: 0.35rem; }}
    a {{ color: var(--accent); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 0.75rem 0 1rem;
      font-size: 0.92rem;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 0.5rem 0.6rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: var(--surface); width: 12rem; }}
    thead th {{ width: auto; }}
    .mono {{
      font-family: ui-monospace, "Cascadia Code", monospace;
      background: var(--surface);
      border-radius: 4px;
      padding: 0.1em 0.35em;
      font-size: 0.88em;
    }}
    .score {{
      border: 1px solid var(--border);
      border-left: 4px solid var(--accent);
      border-radius: 6px;
      padding: 0.8rem 1rem;
      background: var(--surface);
      margin: 0.75rem 0 1rem;
    }}
    .big {{ font-size: 1.65rem; font-weight: 700; }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .bad {{ color: var(--bad); }}
    .nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem 1.25rem;
      margin: 1rem 0 1.5rem;
      padding: 0.75rem 1rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    .nav a {{ text-decoration: none; font-weight: 600; }}
    .nav a:hover {{ text-decoration: underline; }}
    .meta-bar {{
      font-size: 0.92rem;
      color: var(--muted);
      margin-bottom: 1rem;
    }}
    .task-groups {{
      display: grid;
      gap: 0.85rem;
      margin: 0.75rem 0 1.25rem;
    }}
    .task-group {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem 1rem;
      background: var(--surface);
    }}
    .task-header {{
      display: flex;
      align-items: baseline;
      gap: 0.65rem;
      margin-bottom: 0.35rem;
    }}
    .task-priority {{
      flex: 0 0 auto;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      color: var(--accent);
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 0.1rem 0.45rem;
    }}
    .task-title {{
      margin: 0;
      font-size: 1rem;
      color: var(--text);
    }}
    .task-summary {{
      margin: 0 0 0.45rem;
      color: var(--muted);
    }}
    .task-pages {{
      margin: 0 0 0.55rem;
      font-size: 0.9rem;
      color: var(--muted);
    }}
    .task-prompt {{
      margin-top: 0.35rem;
    }}
    .task-prompt summary {{
      cursor: pointer;
      color: var(--accent);
      font-weight: 600;
      font-size: 0.92rem;
    }}
    .cursor-prompt {{
      margin: 0.55rem 0 0;
      padding: 0.75rem 0.85rem;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      font-family: ui-monospace, "Cascadia Code", monospace;
      font-size: 0.82rem;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-x: auto;
    }}
  </style>
</head>
<body>
  <h1>Site status dashboard</h1>
  <p class="meta-bar">Status generated: <strong>{html.escape(now)}</strong> · SEO audit date: <strong>{html.escape(audit_date)}</strong></p>

  <nav class="nav" aria-label="Status sections">
    <a href="#seo-status">SEO status</a>
    <a href="#hero-status">Hero library</a>
    <a href="./hero-images/">Hero images</a>
    <a href="#src-deploy">Src deployment</a>
  </nav>

{seo_html}
{render_hero_section(hero)}
{render_deploy_section(deploy)}

  <section id="regenerate">
    <h2>Regenerate this dashboard</h2>
    <p>From repo root:</p>
    <p><span class="mono">python tools/refresh_seo_all.py</span></p>
    <p class="muted">Runs SEO audit, hero index rebuild, and this status page in one step.</p>
  </section>
</body>
</html>
"""


def main() -> None:
    from generate_seo_report import load_audit, render_report

    deploy = deploy_status()
    hero = hero_summary()
    seo_html = render_report(load_audit())
    STATUS_HTML.parent.mkdir(parents=True, exist_ok=True)
    STATUS_HTML.write_text(build_page(deploy, seo_html, hero), encoding="utf-8")
    print(f"wrote {STATUS_HTML.relative_to(ROOT)}")
    print(f"wrote {DEPLOY_CACHE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
