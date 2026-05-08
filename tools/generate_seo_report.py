"""Build seo/index.html from seo/audit-cache.json (run seo_refresh_audit.py first)."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "seo" / "audit-cache.json"
OUTPUT = ROOT / "seo" / "index.html"

LAST_UPDATED = "May 8, 2026"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        print("Missing audit cache; run: python tools/seo_refresh_audit.py", file=sys.stderr)
        sys.exit(1)
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def indegree_map(rows: list[dict]) -> dict[str, int]:
    slugs = {r["slug"] for r in rows}
    inc = {s: 0 for s in slugs}
    for r in rows:
        for link in r["internal_links"]:
            if link in inc and link != r["slug"]:
                inc[link] += 1
    return inc


def avg_service_word_count(rows: list[dict]) -> float:
    svc = [r["word_count"] for r in rows if r["slug"] != "/"]
    return sum(svc) / max(len(svc), 1)


def compute_breakdown(cache: dict) -> dict:
    rows = cache["rows"]
    n = len(rows)
    live = cache["live_checks"]
    bad = int(live.get("bad_count", 0))
    total_live = int(live.get("total", 1))

    meta_ok = sum(
        1
        for r in rows
        if r["title_present"]
        and r["description_present"]
        and r["canonical_present"]
        and not r["description_has_html"]
        and r["canonical_ok"]
    )
    basic = round(25 * meta_ok / max(n, 1))

    h1_ok = sum(1 for r in rows if r["h1_count"] == 1)
    structure = round(20 * h1_ok / max(n, 1))

    avg_svc = avg_service_word_count(rows)
    content = round(20 * (0.4 + 0.6 * min(1.0, avg_svc / 600.0)))
    content = max(0, min(20, content))

    inc = indegree_map(rows)
    orphans = [s for s in inc if s != "/" and inc[s] == 0]
    internal = round(15 * (1.0 - min(1.0, len(orphans) * 0.25)))
    internal = max(0, min(15, internal))

    live_pts = round(20 * (1.0 - bad / max(total_live, 1)))
    live_pts = max(0, min(20, live_pts))

    kpi = min(100, basic + structure + content + internal + live_pts)

    return {
        "kpi": kpi,
        "basic": basic,
        "structure": structure,
        "content": content,
        "internal": internal,
        "live_pts": live_pts,
        "avg_svc_words": round(avg_svc, 1),
        "orphans": orphans,
        "meta_ok": meta_ok,
    }


def score_one_page(r: dict) -> tuple[int, list[str], list[str]]:
    good: list[str] = []
    bad: list[str] = []
    s = 92
    slug = r["slug"]
    wc = r["word_count"]

    if r["title_present"] and r["description_present"] and r["canonical_present"]:
        good.append("Title, meta description, and canonical present")
    else:
        s -= 22
        bad.append("Incomplete metadata stack")

    if r["description_has_html"]:
        s -= 14
        bad.append("Meta description contains markup")

    if not r["canonical_ok"]:
        s -= 8
        bad.append("Canonical path does not match page slug")

    if r["h1_count"] == 1:
        good.append("Single H1")
    else:
        s -= 14
        bad.append(f"H1 count is {r['h1_count']}, expected 1")

    if r["title_h1_mismatch"]:
        s -= 5
        bad.append("Title stem and H1 token overlap is weak")

    if slug == "/":
        if wc >= 180:
            good.append("Home copy length acceptable for a hub page")
        else:
            s -= 6
            bad.append("Home body is thin relative to internal link hub role")
    else:
        if wc >= 500:
            good.append("Body depth supports topical coverage")
        elif wc >= 350:
            good.append("Moderate body depth")
            s -= 3
            bad.append("Room to grow toward 600–900 words")
        elif wc >= 220:
            s -= 8
            bad.append("Copy still short for commercial service intent")
        else:
            s -= 14
            bad.append("Thin service copy vs. buyer intent depth")

    if not bad:
        bad.append("Continue expanding FAQs and process specifics")

    return max(45, min(100, s)), good, bad


def product_development_has_wrong_intent() -> bool:
    p = ROOT / "product-development" / "index.html"
    if not p.exists():
        return False
    t = p.read_text(encoding="utf-8", errors="ignore")
    block = re.search(
        r'id="bloc-7"[\s\S]*?<!-- bloc-7 END -->',
        t,
        re.I,
    )
    scope = block.group(0) if block else t
    return bool(
        re.search(
            r"ingredient solutions help|Our ingredient solutions",
            scope,
            re.I,
        )
    )


def build_tasks(cache: dict, breakdown: dict) -> list[tuple[str, str]]:
    rows = cache["rows"]
    tasks: list[tuple[str, str]] = []

    if cache.get("desc_html_slugs"):
        tasks.append(
            (
                "P1",
                f'Fix HTML inside meta descriptions on: {", ".join(cache["desc_html_slugs"])} — use plain text only (also align og/twitter where duplicated).',
            )
        )

    if product_development_has_wrong_intent():
        tasks.append(
            (
                "P1",
                "Rewrite /product-development/ hero intro so it reflects R&D and development workflow, not ingredient-sourcing language that belongs on /ingredient-solutions/. Keep both URLs distinct.",
            )
        )

    if breakdown["orphans"]:
        tasks.append(
            (
                "P2",
                f'Add at least one contextual inbound internal link to orphan URLs: {", ".join(breakdown["orphans"])}.',
            )
        )

    tasks.append(
        (
            "P2",
            f'Raise average service-page depth (currently ~{breakdown["avg_svc_words"]} words; target ~600–900) with sections + FAQs.',
        )
    )

    tasks.append(
        (
            "P3",
            "Post-deploy browser QA: console, network, and form POST path for contact flows (complements HTTP status checks in this report).",
        )
    )
    return tasks


def mono_line(s: str) -> str:
    return f'<span class="mono">{esc(s)}</span>'


def main() -> None:
    cache = load_cache()
    rows = cache["rows"]
    breakdown = compute_breakdown(cache)
    pr_full = cache.get("pagerank_full") or cache.get("pagerank_top", [])
    live = cache["live_checks"]
    bad_ct = int(live.get("bad_count", 0))
    total_live = int(live.get("total", 0))
    ok_ct = total_live - bad_ct

    inc = indegree_map(rows)
    page_scores: dict[str, tuple[int, list[str], list[str]]] = {}
    for r in rows:
        page_scores[r["slug"]] = score_one_page(r)

    home_score = page_scores["/"][0]
    service_rows = [r for r in rows if r["slug"] != "/"]
    service_rows.sort(key=lambda r: r["slug"])

    tasks = build_tasks(cache, breakdown)
    live_source = cache.get("live_checks_source", "unknown")

    # Top PageRank rows with scores (exclude ties clutter — top 7 + home row)
    top_pr_lines = []
    for slug, val in pr_full[:7]:
        ps = page_scores.get(slug, (80, [], []))[0]
        cls = "good" if ps >= 82 else ("warn" if ps >= 72 else "bad")
        top_pr_lines.append(
            f"      <tr><td>{esc(slug)}</td><td>{val:.4f}</td><td class=\"{cls}\">{ps}/100</td></tr>"
        )

    per_page_rows = []
    for r in service_rows:
        score, good, bad = page_scores[r["slug"]]
        cls = "good" if score >= 82 else ("warn" if score >= 72 else "bad")
        gtxt = "<br>".join(f"✅ {esc(x)}" for x in good[:2])
        btxt = "<br>".join(f"❌ {esc(x)}" for x in bad[:3])
        prompt = (
            f"Improve {esc(r['slug'])}: strengthen on-page depth, preserve layout/classes, "
            f"then run python tools/seo_refresh_audit.py && python tools/generate_seo_report.py."
        )
        per_page_rows.append(
            f"      <tr><td>{esc(r['slug'])}</td><td class=\"{cls}\">{score}/100</td>"
            f"<td>{gtxt}<br>{btxt}</td><td><span class=\"mono\">{esc(prompt)}</span></td></tr>"
        )

    task_rows = ""
    for pri, text in tasks:
        task_rows += f"    <li><strong>{esc(pri)}:</strong> {esc(text)}</li>\n"

    dup_note = ""
    if cache.get("duplicate_slugs"):
        dup_note = f' Duplicate slug rows detected in source inventory: {", ".join(cache["duplicate_slugs"])}.'

    recompute_lines = [
        "metadata stack (title / meta description / canonical), HTML-in-meta scan, canonical slug match, H1 count, H1 text vs title overlap heuristic",
        "internal link graph, orphan detection, PageRank-style proxy (85% damping, 40 iterations)",
        f"word counts (visible text; scripts/styles stripped); average service words ≈ {breakdown['avg_svc_words']}",
        "full rebuild of seo/hero-images/index.html via tools/rebuild_hero_index.py",
    ]
    reuse_lines = [
        "tools/seo_refresh_audit.py (orchestrates crawl + cache write)",
        "tools/generate_seo_report.py (this report assembler)",
        "tools/rebuild_hero_index.py (hero inventory)",
        f"seo/audit-cache.json intermediate cache (inputs_hash={esc(cache.get('inputs_hash', ''))})",
    ]
    if live_source.startswith("reused"):
        reuse_lines.append(
            "live_checks HTTP results (reused — inputs_hash matched prior audit; no new HTTP fetch)",
        )
    else:
        recompute_lines.append(
            "live HTTP status for each URL in sitemap.xml (fresh fetch this run)",
        )

    status_p1 = (
        f"{ok_ct}/{total_live} sitemap URLs returned HTTP 200."
        if bad_ct == 0
        else f"{bad_ct} sitemap URL(s) failed live checks; review live_checks in seo/audit-cache.json."
    )

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow, noarchive">
  <title>SEO KPI and Current Tasks - Propeller Co-Pack</title>
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
      max-width: 58rem;
      padding: 2rem 1.25rem 3rem;
      font: 16px/1.6 "Segoe UI", system-ui, sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    h1 {{ margin: 0 0 0.35rem; font-size: 1.75rem; }}
    h2 {{
      margin: 1.8rem 0 0.65rem;
      padding-bottom: 0.25rem;
      border-bottom: 1px solid var(--border);
      color: var(--accent);
      font-size: 1.15rem;
    }}
    p {{ margin: 0 0 1rem; color: var(--muted); }}
    ul {{ margin: 0 0 1rem; padding-left: 1.25rem; color: var(--muted); }}
    li {{ margin-bottom: 0.35rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 0.75rem 0 1rem;
      font-size: 0.94rem;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 0.55rem 0.6rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: var(--surface); }}
    .mono {{
      font-family: ui-monospace, "Cascadia Code", monospace;
      background: var(--surface);
      border-radius: 4px;
      padding: 0.1em 0.35em;
      font-size: 0.9em;
    }}
    .score {{
      border: 1px solid var(--border);
      border-left: 4px solid var(--warn);
      border-radius: 6px;
      padding: 0.8rem 1rem;
      background: var(--surface);
      margin-bottom: 0.75rem;
    }}
    .big {{ font-size: 1.7rem; font-weight: 700; color: var(--text); }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .bad {{ color: var(--bad); }}
  </style>
</head>
<body>
  <h1>SEO Score and Next Steps</h1>
  <p>Last updated: {esc(LAST_UPDATED)}. This refresh used local HTML sources under the repo root plus live HTTP checks for every URL listed in <span class="mono">sitemap.xml</span>. Public marketing pages covered: <strong>{len(rows)}</strong> (home + service slugs). Crawl health assumes internal links resolve to on-disk paths (same folder layout as production).{dup_note}</p>
  <p><a href="./hero-images/">Open service-page hero image library</a> (private utility page).</p>

  <div class="score">
    <div class="big">KPI: {breakdown["kpi"]}/100</div>
    <p><strong>How this score works:</strong> We combine basic SEO setup (25), page structure (20), content depth proxy (20), internal link equity / orphans (15), and live sitemap health (20). Per-page scores are a separate heuristic for prioritization.</p>
  </div>

  <h2>Current tasks (in order)</h2>
  <ul>
{task_rows.rstrip()}
  </ul>

  <h2>Suggested Cursor prompts by task</h2>
  <table>
    <thead>
      <tr>
        <th>Task</th>
        <th>What to ask Cursor</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>P1 — Metadata integrity</td>
        <td><span class="mono">Audit all pages: meta description and og/twitter descriptions must be plain text (no HTML). Align canonical with each page slug. Regenerate seo/index.html via tools after fixes.</span></td>
      </tr>
      <tr>
        <td>P1 — /product-development/ vs /ingredient-solutions/</td>
        <td><span class="mono">Ensure /product-development/ opens with product development workflow copy; keep ingredient sourcing on /ingredient-solutions/. Regenerate SEO report after edits.</span></td>
      </tr>
      <tr>
        <td>P2 — Depth &amp; FAQs</td>
        <td><span class="mono">Expand each service page toward 600–900 words with intent-specific sections and 3–5 FAQs; add 2+ contextual internal links per page without changing layout skeleton.</span></td>
      </tr>
      <tr>
        <td>P3 — Post-deploy QA</td>
        <td><span class="mono">Browser QA on production: console errors, failed assets, contact form network path. Update findings and rerun python tools/seo_refresh_audit.py && python tools/generate_seo_report.py.</span></td>
      </tr>
    </tbody>
  </table>

  <h2>Content suggestions and prompts</h2>
  <p><strong>Content target:</strong> Service pages average about <strong>{breakdown["avg_svc_words"]}</strong> visible words. For stronger topical signals, target <strong>600–900 words</strong> where appropriate: a precise intro, 2–4 sections (150–250 words each), and <strong>3–5 short FAQs</strong>.</p>
  <table>
    <thead>
      <tr>
        <th>Content goal</th>
        <th>What to ask Cursor</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Service depth for ranking</td>
        <td><span class="mono">Expand each service page to 600–900 words while preserving layout and tone. Add practical specifics and at least 2 contextual internal links per page. Then run tools/seo_refresh_audit.py and tools/generate_seo_report.py.</span></td>
      </tr>
      <tr>
        <td>Intent-specific intros</td>
        <td><span class="mono">Rewrite each service page opening so it matches buyer intent for that slug; reduce duplicated generic phrasing across pages. Regenerate the SEO report.</span></td>
      </tr>
      <tr>
        <td>Metadata and on-page alignment</td>
        <td><span class="mono">Align title and meta description with H1 and first body paragraph for every page; verify og/twitter mirrors plain-text descriptions.</span></td>
      </tr>
      <tr>
        <td>Internal anchor quality</td>
        <td><span class="mono">Improve internal anchors so readers know why they are clicking; reinforce hub pages ({mono_line("/")}, {mono_line("/formulation/")}, fulfillment/packaging hubs) without spammy repetition.</span></td>
      </tr>
    </tbody>
  </table>

  <h2>Per-page prompts</h2>
  <table>
    <thead>
      <tr>
        <th>Page</th>
        <th>Score</th>
        <th>Good / Needs work</th>
        <th>What to ask Cursor</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(per_page_rows)}
    </tbody>
  </table>

  <h2>Current status</h2>
  <p><strong>Composite KPI:</strong> {breakdown["kpi"]}/100. <strong>Live crawl:</strong> {esc(status_p1)} <strong>Live check source:</strong> {esc(live_source)}.</p>
  <p><strong>Slug inventory:</strong> Both {mono_line("/ingredient-solutions/")} and {mono_line("/product-development/")} exist as separate folders in this repo; keep intents distinct in copy and internal links.</p>
  <p><strong>Recomputed in this pipeline run:</strong></p>
  <ul>
{"".join(f"    <li>{esc(x)}</li>\n" for x in recompute_lines)}
  </ul>
  <p><strong>Reused / tooling:</strong></p>
  <ul>
{"".join(f"    <li>{esc(x)}</li>\n" for x in reuse_lines)}
  </ul>

  <h2>Details (at bottom)</h2>
  <h3>Score breakdown</h3>
  <table>
    <thead>
      <tr>
        <th>Category</th>
        <th>Weight</th>
        <th>Current score</th>
        <th>Why</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Basic SEO setup</td>
        <td>25</td>
        <td class="good">{breakdown["basic"]}</td>
        <td>{breakdown["meta_ok"]}/{len(rows)} pages pass title + meta description + canonical, no HTML in meta description, canonical matches slug.</td>
      </tr>
      <tr>
        <td>Page structure</td>
        <td>20</td>
        <td class="good">{breakdown["structure"]}</td>
        <td>Exactly one &lt;h1&gt; per audited page.</td>
      </tr>
      <tr>
        <td>Content quality (depth proxy)</td>
        <td>20</td>
        <td class="warn">{breakdown["content"]}</td>
        <td>Derived from average service-page word count (~{breakdown["avg_svc_words"]} words vs. target curve toward 600+).</td>
      </tr>
      <tr>
        <td>Internal links (PageRank proxy + orphans)</td>
        <td>15</td>
        <td class="{'good' if breakdown['internal'] >= 12 else 'warn'}">{breakdown["internal"]}</td>
        <td>{'No orphan slugs detected.' if not breakdown['orphans'] else 'Orphan slugs (no inbound internal links from other pages): ' + esc(', '.join(breakdown['orphans']))}</td>
      </tr>
      <tr>
        <td>Live site health (sitemap URLs)</td>
        <td>20</td>
        <td class="{'good' if breakdown['live_pts'] >= 18 else 'bad'}">{breakdown["live_pts"]}</td>
        <td>HTTP status checks for all sitemap.xml locs ({bad_ct} failures).</td>
      </tr>
    </tbody>
  </table>

  <h3>PageRank proxy snapshot</h3>
  <p>Random-walk PageRank on internal links between audited marketing slugs (damping 0.85). Home page score for reference: <strong class="good">{home_score}/100</strong>.</p>
  <table>
    <thead>
      <tr>
        <th>Top internal URLs by PageRank proxy</th>
        <th>PageRank proxy</th>
        <th>Page score</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(top_pr_lines)}
    </tbody>
  </table>

  <h3>Full regeneration prompt</h3>
  <p>Use this prompt when you want Cursor to fully rebuild this SEO report from current site state:</p>
  <p><span class="mono">Regenerate this entire seo/index.html page from scratch using the current project files and live site checks. Recompute and rewrite: KPI score, current tasks, suggested prompts by task, content suggestions, per-page prompts/scores for all public pages, current status, score breakdown table, and PageRank proxy snapshot. As part of the same workflow, rebuild seo/hero-images/index.html from current service page hero image sources so names, paths, image URLs, and alt text stay synchronized. Validate internal links, metadata consistency (title/meta/canonical), single-H1 structure, and crawl health assumptions. Ensure page/slug naming is consistent (including both /ingredient-solutions/ and /product-development/ where they exist), remove stale duplicates, and update the Last updated date. Keep the same overall HTML structure and styling conventions used in this file. You may create and reuse local helper scripts (for crawling, scoring, link graph, report assembly, and hero index generation) plus cached intermediate outputs so incremental refreshes run faster; only re-run expensive checks (especially live checks) when source files or dependent inputs changed, and document which sections were recomputed versus reused.</span></p>
</body>
</html>
"""

    OUTPUT.write_text(body, encoding="utf-8")
    print(f"Wrote {OUTPUT} (KPI {breakdown['kpi']}, pages {len(rows)})")


if __name__ == "__main__":
    main()
