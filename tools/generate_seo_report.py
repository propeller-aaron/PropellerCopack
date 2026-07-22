"""Build SEO status dashboard HTML from audit-cache.json."""
from __future__ import annotations

import html
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from status_design import STATUS_JS
from status_metrics import ISSUE_LABELS, build_metric_catalog, metric_trigger, safe_json_for_script

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
                    f"On {slug}, remove HTML tags from the meta description. "
                    "Keep plain text only and match the on-page copy tone."
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
                    f"On {slug}, add a unique title, meta description, and canonical URL. "
                    "Follow patterns in tools/update_inner_seo.py and existing inner pages."
                ),
            )
        )

    h1_groups = pages_by_h1_count(audit)
    if three := sorted(h1_groups.get(3, [])):
        groups.append(
            TaskGroup(
                priority="P1",
                title="Fix heading hierarchy on service pages (3 H1s)",
                summary=f"{len(three)} pages use three H1 tags.",
                pages=tuple(three),
                cursor_prompt=(
                    "Fix heading hierarchy on these Propeller Co-Pack service pages so each page has exactly one H1:\n"
                    f"{chr(10).join(three)}\n\n"
                    "Keep the bloc-7 service title as the sole H1; demote shared banner and contact headings to h2."
                ),
            )
        )

    if two := sorted(h1_groups.get(2, [])):
        page_lines = ["/ (homepage)" if slug == "/" else slug for slug in two]
        groups.append(
            TaskGroup(
                priority="P1",
                title="Fix heading hierarchy (2 H1s)",
                summary=f"{len(two)} pages use two H1 tags.",
                pages=tuple(two),
                cursor_prompt=(
                    "Fix heading hierarchy so each page has exactly one H1:\n"
                    f"{chr(10).join(page_lines)}"
                ),
            )
        )

    thin = sorted(r["slug"] for r in audit["rows"] if r["word_count"] < 250 and r["slug"] != "/")
    if thin:
        groups.append(
            TaskGroup(
                priority="P2",
                title="Expand thin service page content",
                summary=f"{len(thin)} service pages are under ~250 words; target 600-900 words.",
                pages=tuple(thin),
                cursor_prompt=(
                    "Expand on-page copy on these Propeller Co-Pack service pages to roughly 600-900 words each:\n"
                    f"{chr(10).join(thin)}"
                ),
            )
        )

    moderate = sorted(
        r["slug"] for r in audit["rows"] if 250 <= r["word_count"] < 400 and r["slug"] != "/"
    )
    if moderate:
        groups.append(
            TaskGroup(
                priority="P2",
                title="Deepen moderate-length service pages",
                summary=f"{len(moderate)} pages are ~250-400 words; expand toward 600-900 words.",
                pages=tuple(moderate),
                cursor_prompt=(
                    "Expand these service pages from moderate depth toward 600-900 words:\n"
                    f"{chr(10).join(moderate)}"
                ),
            )
        )

    if audit["live_checks"].get("bad_count", 0):
        bad_urls = [
            item["url"] for item in audit["live_checks"].get("results", []) if item.get("status") != 200
        ]
        groups.append(
            TaskGroup(
                priority="P1",
                title="Fix live sitemap URL failures",
                summary=f"{len(bad_urls)} sitemap URLs are not returning HTTP 200.",
                pages=tuple(bad_urls),
                cursor_prompt=(
                    "These sitemap URLs are failing live HTTP checks:\n"
                    f"{chr(10).join(bad_urls)}"
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
                cursor_prompt="Re-run python tools/refresh_seo_all.py after future content or deploy changes.",
            )
        )

    return groups


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

    return max(0, min(100, score)), good, bad


def score_site(audit: dict) -> tuple[int, dict[str, int], dict[str, int], float]:
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
    return [(group.priority, group.summary) for group in build_task_groups(audit, page_scores)]


def page_file_from_slug(slug: str) -> str:
    if slug == "/":
        return "index.html"
    return f"{slug.strip('/')}/index.html"


def link_graph_stats(rows: list[dict]) -> tuple[dict[str, int], dict[str, int], int]:
    slugs = {row["slug"] for row in rows}
    inbound: dict[str, int] = defaultdict(int)
    outbound: dict[str, int] = defaultdict(int)
    edges = 0
    for row in rows:
        seen: set[str] = set()
        for link in row.get("internal_links", []):
            if link not in slugs or link in seen:
                continue
            seen.add(link)
            outbound[row["slug"]] += 1
            inbound[link] += 1
            edges += 1
    return dict(inbound), dict(outbound), edges


def toolbar_score(pr_value: float, max_pr: float) -> float:
    if max_pr <= 0:
        return 0.0
    return round(max(0.1, min(10.0, (pr_value / max_pr) * 10)), 1)


def page_suggestions(row: dict, findings: list[dict], toolbar: float | None) -> list[str]:
    suggestions: list[str] = []
    codes = {finding["code"] for finding in findings}
    if "pagerank-orphan" in codes:
        suggestions.append(
            f"Low simulated PageRank ({toolbar or 0}/10). Link to this page from related service content and the homepage."
        )
    if "thin-content" in codes or "moderate-content" in codes:
        suggestions.append(
            f"Expand on-page copy (~{row['word_count']} words now) toward 600-900 words while preserving layout and SEO head tags."
        )
    if "bad-h1" in codes:
        suggestions.append("Demote extra H1 headings to h2 so the page has exactly one H1.")
    if not suggestions:
        suggestions.append(
            "Metadata looks healthy. Review annually for keyword freshness and add one new contextual internal link if possible."
        )
    return suggestions


def build_report_model(audit: dict) -> dict:
    rows = audit["rows"]
    kpi, breakdown, page_scores, _avg_page = score_site(audit)
    inbound, outbound, edges = link_graph_stats(rows)
    slugs = [row["slug"] for row in rows]

    pr_map = {slug: value for slug, value in audit.get("pagerank_top", [])}
    for row in rows:
        pr_map.setdefault(row["slug"], 0.0)
    max_pr = max(pr_map.values()) if pr_map else 1.0
    home_pr = pr_map.get("/", max_pr)

    orphan_slugs = {
        slug
        for slug in slugs
        if slug != "/" and inbound.get(slug, 0) <= 1 and toolbar_score(pr_map.get(slug, 0.0), max_pr) < 3
    }

    findings: list[dict] = []
    page_findings: dict[str, list[dict]] = defaultdict(list)

    def add_finding(slug: str, code: str, severity: str, detail: str) -> None:
        finding = {
            "slug": slug,
            "file": page_file_from_slug(slug),
            "code": code,
            "severity": severity,
            "detail": detail,
        }
        findings.append(finding)
        page_findings[slug].append(finding)

    for slug in audit.get("missing_meta_slugs", []):
        add_finding(slug, "missing-meta", "high", "Missing title, meta description, or canonical")
    for slug in audit.get("bad_h1_slugs", []):
        add_finding(slug, "bad-h1", "high", "Page does not have exactly one H1")
    for slug in audit.get("desc_html_slugs", []):
        add_finding(slug, "desc-html", "high", "Meta description contains HTML markup")

    for row in rows:
        slug = row["slug"]
        if row["word_count"] < 250 and slug != "/":
            add_finding(slug, "thin-content", "medium", f"Thin content (~{row['word_count']} words)")
        elif 250 <= row["word_count"] < 400 and slug != "/":
            add_finding(slug, "moderate-content", "low", f"Moderate depth (~{row['word_count']} words)")
        if len(row["title_text"]) > 60:
            add_finding(slug, "title-too-long", "low", f"Title is {len(row['title_text'])} characters")
        if slug in orphan_slugs:
            add_finding(
                slug,
                "pagerank-orphan",
                "medium",
                "Few inbound internal links; page may be hard to discover",
            )

    for item in audit["live_checks"].get("results", []):
        if item.get("status") != 200:
            add_finding(
                item["url"],
                "live-url-fail",
                "high",
                f"HTTP {item.get('status') or 'ERR'}: {item.get('error', 'request failed')}",
            )

    page_reports = []
    for row in rows:
        slug = row["slug"]
        row_findings = page_findings.get(slug, [])
        toolbar = toolbar_score(pr_map.get(slug, 0.0), max_pr)
        page_reports.append(
            {
                "url": slug,
                "title": row["title_text"],
                "file": page_file_from_slug(slug),
                "titleLength": len(row["title_text"]),
                "descriptionLength": len(row["description_text"]) if row["description_present"] else 0,
                "featuredImage": False,
                "findings": row_findings,
                "suggestions": page_suggestions(row, row_findings, toolbar),
                "pageRank": {
                    "toolbar": toolbar,
                    "inbound": inbound.get(slug, 0),
                    "outbound": outbound.get(slug, 0),
                },
                "score": page_scores.get(slug, 0),
            }
        )

    linked_pages = sum(1 for slug in slugs if inbound.get(slug, 0) > 0)
    coverage = round((linked_pages / max(len(slugs), 1)) * 100, 1)
    site_toolbar = toolbar_score(sum(pr_map.values()) / max(len(pr_map), 1), max_pr)
    home_toolbar = toolbar_score(home_pr, max_pr)

    rank_entries = sorted(
        (
            {
                "url": slug,
                "toolbar": toolbar_score(pr_map.get(slug, 0.0), max_pr),
                "inbound": inbound.get(slug, 0),
                "outbound": outbound.get(slug, 0),
            }
            for slug in slugs
        ),
        key=lambda item: (item["toolbar"], item["inbound"]),
        reverse=True,
    )

    robots_ok = (ROOT / "robots.txt").is_file() and "Sitemap:" in (ROOT / "robots.txt").read_text(encoding="utf-8")
    sitemap_ok = (ROOT / "sitemap.xml").is_file()
    live = audit["live_checks"]
    live_ok = live.get("bad_count", 0) == 0

    site_checks = [
        {
            "id": "robots",
            "label": "robots.txt present",
            "ok": robots_ok,
            "detail": "Found robots.txt with sitemap reference" if robots_ok else "Missing or incomplete robots.txt",
        },
        {
            "id": "sitemap",
            "label": "XML sitemap present",
            "ok": sitemap_ok,
            "detail": "sitemap.xml found at repo root" if sitemap_ok else "sitemap.xml missing",
        },
        {
            "id": "live-http",
            "label": "Live sitemap HTTP checks",
            "ok": live_ok,
            "detail": f"{live.get('total', 0) - live.get('bad_count', 0)}/{live.get('total', 0)} URLs return HTTP 200",
        },
        {
            "id": "link-coverage",
            "label": "Internal link coverage",
            "ok": coverage >= 70,
            "detail": f"{coverage}% of pages receive at least one internal link",
        },
        {
            "id": "metadata",
            "label": "Metadata completeness",
            "ok": not audit.get("missing_meta_slugs"),
            "detail": "All pages have title, description, and canonical"
            if not audit.get("missing_meta_slugs")
            else f"{len(audit.get('missing_meta_slugs', []))} pages missing metadata",
        },
    ]

    summary = {
        "missingMeta": len(audit.get("missing_meta_slugs", [])),
        "badH1": len(audit.get("bad_h1_slugs", [])),
        "thinContent": sum(1 for r in rows if r["word_count"] < 250 and r["slug"] != "/"),
        "titleTooLong": sum(1 for r in rows if len(r["title_text"]) > 60),
        "liveFailures": live.get("bad_count", 0),
        "orphanPages": len(orphan_slugs),
    }

    prompts = [
        {"title": group.title, "prompt": group.cursor_prompt}
        for group in build_task_groups(audit, page_scores)
    ]

    return {
        "generatedAt": audit["generated_on"],
        "score": kpi,
        "breakdown": breakdown,
        "findings": findings,
        "pageReports": sorted(page_reports, key=lambda item: item["url"]),
        "siteChecks": site_checks,
        "summary": summary,
        "liveChecks": live,
        "pageRank": {
            "siteToolbar": site_toolbar,
            "homeToolbar": home_toolbar,
            "coverage": coverage,
            "pagesAnalyzed": len(slugs),
            "edges": edges,
            "topPages": rank_entries[:15],
        },
        "prompts": prompts,
        "fileCount": len(rows),
    }


def build_dashboard_metrics(report: dict) -> dict:
    severity_counts = Counter(finding["severity"] for finding in report["findings"])
    code_counts = Counter(finding["code"] for finding in report["findings"])
    current_score = report["score"]
    potential_score = 100
    improvement = max(0, potential_score - current_score)
    pages_with_issues = sum(1 for page in report["pageReports"] if page["findings"])
    clean_pages = len(report["pageReports"]) - pages_with_issues
    checks_passing = sum(1 for check in report["siteChecks"] if check["ok"])
    breakdown = report["breakdown"]

    score_breakdown = [
        {"metricId": "score-basic-seo", "label": "Basic SEO setup", "current": breakdown["basic"], "max": 25},
        {"metricId": "score-structure", "label": "Page structure", "current": breakdown["structure"], "max": 20},
        {"metricId": "score-content", "label": "Content quality", "current": breakdown["content"], "max": 20},
        {"metricId": "score-links", "label": "Internal links", "current": breakdown["links"], "max": 15},
        {"metricId": "score-health", "label": "Live site health", "current": breakdown["health"], "max": 20},
    ]

    return {
        "currentScore": current_score,
        "potentialScore": potential_score,
        "improvement": improvement,
        "severityCounts": {
            "high": severity_counts.get("high", 0),
            "medium": severity_counts.get("medium", 0),
            "low": severity_counts.get("low", 0),
        },
        "severityTotal": max(1, len(report["findings"])),
        "topIssues": code_counts.most_common(6),
        "pagesWithIssues": pages_with_issues,
        "cleanPages": clean_pages,
        "checksPassing": checks_passing,
        "totalChecks": len(report["siteChecks"]),
        "scoreBreakdown": score_breakdown,
    }


def format_display_date(value: str) -> str:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%B %d, %Y")
        except ValueError:
            continue
    return value


def build_odometer_html(value: int, *, variant: str = "score", prefix: str = "") -> str:
    digits = list(str(max(0, round(value))))
    wheels = []
    for index, digit in enumerate(digits):
        strip = "".join(f"<span>{number}</span>" for number in range(10))
        wheels.append(
            f'<span class="status-odometer-wheel" data-digit="{html.escape(digit)}" data-index="{index}">'
            f'<span class="status-odometer-strip">{strip}</span></span>'
        )
    prefix_html = f'<span class="status-odometer-prefix">{html.escape(prefix)}</span>' if prefix else ""
    return (
        f'<div class="status-odometer status-odometer-{variant}" data-target="{value}" aria-hidden="true">'
        f"{prefix_html}{''.join(wheels)}</div>"
    )


def build_gauge_svg(score: int, potential: int) -> str:
    radius = 46
    circumference = 2 * math.pi * radius
    score_offset = circumference * (1 - score / 100)
    potential_offset = circumference * (1 - potential / 100)
    return f"""<svg class="status-gauge-svg" viewBox="0 0 120 120" role="img" aria-label="SEO score {score} out of {potential}">
    <circle class="status-gauge-ring status-gauge-ring-bg" cx="60" cy="60" r="{radius}" />
    <circle class="status-gauge-ring status-gauge-ring-potential" cx="60" cy="60" r="{radius}" stroke-dasharray="{circumference}" stroke-dashoffset="{potential_offset}" />
    <circle class="status-gauge-ring status-gauge-ring-current" cx="60" cy="60" r="{radius}" stroke-dasharray="{circumference}" stroke-dashoffset="{score_offset}" />
    <text x="60" y="56" class="status-gauge-value">{score}</text>
    <text x="60" y="74" class="status-gauge-sub">of {potential}</text>
  </svg>"""


def build_donut_style(severity_counts: dict[str, int], total: int) -> str:
    segments = [
        (severity_counts.get("high", 0), "#c0392b"),
        (severity_counts.get("medium", 0), "#d68910"),
        (severity_counts.get("low", 0), "#2980b9"),
    ]
    segments = [(count, color) for count, color in segments if count > 0]
    if not segments:
        return "conic-gradient(#e5e5e5 0 100%)"
    cursor = 0.0
    stops: list[str] = []
    for count, color in segments:
        pct = (count / total) * 100
        start = cursor
        cursor += pct
        stops.append(f"{color} {start}% {cursor}%")
    return f"conic-gradient({', '.join(stops)})"


def build_status_dashboard_html(report: dict, metrics: dict) -> str:
    max_issue_count = metrics["topIssues"][0][1] if metrics["topIssues"] else 1
    donut_style = build_donut_style(metrics["severityCounts"], metrics["severityTotal"])
    health_total = metrics["pagesWithIssues"] + metrics["cleanPages"] or 1
    clean_pct = round((metrics["cleanPages"] / health_total) * 100)

    kpi_cards = []
    for kpi in [
        ("kpi-total-findings", "Total findings", len(report["findings"]), f"{metrics['severityCounts']['high']} high priority", min(100, len(report["findings"]) / 1.5), "warn"),
        ("kpi-pages-needing-work", "Pages needing work", metrics["pagesWithIssues"], f"{metrics['cleanPages']} pages clean", round((metrics["pagesWithIssues"] / max(len(report["pageReports"]), 1)) * 100), "warn"),
        ("kpi-link-coverage", "Link coverage", f"{report['pageRank']['coverage']}%", f"{report['pageRank']['edges']} internal edges", report["pageRank"]["coverage"], "good"),
        ("kpi-site-pagerank", "Site PageRank", f"{report['pageRank']['siteToolbar']}/10", "Simulated authority", report["pageRank"]["siteToolbar"] * 10, "good"),
        ("kpi-site-checks", "Site checks passing", f"{metrics['checksPassing']}/{metrics['totalChecks']}", "Infrastructure readiness", round((metrics["checksPassing"] / metrics["totalChecks"]) * 100), "good"),
        ("kpi-improvement", "Improvement available", f"+{metrics['improvement']}", "Points to optimal score", metrics["improvement"], "gain"),
    ]:
        kpi_id, label, value, detail, bar, tone = kpi
        kpi_cards.append(
            metric_trigger(
                kpi_id,
                f"""<span class="status-kpi status-kpi-{tone}">
        <span class="status-kpi-label">{html.escape(label)}</span>
        <span class="status-kpi-value">{html.escape(str(value))}</span>
        <span class="status-kpi-detail">{html.escape(detail)}</span>
        <span class="status-kpi-bar" aria-hidden="true"><span style="width:{bar}%"></span></span>
      </span>""",
                "status-kpi-trigger",
            )
        )

    severity_legend = []
    for key, label, color in [
        ("high", "High", "#c0392b"),
        ("medium", "Medium", "#d68910"),
        ("low", "Low", "#2980b9"),
    ]:
        count = metrics["severityCounts"][key]
        severity_legend.append(
            f"<li>{metric_trigger(f'severity-{key}', f'<span class=\"status-legend-swatch\" style=\"background:{color}\"></span>{html.escape(label)} <strong>{count}</strong>', 'status-legend-trigger')}</li>"
        )

    issue_bars = []
    for code, count in metrics["topIssues"]:
        width = round((count / max_issue_count) * 100)
        label = ISSUE_LABELS.get(code, code)
        issue_bars.append(
            metric_trigger(
                f"issue-{code}",
                f"""<span class="status-bar-row"><span class="status-bar-label"><span>{html.escape(label)}</span><strong>{count}</strong></span><span class="status-bar-track"><span style="width:{width}%"></span></span></span>""",
                "status-bar-trigger",
            )
        )

    score_bars = []
    for item in metrics["scoreBreakdown"]:
        width = round((item["current"] / item["max"]) * 100)
        score_bars.append(
            metric_trigger(
                item["metricId"],
                f"""<span class="status-bar-row"><span class="status-bar-label"><span>{html.escape(item['label'])}</span><strong>{item['current']}/{item['max']}</strong></span><span class="status-bar-track status-bar-track-score"><span style="width:{width}%"></span></span></span>""",
                "status-bar-trigger",
            )
        )

    return f"""<section class="status-dashboard" id="status-dashboard" aria-label="SEO dashboard">
    <div class="status-dashboard-hero">
      {metric_trigger("seo-score", f'''<span class="status-odometer-card">
        <span class="status-odometer-kicker">Current SEO score</span>
        {build_odometer_html(metrics["currentScore"], variant="score")}
        <span class="status-odometer-caption">out of 100 · click for details</span>
      </span>''', "status-hero-trigger")}
      {metric_trigger("improvement-headroom", f'''<span class="status-odometer-card status-odometer-card-gain">
        <span class="status-odometer-kicker">Improvement headroom</span>
        {build_odometer_html(metrics["improvement"], variant="gain", prefix="+")}
        <span class="status-odometer-caption">points available if issues are fixed</span>
      </span>''', "status-hero-trigger")}
      {metric_trigger("score-vs-optimal", f'''<span class="status-gauge-card">
        <span class="status-odometer-kicker">Score vs optimal</span>
        {build_gauge_svg(metrics["currentScore"], metrics["potentialScore"])}
        <span class="status-odometer-caption">{metrics["improvement"]} points to reach {metrics["potentialScore"]}</span>
      </span>''', "status-hero-trigger")}
    </div>
    <div class="status-kpi-grid" aria-label="Key performance indicators">{''.join(kpi_cards)}</div>
    <div class="status-charts-grid">
      <article class="status-chart-panel">
        <h3>Findings by severity</h3>
        <div class="status-donut-wrap">
          {metric_trigger("findings-total", f'<span class="status-donut" style="background:{donut_style}"></span><span class="status-donut-center"><strong>{len(report["findings"])}</strong><span>findings</span></span>', "status-donut-trigger")}
        </div>
        <ul class="status-legend">{''.join(severity_legend)}</ul>
      </article>
      <article class="status-chart-panel">
        <h3>Top issue categories</h3>
        <div class="status-bar-chart">{''.join(issue_bars) or '<p class="status-muted">No issues detected.</p>'}</div>
      </article>
      <article class="status-chart-panel">
        <h3>Score breakdown</h3>
        <div class="status-bar-chart">{''.join(score_bars)}</div>
      </article>
      <article class="status-chart-panel">
        <h3>Page health</h3>
        <div class="status-health-chart">
          <div class="status-health-bar" aria-hidden="true">
            <span class="status-health-clean" style="width:{clean_pct}%"></span>
            <span class="status-health-issues" style="width:{100 - clean_pct}%"></span>
          </div>
          <ul class="status-health-legend">
            <li>{metric_trigger("page-health-clean", f'<span class="status-legend-swatch status-health-clean-swatch"></span>Clean pages <strong>{metrics["cleanPages"]}</strong>', "status-legend-trigger")}</li>
            <li>{metric_trigger("page-health-issues", f'<span class="status-legend-swatch status-health-issues-swatch"></span>Needs work <strong>{metrics["pagesWithIssues"]}</strong>', "status-legend-trigger")}</li>
          </ul>
        </div>
      </article>
    </div>
  </section>"""


def build_status_checks(site_checks: list[dict]) -> str:
    return "".join(
        f'<li class="status-check{" is-ok" if check["ok"] else " is-fail"}">'
        f'{metric_trigger(f"site-check-{check["id"]}", f"<span class=\"status-check-label\">{html.escape(check['label'])}</span><span class=\"status-check-detail\">{html.escape(check['detail'])}</span>", "status-check-trigger")}'
        f"</li>"
        for check in site_checks
    )


def build_status_summary(summary: dict) -> str:
    rows = [
        ("summary-missing-meta", "Missing metadata", summary["missingMeta"]),
        ("summary-bad-h1", "Bad H1 count", summary["badH1"]),
        ("summary-thin-content", "Thin content", summary["thinContent"]),
        ("summary-title-too-long", "Titles too long", summary["titleTooLong"]),
        ("summary-live-failures", "Live URL failures", summary["liveFailures"]),
        ("summary-orphan-pages", "Orphan pages", summary["orphanPages"]),
    ]
    return "".join(
        metric_trigger(
            metric_id,
            f'<span class="status-summary-row"><span class="status-summary-label">{html.escape(label)}</span><span class="status-summary-value">{value}</span></span>',
            "status-summary-trigger",
        )
        for metric_id, label, value in rows
    )


def build_status_rank_list(pages: list[dict]) -> str:
    items = []
    for page in pages:
        rank_id = page["url"].replace("/", "_").strip("_") or "home"
        inner = (
            f'<span class="status-rank-url">{html.escape(page["url"])}</span>'
            f'<span>{page["toolbar"]}/10 · {page["inbound"]} inbound</span>'
        )
        items.append(
            f"<li>{metric_trigger(f'rank-{rank_id}', inner, 'status-rank-trigger')}</li>"
        )
    return "".join(items)


def build_status_prompts(prompts: list[dict]) -> str:
    return "".join(
        f"<details><summary>{html.escape(item['title'])}</summary><p>{html.escape(item['prompt'])}</p></details>"
        for item in prompts
    )


def build_status_table_rows(page_reports: list[dict]) -> str:
    rows = []
    for page in page_reports:
        search_tokens = " ".join(
            [
                page["url"],
                page["title"],
                page["file"],
                *(finding["code"] for finding in page["findings"]),
                *(finding["detail"] for finding in page["findings"]),
            ]
        ).strip()
        findings_html = (
            '<ul class="status-findings">'
            + "".join(
                f'<li class="severity-{html.escape(finding["severity"])}">{html.escape(finding["code"])}</li>'
                for finding in page["findings"]
            )
            + "</ul>"
            if page["findings"]
            else '<span class="status-ok-label">None</span>'
        )
        rank = page["pageRank"]
        rank_html = (
            f'<span class="status-rank-badge">{rank["toolbar"]}/10</span>'
            f'<span class="status-rank-detail">{rank["inbound"]} in · {rank["outbound"]} out</span>'
        )
        suggestions_html = (
            '<ul class="status-suggestions">'
            + "".join(f"<li>{html.escape(item)}</li>" for item in page["suggestions"])
            + "</ul>"
        )
        description_label = f"{page['descriptionLength']} chars" if page["descriptionLength"] else "missing"
        rows.append(
            f'<tr data-search="{html.escape(search_tokens)}"><td class="status-page-cell">'
            f'<a href="{html.escape(page["url"])}"><strong>{html.escape(page["title"] or page["url"])}</strong></a>'
            f'<code>{html.escape(page["url"])}</code><span class="status-source">{html.escape(page["file"])}</span></td>'
            f"<td><ul class=\"status-meta-list\"><li>Title: {page['titleLength']} chars</li>"
            f"<li>Description: {html.escape(description_label)}</li>"
            f"<li>Score: {page['score']}/100</li></ul></td>"
            f"<td>{rank_html}</td><td>{findings_html}</td><td>{suggestions_html}</td></tr>"
        )
    return "".join(rows)


def build_status_modal_html() -> str:
    return """<div class="status-modal" id="status-modal" hidden>
  <div class="status-modal-backdrop" data-close-modal tabindex="-1"></div>
  <div class="status-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="status-modal-title">
    <button type="button" class="status-modal-close" data-close-modal aria-label="Close">&times;</button>
    <p class="status-modal-kicker">Metric detail</p>
    <h2 id="status-modal-title"></h2>
    <p class="status-modal-value"></p>
    <p class="status-modal-desc"></p>
    <h3 class="status-modal-section-title">Culprits</h3>
    <ul class="status-modal-culprits" id="status-modal-culprits"></ul>
    <div class="status-modal-prompt">
      <h3 class="status-modal-section-title">Suggested Cursor prompt</h3>
      <pre id="status-modal-prompt"></pre>
      <button type="button" class="status-copy-prompt" id="status-copy-prompt">Copy prompt</button>
      <span class="status-copy-feedback" id="status-copy-feedback" hidden>Copied</span>
    </div>
  </div>
</div>"""


def render_report(audit: dict) -> str:
    report = build_report_model(audit)
    metrics = build_dashboard_metrics(report)
    metric_catalog = build_metric_catalog(report, metrics)
    generated = format_display_date(report["generatedAt"])

    return f"""<div class="status-shell">
  <header class="status-header">
    <div>
      <p class="status-kicker">Internal tooling · not indexed</p>
      <p class="status-meta">Generated {html.escape(generated)} · {len(report["pageReports"])} pages · {len(report["findings"])} findings · click any metric for culprits and fix prompts</p>
    </div>
  </header>
  {build_status_dashboard_html(report, metrics)}
  <section class="status-grid" aria-label="Site metrics">
    {metric_trigger("metric-site-pagerank", f'<span class="status-card"><span class="status-card-heading">Site PageRank</span><span class="status-metric">{report["pageRank"]["siteToolbar"]}/10</span><span class="status-detail">Simulated sitewide authority</span></span>', "status-card-trigger")}
    {metric_trigger("metric-home-pagerank", f'<span class="status-card"><span class="status-card-heading">Home PageRank</span><span class="status-metric">{report["pageRank"]["homeToolbar"]}/10</span><span class="status-detail">Homepage toolbar score</span></span>', "status-card-trigger")}
    {metric_trigger("metric-link-coverage", f'<span class="status-card"><span class="status-card-heading">Link coverage</span><span class="status-metric">{report["pageRank"]["coverage"]}%</span><span class="status-detail">{report["pageRank"]["pagesAnalyzed"]} pages · {report["pageRank"]["edges"]} edges</span></span>', "status-card-trigger")}
    {metric_trigger("metric-content-files", f'<span class="status-card"><span class="status-card-heading">Content pages</span><span class="status-metric">{report["fileCount"]}</span><span class="status-detail">{report["summary"]["thinContent"]} thin-content pages</span></span>', "status-card-trigger")}
  </section>
  <section class="status-panel"><h2>Site checks</h2><ul class="status-checks">{build_status_checks(report["siteChecks"])}</ul></section>
  <section class="status-panel"><h2>Summary</h2><div class="status-summary">{build_status_summary(report["summary"])}</div></section>
  <section class="status-panel"><h2>Top PageRank pages</h2><ul class="status-rank-list">{build_status_rank_list(report["pageRank"]["topPages"])}</ul></section>
  <section class="status-panel"><h2>Global improvement prompts</h2><div class="status-prompts">{build_status_prompts(report["prompts"])}</div></section>
  <section class="status-panel status-pages">
    <div class="status-pages-head">
      <h2>Page-by-page suggestions</h2>
      <label class="status-filter"><span class="utility-sr-only">Filter pages</span><input type="search" id="status-filter" placeholder="Filter by URL, title, or issue…" /></label>
    </div>
    <div class="status-table-wrap">
      <table class="status-table" id="status-table">
        <thead><tr><th scope="col">Page</th><th scope="col">Meta</th><th scope="col">Rank</th><th scope="col">Findings</th><th scope="col">Suggestions</th></tr></thead>
        <tbody>{build_status_table_rows(report["pageReports"])}</tbody>
      </table>
    </div>
  </section>
  {build_status_modal_html()}
  <script type="application/json" id="status-metrics-json">{safe_json_for_script(metric_catalog)}</script>
  <script>{STATUS_JS}</script>
</div>"""


def load_audit() -> dict:
    return json.loads(CACHE.read_text(encoding="utf-8"))


def main() -> None:
    audit = load_audit()
    print(render_report(audit))


if __name__ == "__main__":
    main()
