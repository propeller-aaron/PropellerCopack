"""Build SEO report HTML sections from audit-cache.json."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "seo" / "audit-cache.json"


def score_page(row: dict) -> tuple[int, list[str], list[str]]:
    good: list[str] = []
    bad: list[str] = []
    score = 100

    if not (row["title_present"] and row["description_present"] and row["canonical_present"]):
        score -= 25
        bad.append("Missing title, meta description, or canonical")
    else:
        good.append("Metadata complete")

    if row["h1_count"] != 1:
        score -= 20
        bad.append(f"H1 count is {row['h1_count']} (expected 1)")
    else:
        good.append("Single H1")

    if row["description_has_html"]:
        score -= 15
        bad.append("Meta description contains HTML markup")
    else:
        good.append("Clean meta description")

    wc = row["word_count"]
    if wc < 250:
        score -= 12
        bad.append(f"Thin content (~{wc} words)")
    elif wc < 400:
        score -= 6
        bad.append(f"Moderate depth (~{wc} words)")
    else:
        good.append(f"Solid depth (~{wc} words)")

    if len(row["title_text"]) > 60:
        score -= 3
        bad.append("Title may be long for SERP display")
    else:
        good.append("Title length OK")

    score = max(0, min(100, score))
    return score, good, bad


def score_site(audit: dict) -> tuple[int, dict[str, int]]:
    rows = audit["rows"]
    page_scores = {r["slug"]: score_page(r)[0] for r in rows}
    avg_page = sum(page_scores.values()) / max(len(page_scores), 1)

    basic = 25 if not audit["missing_meta_slugs"] else 10
    structure = 20 if not audit["bad_h1_slugs"] else 8
    content = 20
    thin = sum(1 for r in rows if r["word_count"] < 250)
    content -= min(12, thin * 2)
    links = 15
    if audit.get("pagerank_top"):
        links = 13 if len(audit["pagerank_top"]) >= 5 else 10
    live = audit["live_checks"]
    health = 20 if live.get("bad_count", 1) == 0 else max(0, 20 - live.get("bad_count", 0) * 4)

    total = round(basic + structure + content + links + health)
    breakdown = {
        "basic": basic,
        "structure": structure,
        "content": content,
        "links": links,
        "health": health,
    }
    return total, breakdown, page_scores, avg_page


def build_tasks(audit: dict, page_scores: dict[str, int]) -> list[tuple[str, str]]:
    tasks: list[tuple[str, str]] = []
    for slug in audit.get("desc_html_slugs", []):
        tasks.append(("P1", f"Fix HTML inside meta description on {slug}"))
    for slug in audit.get("bad_h1_slugs", []):
        tasks.append(("P1", f"Fix H1 count on {slug}"))
    for slug in audit.get("missing_meta_slugs", []):
        tasks.append(("P1", f"Add missing metadata on {slug}"))

    thin = [r for r in audit["rows"] if r["word_count"] < 250 and r["slug"] != "/"]
    if thin:
        tasks.append(
            (
                "P2",
                f"Expand content depth on {len(thin)} service pages (target 600-900 words)",
            )
        )

    low = sorted(
        ((s, sc) for s, sc in page_scores.items() if s != "/" and sc < 78),
        key=lambda x: x[1],
    )
    for slug, sc in low[:3]:
        tasks.append(("P2", f"Improve on-page quality on {slug} (score {sc}/100)"))

    if audit["live_checks"].get("bad_count", 0):
        tasks.append(("P1", "Fix non-200 sitemap URLs (see live checks table)"))

    if not tasks:
        tasks.append(("—", "No critical SEO blockers detected in this run"))
    return tasks


def render_report(audit: dict) -> str:
    kpi, breakdown, page_scores, avg_page = score_site(audit)
    tasks = build_tasks(audit, page_scores)
    live = audit["live_checks"]
    generated = audit["generated_on"]
    page_count = audit["page_count"]

    kpi_class = "good" if kpi >= 85 else "warn" if kpi >= 70 else "bad"

    task_items = "\n".join(
        f'    <li><strong>{prio}:</strong> {html.escape(msg)}</li>' for prio, msg in tasks
    )

    per_page_rows = []
    for row in sorted(audit["rows"], key=lambda r: r["slug"]):
        if row["slug"] == "/":
            continue
        sc, good, bad = score_page(row)
        cls = "good" if sc >= 82 else "warn" if sc >= 75 else "bad"
        status = "<br>".join(
            [f"✅ {html.escape(g)}" for g in good[:2]]
            + [f"❌ {html.escape(b)}" for b in bad[:2]]
        )
        per_page_rows.append(
            f'<tr><td>{html.escape(row["slug"])}</td>'
            f'<td class="{cls}">{sc}/100</td>'
            f'<td>{status}</td>'
            f'<td><span class="mono">~{row["word_count"]} words</span></td></tr>'
        )

    pr_rows = []
    for slug, pr in audit.get("pagerank_top", [])[:8]:
        sc = page_scores.get(slug, "—")
        pr_rows.append(
            f'<tr><td>{html.escape(slug)}</td><td>{pr:.4f}</td>'
            f'<td class="{"good" if isinstance(sc, int) and sc >= 82 else "warn"}">{sc}/100</td></tr>'
        )

    live_rows = []
    for item in live.get("results", []):
        ok = item["status"] == 200
        live_rows.append(
            f'<tr><td>{html.escape(item["url"])}</td>'
            f'<td class="{"good" if ok else "bad"}">{item["status"] or "ERR"}</td>'
            f'<td>{html.escape(item.get("error", ""))}</td></tr>'
        )

    return f"""
  <section id="seo-status">
    <h2>SEO status</h2>
    <p>Audit date: <strong>{html.escape(generated)}</strong>. Covers <strong>{page_count}</strong> public pages. Average page score: <strong>{avg_page:.0f}/100</strong>.</p>
    <div class="score">
      <div class="big {kpi_class}">KPI: {kpi}/100</div>
      <p>Combines metadata setup, H1 structure, content depth, internal link graph, and live sitemap HTTP checks.</p>
    </div>

    <h3>Priority tasks</h3>
    <ul>
{task_items}
    </ul>

    <h3>Score breakdown</h3>
    <table>
      <thead><tr><th>Category</th><th>Weight</th><th>Score</th></tr></thead>
      <tbody>
        <tr><td>Basic SEO setup</td><td>25</td><td class="good">{breakdown["basic"]}</td></tr>
        <tr><td>Page structure</td><td>20</td><td class="{"good" if breakdown["structure"] >= 18 else "warn"}">{breakdown["structure"]}</td></tr>
        <tr><td>Content quality</td><td>20</td><td class="{"good" if breakdown["content"] >= 16 else "warn"}">{breakdown["content"]}</td></tr>
        <tr><td>Internal links</td><td>15</td><td class="good">{breakdown["links"]}</td></tr>
        <tr><td>Live site health</td><td>20</td><td class="{"good" if breakdown["health"] >= 18 else "bad"}">{breakdown["health"]}</td></tr>
      </tbody>
    </table>

    <h3>Per-page scores</h3>
    <table>
      <thead><tr><th>Page</th><th>Score</th><th>Status</th><th>Words</th></tr></thead>
      <tbody>
        {''.join(per_page_rows)}
      </tbody>
    </table>

    <h3>PageRank proxy (top internal URLs)</h3>
    <table>
      <thead><tr><th>URL</th><th>PageRank proxy</th><th>Page score</th></tr></thead>
      <tbody>
        {''.join(pr_rows)}
      </tbody>
    </table>

    <h3>Live sitemap checks ({live.get("total", 0) - live.get("bad_count", 0)}/{live.get("total", 0)} OK)</h3>
    <table>
      <thead><tr><th>URL</th><th>HTTP</th><th>Error</th></tr></thead>
      <tbody>
        {''.join(live_rows)}
      </tbody>
    </table>
  </section>
"""


def load_audit() -> dict:
    return json.loads(CACHE.read_text(encoding="utf-8"))


def main() -> None:
    audit = load_audit()
    print(render_report(audit))


if __name__ == "__main__":
    main()
