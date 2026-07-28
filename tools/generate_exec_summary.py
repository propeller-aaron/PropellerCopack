"""Generate a plain-English, non-technical website health summary for non-technical stakeholders."""
from __future__ import annotations

import html
from pathlib import Path

from generate_seo_report import build_dashboard_metrics, build_report_model, format_display_date, load_audit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "status" / "executive-summary" / "index.html"


def grade_for_score(score: int) -> tuple[str, str, str]:
    """Return (label, color, emoji) for a 0-100 score."""
    if score >= 90:
        return "Excellent", "#1b7f3b", "✅"
    if score >= 75:
        return "Good", "#0b3a5b", "✅"
    if score >= 60:
        return "Fair", "#d68910", "⚠️"
    return "Needs attention", "#b42318", "⛔"


def build_attention_items(summary: dict) -> list[str]:
    items: list[str] = []
    if summary["liveFailures"]:
        n = summary["liveFailures"]
        items.append(
            f"<strong>{n} page{'s' if n != 1 else ''} on the live website {'are' if n != 1 else 'is'} not loading correctly.</strong> "
            "This should be looked at right away since visitors could be affected."
        )
    if summary["missingMeta"]:
        n = summary["missingMeta"]
        items.append(
            f"<strong>{n} page{'s' if n != 1 else ''}</strong> {'are' if n != 1 else 'is'} missing some of the behind-the-scenes information "
            "search engines use to describe the page in results."
        )
    if summary["badH1"]:
        n = summary["badH1"]
        items.append(
            f"<strong>{n} page{'s' if n != 1 else ''}</strong> {'have' if n != 1 else 'has'} a heading layout that could confuse search engines "
            "about what the page is really about."
        )
    if summary["thinContent"]:
        n = summary["thinContent"]
        items.append(
            f"<strong>{n} page{'s' if n != 1 else ''}</strong> {'have' if n != 1 else 'has'} less written content than recommended. "
            "Adding more detail to these pages could help them rank better in search."
        )
    if summary["orphanPages"]:
        n = summary["orphanPages"]
        items.append(
            f"<strong>{n} page{'s' if n != 1 else ''}</strong> {'are' if n != 1 else 'is'} hard for search engines to discover because few other "
            "pages link to them."
        )
    if summary["titleTooLong"]:
        n = summary["titleTooLong"]
        items.append(
            f"<strong>{n} page title{'s' if n != 1 else ''}</strong> {'are' if n != 1 else 'is'} a little long and may get cut off in search results. "
            "This is a minor, cosmetic issue."
        )
    return items


def build_working_well_items(report: dict) -> list[str]:
    items: list[str] = []
    for check in report["siteChecks"]:
        if check["ok"]:
            friendly = {
                "robots": "Search engines are allowed to visit the website",
                "sitemap": "The website provides search engines a map of all its pages",
                "live-http": "Every page on the website is online and loading correctly",
                "link-coverage": "Pages link to each other well, making the site easy to navigate",
                "metadata": "Every page has the descriptive information search engines look for",
            }.get(check["id"], check["label"])
            items.append(friendly)
    return items


