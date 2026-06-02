"""Build SEO report HTML sections from audit-cache.json."""
from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "seo" / "audit-cache.json"


@dataclass(frozen=True)
class TaskGroup:
    priority: str
    title: str
    summary: str
    pages: tuple[str, ...]
    cursor_prompt: str


def slug_list(slugs: list[str], limit: int = 12) -> str:
    shown = slugs[:limit]
    text = ", ".join(shown)
    if len(slugs) > limit:
        text += f", … (+{len(slugs) - limit} more)"
    return text


def pages_by_h1_count(audit: dict) -> dict[int, list[str]]:
    groups: dict[int, list[str]] = {}
    for row in audit["rows"]:
        if row["h1_count"] != 1:
            groups.setdefault(row["h1_count"], []).append(row["slug"])
    return groups


def build_task_groups(audit: dict, page_scores: dict[str, int]) -> list[TaskGroup]:
    groups: list[TaskGroup] = []

    for slug in audit.get("desc_html_slugs", []):
        groups.append(
            TaskGroup(
                priority="P1",
                title="Remove HTML from meta descriptions",
                summary=f"Meta description contains markup on {slug}.",
                pages=(slug,),
                cursor_prompt=(
                    f"On {slug}, remove HTML tags from the meta description, Open Graph "
                    "description, and Twitter description. Keep plain text only and match "
                    "the on-page copy tone."
                ),
            )
        )

    for slug in audit.get("missing_meta_slugs", []):
        groups.append(
            TaskGroup(
                priority="P1",
                title="Add missing metadata",
                summary=f"Missing title, description, or canonical on {slug}.",
                pages=(slug,),
                cursor_prompt=(
                    f"On {slug}, add a unique title, meta description, canonical URL, and "
                    "matching Open Graph / Twitter tags. Follow patterns in "
                    "tools/update_inner_seo.py PAGE_META and existing inner pages."
                ),
            )
        )

    h1_groups = pages_by_h1_count(audit)
    if three := sorted(h1_groups.get(3, [])):
        groups.append(
            TaskGroup(
                priority="P1",
                title="Fix heading hierarchy on service pages (3 H1s)",
                summary=(
                    f"{len(three)} pages use three H1 tags: shared hero band, service title, "
                    "and contact heading."
                ),
                pages=tuple(three),
                cursor_prompt=(
                    "Fix heading hierarchy on these Propeller Co-Pack service pages so each "
                    "page has exactly one H1:\n"
                    f"{chr(10).join(three)}\n\n"
                    "Pattern on v3 pages:\n"
                    "- Keep the bloc-7 service title as the sole H1.\n"
                    "- Change the shared bloc-1 banner heading ('POWDER MANUFACTURING') to h2.\n"
                    "- Change the contact section heading ('Drop us a line...') to h2.\n"
                    "- Do not change visible styling classes unless needed.\n"
                    "- Preserve SEO meta, contact form, footer structure, and internal links.\n"
                    "- Run python tools/seo_refresh_audit.py afterward to verify h1_count is 1."
                ),
            )
        )

    if two := sorted(h1_groups.get(2, [])):
        homepage = "/" in two
        others = [s for s in two if s != "/"]
        page_lines = []
        if homepage:
            page_lines.append("/ (homepage)")
        page_lines.extend(others)
        groups.append(
            TaskGroup(
                priority="P1",
                title="Fix heading hierarchy (2 H1s)",
                summary=(
                    f"{len(two)} pages use two H1 tags, including the homepage and "
                    "legacy-format service pages."
                ),
                pages=tuple(two),
                cursor_prompt=(
                    "Fix heading hierarchy so each page has exactly one H1:\n"
                    f"{chr(10).join(page_lines)}\n\n"
                    "For inner service pages:\n"
                    "- Keep the bloc-7 service-specific title as the only H1.\n"
                    "- Demote the shared bloc-1 'POWDER MANUFACTURING' banner heading to h2.\n"
                    "For the homepage:\n"
                    "- Keep the primary page headline as the only H1.\n"
                    "- Demote secondary hero or section headings currently marked h1 to h2.\n"
                    "- Preserve layout, links, contact form, and SEO head tags.\n"
                    "- Run python tools/seo_refresh_audit.py afterward to verify h1_count is 1."
                ),
            )
        )

    thin = sorted(
        r["slug"] for r in audit["rows"] if r["word_count"] < 250 and r["slug"] != "/"
    )
    if thin:
        groups.append(
            TaskGroup(
                priority="P2",
                title="Expand thin service page content",
                summary=(
                    f"{len(thin)} service pages are under ~250 words; target 600-900 words "
                    "for stronger SEO depth."
                ),
                pages=tuple(thin),
                cursor_prompt=(
                    "Expand on-page copy on these Propeller Co-Pack service pages to "
                    "roughly 600-900 words each:\n"
                    f"{chr(10).join(thin)}\n\n"
                    "Requirements:\n"
                    "- Preserve existing title, meta description, canonical, OG/Twitter tags, "
                    "and Propeller contact form markup.\n"
                    "- Keep the v3 bloc layout; add 2-4 substantive paragraphs or bullet sections "
                    "within existing content areas.\n"
                    "- Cover capabilities, ideal use cases, quality/compliance, and workflow.\n"
                    "- Add natural internal links to related services already on the site.\n"
                    "- Match the tone of neighboring pages; no keyword stuffing.\n"
                    "- Run python tools/seo_refresh_audit.py afterward to confirm word counts."
                ),
            )
        )

    moderate = sorted(
        r["slug"]
        for r in audit["rows"]
        if 250 <= r["word_count"] < 400 and r["slug"] != "/"
    )
    if moderate:
        groups.append(
            TaskGroup(
                priority="P2",
                title="Deepen moderate-length service pages",
                summary=(
                    f"{len(moderate)} pages are ~250-400 words; expand toward 600-900 words."
                ),
                pages=tuple(moderate),
                cursor_prompt=(
                    "Expand these service pages from moderate depth toward 600-900 words:\n"
                    f"{chr(10).join(moderate)}\n\n"
                    "Add useful, non-duplicative sections while preserving SEO head tags, "
                    "contact form, hero images, and v3 styling. Prefer expanding bloc-7 body "
                    "copy and adding one supporting detail section before the contact bloc."
                ),
            )
        )

    if audit["live_checks"].get("bad_count", 0):
        bad_urls = [
            item["url"]
            for item in audit["live_checks"].get("results", [])
            if item.get("status") != 200
        ]
        groups.append(
            TaskGroup(
                priority="P1",
                title="Fix live sitemap URL failures",
                summary=f"{len(bad_urls)} sitemap URLs are not returning HTTP 200.",
                pages=tuple(bad_urls),
                cursor_prompt=(
                    "These sitemap URLs are failing live HTTP checks:\n"
                    f"{chr(10).join(bad_urls)}\n\n"
                    "Diagnose each failure (404, redirect loop, timeout, or deploy gap). "
                    "Fix routing/deploy for live pages or update sitemap.xml if the URL should "
                    "be removed. Re-run python tools/seo_refresh_audit.py to confirm all "
                    "sitemap checks pass."
                ),
            )
        )

    if not groups:
        groups.append(
            TaskGroup(
                priority="—",
                title="No critical SEO blockers",
                summary="No critical SEO blockers detected in this audit run.",
                pages=(),
                cursor_prompt=(
                    "No SEO remediation needed from the latest audit. Re-run "
                    "python tools/refresh_seo_all.py after future content or deploy changes."
                ),
            )
        )

    return groups


