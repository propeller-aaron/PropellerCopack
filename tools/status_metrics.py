"""Metric catalog and prompts for the SEO status dashboard."""
from __future__ import annotations

import json
from typing import Any

ISSUE_LABELS = {
    "missing-meta": "Missing metadata",
    "bad-h1": "Bad H1 count",
    "desc-html": "HTML in descriptions",
    "thin-content": "Thin content",
    "moderate-content": "Moderate content depth",
    "title-too-long": "Long titles",
    "pagerank-orphan": "Orphan pages",
    "live-url-fail": "Live URL failures",
}

PROMPTS_BY_CODE = {
    "missing-meta": (
        "Add title, meta description, and canonical URL to every page missing metadata. "
        "Follow patterns in tools/update_inner_seo.py and neighboring service pages."
    ),
    "bad-h1": (
        "Fix heading hierarchy so each page has exactly one H1. On v3 service pages, keep "
        "the bloc-7 service title as the sole H1 and demote shared banner/contact headings to h2."
    ),
    "desc-html": (
        "Remove HTML tags from meta descriptions. Keep plain text only in description meta tags."
    ),
    "thin-content": (
        "Expand thin service pages to roughly 600-900 words. Preserve SEO head tags, contact "
        "form, hero images, and v3 bloc layout."
    ),
    "moderate-content": (
        "Deepen moderate-length service pages toward 600-900 words with useful, non-duplicative sections."
    ),
    "title-too-long": (
        "Shorten SEO titles to ≤60 characters while keeping primary service keywords and brand context."
    ),
    "pagerank-orphan": (
        "Add contextual internal links from high-authority pages (homepage, related services) to "
        "orphan URLs listed on /status/."
    ),
    "live-url-fail": (
        "Fix sitemap URLs that are not returning HTTP 200. Update routing/deploy or remove stale URLs from sitemap.xml."
    ),
}


def safe_json_for_script(value: Any) -> str:
    return json.dumps(value).replace("<", "\\u003c")


def metric_trigger(metric_id: str, inner_html: str, class_name: str = "") -> str:
    classes = " ".join(part for part in ("status-metric-trigger", class_name) if part)
    safe_id = metric_id.replace('"', "&quot;")
    return f'<button type="button" class="{classes}" data-metric-id="{safe_id}">{inner_html}</button>'


def empty_culprit(message: str) -> list[dict[str, str]]:
    return [{"title": "No issues", "url": "", "file": "", "detail": message}]


def culprit_from_finding(finding: dict, page: dict | None = None) -> dict:
    return {
        "file": finding.get("file") or finding.get("slug", ""),
        "url": page.get("url", finding.get("slug", "")) if page else finding.get("slug", ""),
        "title": (page or {}).get("title") or finding.get("slug", ""),
        "detail": finding.get("detail", ""),
        "severity": finding.get("severity", ""),
    }


def culprit_from_page(page: dict, detail: str = "") -> dict:
    return {
        "file": page.get("file", ""),
        "url": page.get("url", ""),
        "title": page.get("title") or page.get("url", ""),
        "detail": detail,
    }


def prompt_for_code(code: str, files: list[str]) -> str:
    base = PROMPTS_BY_CODE.get(code, f'Fix SEO issue "{code}" on affected pages.')
    if len(files) <= 8:
        return f"{base}\n\nAffected pages:\n" + "\n".join(f"- {item}" for item in files)
    return f"{base}\n\n{len(files)} affected pages — filter /status/ by \"{code}\" for the full list."


def prompt_for_findings(findings: list[dict]) -> str:
    if not findings:
        return (
            "No open issues for this metric. Re-run python tools/refresh_seo_all.py after content changes."
        )
    codes = sorted({finding["code"] for finding in findings})
    if len(codes) == 1:
        return prompt_for_code(codes[0], [finding.get("slug") or finding.get("file", "") for finding in findings])
    return (
        f"Fix all remaining SEO findings ({len(findings)} total) on /status/. Prioritize high-severity items first.\n\n"
        f"Issue types: {', '.join(codes)}"
    )