def render(audit: dict) -> str:
    report = build_report_model(audit)
    metrics = build_dashboard_metrics(report)
    generated = format_display_date(report["generatedAt"])
    score = metrics["currentScore"]
    label, color, emoji = grade_for_score(score)

    total_pages = len(report["pageReports"])
    clean_pages = metrics["cleanPages"]
    pages_with_issues = metrics["pagesWithIssues"]

    attention_items = build_attention_items(report["summary"])
    working_items = build_working_well_items(report)

    attention_html = (
        "".join(f"<li>{item}</li>" for item in attention_items)
        if attention_items
        else "<li>Nothing needs attention right now — great job!</li>"
    )
    working_html = "".join(f"<li>{html.escape(item)}</li>" for item in working_items)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>Website Health Report — Propeller Co-Pack</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 2rem 1.25rem 3rem;
    background: #f4f7fa;
    font: 19px/1.6 "Segoe UI", system-ui, sans-serif;
    color: #24303d;
  }}
  .exec-shell {{
    max-width: 46rem;
    margin: 0 auto;
  }}
  .exec-title {{
    margin: 0 0 0.25rem;
    font-size: 1.6rem;
    color: #0b3a5b;
  }}
  .exec-sub {{
    margin: 0 0 1.75rem;
    color: #5b6b7a;
    font-size: 1rem;
  }}
  .exec-banner {{
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 1.5rem 1.75rem;
    border-radius: 14px;
    background: #fff;
    border: 2px solid {color};
    margin-bottom: 1.75rem;
  }}
  .exec-banner-emoji {{
    font-size: 2.75rem;
    line-height: 1;
  }}
  .exec-banner-label {{
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: {color};
  }}
  .exec-banner-score {{
    margin: 0.2rem 0 0;
    color: #5b6b7a;
    font-size: 1.05rem;
  }}
  .exec-stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 1rem;
    margin-bottom: 1.75rem;
  }}
  .exec-stat {{
    background: #fff;
    border: 1px solid #e2e8ef;
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
  }}
  .exec-stat-value {{
    display: block;
    font-size: 1.8rem;
    font-weight: 700;
    color: #0b3a5b;
  }}
  .exec-stat-label {{
    display: block;
    margin-top: 0.15rem;
    color: #5b6b7a;
    font-size: 0.95rem;
  }}
  .exec-section {{
    background: #fff;
    border: 1px solid #e2e8ef;
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.5rem;
  }}
  .exec-section h2 {{
    margin: 0 0 1rem;
    font-size: 1.15rem;
    color: #0b3a5b;
  }}
  .exec-list {{
    margin: 0;
    padding: 0;
    list-style: none;
  }}
  .exec-list li {{
    position: relative;
    padding: 0.55rem 0 0.55rem 1.9rem;
    border-bottom: 1px solid #eef2f6;
  }}
  .exec-list li:last-child {{
    border-bottom: 0;
  }}
  .exec-attention li::before {{
    content: "⚠️";
    position: absolute;
    left: 0;
  }}
  .exec-attention.exec-list-clear li::before {{
    content: "✅";
  }}
  .exec-working li::before {{
    content: "✅";
    position: absolute;
    left: 0;
  }}
  .exec-footer {{
    color: #5b6b7a;
    font-size: 0.9rem;
    text-align: center;
    margin-top: 2rem;
  }}
  .exec-footer a {{
    color: #0b3a5b;
  }}
  @media (max-width: 560px) {{
    body {{ font-size: 17px; padding: 1.25rem 1rem 2.5rem; }}
    .exec-banner {{ flex-direction: column; text-align: center; }}
  }}
</style>
</head>
<body>
  <div class="exec-shell">
    <p class="exec-title">Propeller Co-Pack — Website Health Report</p>
    <p class="exec-sub">A plain-English summary, prepared {html.escape(generated)}.</p>

    <div class="exec-banner">
      <span class="exec-banner-emoji">{emoji}</span>
      <div>
        <p class="exec-banner-label">Overall: {html.escape(label)}</p>
        <p class="exec-banner-score">Score: {score} out of 100</p>
      </div>
    </div>

    <div class="exec-stats">
      <div class="exec-stat">
        <span class="exec-stat-value">{total_pages}</span>
        <span class="exec-stat-label">pages on the website checked</span>
      </div>
      <div class="exec-stat">
        <span class="exec-stat-value">{clean_pages}</span>
        <span class="exec-stat-label">pages in great shape already</span>
      </div>
      <div class="exec-stat">
        <span class="exec-stat-value">{pages_with_issues}</span>
        <span class="exec-stat-label">pages with room to improve</span>
      </div>
    </div>

    <div class="exec-section">
      <h2>What needs attention</h2>
      <ul class="exec-list exec-attention{' exec-list-clear' if not attention_items else ''}">{attention_html}</ul>
    </div>

    <div class="exec-section">
      <h2>What's working well</h2>
      <ul class="exec-list exec-working">{working_html}</ul>
    </div>

    <p class="exec-footer">
      This report is generated automatically from the website's SEO monitoring tool.<br>
      Questions? Contact Aaron at <a href="mailto:aaron@propellerinc.com">aaron@propellerinc.com</a>.
    </p>
  </div>
</body>
</html>
"""


def main() -> None:
    audit = load_audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(audit), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