def render_task_groups(groups: list[TaskGroup]) -> str:
    blocks: list[str] = []
    for group in groups:
        pages_html = ""
        if group.pages:
            pages_html = (
                f'<p class="task-pages"><strong>Affected:</strong> '
                f'<span class="mono">{html.escape(slug_list(list(group.pages), limit=20))}</span></p>'
            )
        prompt = html.escape(group.cursor_prompt)
        blocks.append(
            f"""    <article class="task-group">
      <header class="task-header">
        <span class="task-priority">{html.escape(group.priority)}</span>
        <h4 class="task-title">{html.escape(group.title)}</h4>
      </header>
      <p class="task-summary">{html.escape(group.summary)}</p>
      {pages_html}
      <details class="task-prompt">
        <summary>Cursor prompt</summary>
        <pre class="cursor-prompt">{prompt}</pre>
      </details>
    </article>"""
        )
    return "\n".join(blocks)


def build_tasks(audit: dict, page_scores: dict[str, int]) -> list[tuple[str, str]]:
    """Legacy flat task list used by tests or scripts."""
    return [(group.priority, group.summary) for group in build_task_groups(audit, page_scores)]


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


def render_report(audit: dict) -> str:
    kpi, breakdown, page_scores, avg_page = score_site(audit)
    task_groups = build_task_groups(audit, page_scores)
    live = audit["live_checks"]
    generated = audit["generated_on"]
    page_count = audit["page_count"]

    kpi_class = "good" if kpi >= 85 else "warn" if kpi >= 70 else "bad"
    task_blocks = render_task_groups(task_groups)

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
    <p class="muted">Grouped remediation work with copy-ready Cursor prompts. Expand a task to copy its prompt.</p>
    <div class="task-groups">
{task_blocks}
    </div>

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