def build_metric_catalog(report: dict, metrics: dict) -> dict[str, dict]:
    catalog: dict[str, dict] = {}

    def add(
        metric_id: str,
        title: str,
        value: str,
        description: str,
        culprits: list[dict],
        prompt: str,
    ) -> None:
        catalog[metric_id] = {
            "id": metric_id,
            "title": title,
            "value": value,
            "description": description,
            "culprits": culprits,
            "prompt": prompt,
        }

    findings = report["findings"]
    page_reports = report["pageReports"]
    all_culprits = [culprit_from_finding(f, next((p for p in page_reports if p["url"] == f.get("slug")), None)) for f in findings]
    pages_with_issues = [page for page in page_reports if page["findings"]]
    clean_pages = [page for page in page_reports if not page["findings"]]
    orphan_findings = [f for f in findings if f["code"] == "pagerank-orphan"]
    orphan_culprits = [culprit_from_finding(f) for f in orphan_findings]
    failed_checks = [check for check in report["siteChecks"] if not check["ok"]]
    live_failures = [f for f in findings if f["code"] == "live-url-fail"]

    add(
        "seo-score",
        "Current SEO score",
        f"{metrics['currentScore']}/100",
        "Composite score from metadata, H1 structure, content depth, internal links, and live HTTP checks.",
        all_culprits or empty_culprit("Score is at maximum — no automated findings."),
        prompt_for_findings(findings),
    )
    add(
        "improvement-headroom",
        "Improvement headroom",
        f"+{metrics['improvement']}",
        "Points available if all score-deducting issues are resolved.",
        all_culprits or empty_culprit("No headroom — score is already optimal."),
        prompt_for_findings(findings) if metrics["improvement"] else "No action needed — score is already at 100.",
    )
    add(
        "score-vs-optimal",
        "Score vs optimal",
        f"{metrics['currentScore']} of {metrics['potentialScore']}",
        "Gap between current composite score and the maximum possible score.",
        all_culprits or empty_culprit("Already at optimal score."),
        prompt_for_findings(findings),
    )
    add(
        "kpi-total-findings",
        "Total findings",
        str(len(findings)),
        f"{metrics['severityCounts']['high']} high · {metrics['severityCounts']['medium']} medium · {metrics['severityCounts']['low']} low priority",
        all_culprits or empty_culprit("No findings detected."),
        prompt_for_findings(findings),
    )
    add(
        "kpi-pages-needing-work",
        "Pages needing work",
        str(metrics["pagesWithIssues"]),
        f"{metrics['cleanPages']} pages pass all automated checks",
        [
            {**culprit_from_page(page, finding["detail"]), "severity": finding["severity"]}
            for page in pages_with_issues
            for finding in page["findings"]
        ]
        or empty_culprit("Every page passes automated checks."),
        prompt_for_findings(findings) if pages_with_issues else "All pages are clean — no action required.",
    )
    add(
        "kpi-link-coverage",
        "Link coverage",
        f"{report['pageRank']['coverage']}%",
        f"{report['pageRank']['pagesAnalyzed']} pages · {report['pageRank']['edges']} internal edges",
        orphan_culprits or empty_culprit(f"{report['pageRank']['coverage']}% of pages receive inbound links."),
        prompt_for_code("pagerank-orphan", [f["slug"] for f in orphan_findings]) if orphan_findings else "Maintain internal linking when adding new pages.",
    )
    add(
        "kpi-site-pagerank",
        "Site PageRank",
        f"{report['pageRank']['siteToolbar']}/10",
        "Simulated sitewide authority based on internal link graph.",
        orphan_culprits[:15] or empty_culprit("No critically low-rank pages detected."),
        prompt_for_code("pagerank-orphan", [f["slug"] for f in orphan_findings]) if orphan_findings else "Sitewide PageRank looks healthy.",
    )
    add(
        "kpi-site-checks",
        "Site checks passing",
        f"{metrics['checksPassing']}/{metrics['totalChecks']}",
        "Infrastructure readiness: robots.txt, sitemap, live HTTP checks, link coverage",
        [
            {"title": check["label"], "url": "", "file": check["id"], "detail": check["detail"]}
            for check in failed_checks
        ]
        or empty_culprit("All infrastructure checks pass."),
        f"Fix failing site checks: {', '.join(c['label'] for c in failed_checks)}." if failed_checks else "All infrastructure checks pass.",
    )
    add(
        "kpi-improvement",
        "Improvement available",
        f"+{metrics['improvement']}",
        "Points between current score and a perfect score of 100",
        all_culprits or empty_culprit("No improvement available."),
        prompt_for_findings(findings),
    )

    for severity in ("high", "medium", "low"):
        severity_findings = [f for f in findings if f["severity"] == severity]
        add(
            f"severity-{severity}",
            f"{severity.capitalize()} severity findings",
            str(len(severity_findings)),
            f"Findings classified as {severity} priority",
            [culprit_from_finding(f) for f in severity_findings]
            or empty_culprit(f"No {severity}-severity findings."),
            prompt_for_findings(severity_findings) if severity_findings else f"No {severity}-severity findings to fix.",
        )

    add(
        "findings-total",
        "All findings",
        str(len(findings)),
        "Total automated SEO findings across metadata, structure, content, and links",
        all_culprits or empty_culprit("No findings."),
        prompt_for_findings(findings),
    )

    for code, count in metrics["topIssues"]:
        code_findings = [f for f in findings if f["code"] == code]
        add(
            f"issue-{code}",
            ISSUE_LABELS.get(code, code),
            str(count),
            f"{count} finding{'s' if count != 1 else ''} in this category",
            [culprit_from_finding(f) for f in code_findings] or empty_culprit("No findings in this category."),
            prompt_for_code(code, [f.get("slug", "") for f in code_findings]),
        )

    for item in metrics["scoreBreakdown"]:
        metric_id = item["metricId"]
        code_map = {
            "score-basic-seo": "missing-meta",
            "score-structure": "bad-h1",
            "score-content": "thin-content",
            "score-links": "pagerank-orphan",
            "score-health": "live-url-fail",
        }
        code = code_map.get(metric_id)
        code_findings = [f for f in findings if f["code"] == code] if code else []
        add(
            metric_id,
            item["label"],
            f"{item['current']}/{item['max']}",
            f"Score component contributing up to {item['max']} points",
            [culprit_from_finding(f) for f in code_findings]
            or empty_culprit(f"Full {item['max']}/{item['max']} points — no culprits."),
            prompt_for_code(code, [f.get("slug", "") for f in code_findings]) if code_findings else f"Maintain {item['label']} quality.",
        )

    add(
        "page-health-clean",
        "Clean pages",
        str(metrics["cleanPages"]),
        "Pages with zero automated findings",
        [culprit_from_page(page, "Passes all automated checks") for page in clean_pages[:25]]
        or empty_culprit("No clean pages."),
        "These pages pass automated checks. Review annually for keyword freshness.",
    )
    add(
        "page-health-issues",
        "Pages needing work",
        str(metrics["pagesWithIssues"]),
        "Pages with one or more automated findings",
        [culprit_from_page(page, ", ".join(f["code"] for f in page["findings"])) for page in pages_with_issues],
        prompt_for_findings(findings),
    )

    for check in report["siteChecks"]:
        add(
            f"site-check-{check['id']}",
            check["label"],
            "Pass" if check["ok"] else "Fail",
            check["detail"],
            empty_culprit(check["detail"]) if check["ok"] else [{"title": check["label"], "url": "", "file": check["id"], "detail": check["detail"]}],
            f"Maintain: {check['label']} — {check['detail']}" if check["ok"] else f"Fix failing check \"{check['label']}\": {check['detail']}",
        )

    summary_rows = [
        ("summary-missing-meta", "Missing metadata", report["summary"]["missingMeta"], "missing-meta"),
        ("summary-bad-h1", "Bad H1 count", report["summary"]["badH1"], "bad-h1"),
        ("summary-thin-content", "Thin content", report["summary"]["thinContent"], "thin-content"),
        ("summary-title-too-long", "Titles too long", report["summary"]["titleTooLong"], "title-too-long"),
        ("summary-live-failures", "Live URL failures", report["summary"]["liveFailures"], "live-url-fail"),
        ("summary-orphan-pages", "Orphan pages", report["summary"]["orphanPages"], "pagerank-orphan"),
    ]
    for metric_id, label, value, code in summary_rows:
        code_findings = [f for f in findings if f["code"] == code]
        add(
            metric_id,
            label,
            str(value),
            f"{value} page{'s' if value != 1 else ''} in this category",
            [culprit_from_finding(f) for f in code_findings] or empty_culprit(f"Zero {label.lower()}."),
            prompt_for_code(code, [f.get("slug", "") for f in code_findings]) if code_findings else f"No {label.lower()} to fix.",
        )

    for page in report["pageRank"]["topPages"][:15]:
        report_page = next((item for item in page_reports if item["url"] == page["url"]), None)
        rank_id = page["url"].replace("/", "_").strip("_") or "home"
        add(
            f"rank-{rank_id}",
            page["url"],
            f"{page['toolbar']}/10",
            f"{page['inbound']} inbound · {page['outbound']} outbound links",
            [
                {
                    "title": (report_page or {}).get("title") or page["url"],
                    "url": page["url"],
                    "file": (report_page or {}).get("file") or page["url"],
                    "detail": report_page["suggestions"][0] if report_page and report_page.get("suggestions") else "No automated findings.",
                }
            ],
            (report_page or {}).get("suggestions", ["Review internal links and metadata."])[0],
        )

    if live_failures:
        add(
            "metric-live-health",
            "Live site health",
            f"{report['liveChecks']['total'] - report['liveChecks']['bad_count']}/{report['liveChecks']['total']} OK",
            "Sitemap URLs returning HTTP 200",
            [{"title": f.get("detail", ""), "url": f.get("slug", ""), "file": f.get("slug", ""), "detail": f.get("detail", "")} for f in live_failures],
            prompt_for_code("live-url-fail", [f.get("slug", "") for f in live_failures]),
        )

    return catalog
