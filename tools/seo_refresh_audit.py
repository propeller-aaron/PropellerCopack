from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
CACHE = ROOT / "seo" / "audit-cache.json"
EXCLUDE = {"seo", "img", "js", "css", "fonts", "includes", "tools"}


def slug_from_path(path: Path) -> str:
    return "/" if path.parent == ROOT else f"/{path.parent.name}/"


def normalize_link(href: str, slug: str) -> str | None:
    if href.startswith("http"):
        if "propellercopack.com" not in href:
            return None
        href = href.split("propellercopack.com", 1)[1]
    if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return None
    if href.startswith("/"):
        out = href
    elif href.startswith("../"):
        out = "/" + href.replace("../", "")
    elif href.startswith("./"):
        out = ("/" if slug == "/" else slug) + href[2:]
    else:
        return None
    out = out.split("#", 1)[0].split("?", 1)[0]
    if not out.endswith("/") and "." not in out.rsplit("/", 1)[-1]:
        out += "/"
    return out


def collect_pages() -> list[Path]:
    pages = [p for p in ROOT.glob("*/index.html") if p.parent.name not in EXCLUDE]
    pages.append(ROOT / "index.html")
    return pages


def strip_tags_fragment(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_canonical_path(path: str) -> str:
    path = path.strip()
    if not path or path == "/":
        return "/"
    return path if path.endswith("/") else path + "/"


def title_h1_mismatch_heuristic(title: str, h1_text: str) -> bool:
    """True when main title tokens poorly overlap primary H1 (metadata drift)."""
    if not title or not h1_text:
        return False
    main = re.sub(r"\s*\|\s*.*$", "", title).strip()
    ta = set(re.findall(r"[a-z0-9]+", main.lower()))
    hb = set(re.findall(r"[a-z0-9]+", h1_text.lower()))
    if not ta or not hb:
        return False
    inter = ta & hb
    denom = min(len(ta), len(hb))
    return len(inter) / max(denom, 1) < 0.34


def compute_inputs_hash() -> str:
    h = hashlib.sha256()
    for path in sorted(collect_pages(), key=lambda p: str(p.relative_to(ROOT))):
        rel = path.relative_to(ROOT)
        h.update(str(rel).encode())
        h.update(str(path.stat().st_mtime_ns).encode())
    h.update(b"sitemap.xml")
    h.update(str(SITEMAP.stat().st_mtime_ns).encode())
    return h.hexdigest()[:24]


def word_count_from_html(text: str) -> int:
    clean = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    clean = re.sub(r"<style[\s\S]*?</style>", " ", clean, flags=re.I)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return len(clean.split())


def parse_page(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    slug = slug_from_path(path)
    title_match = re.search(r"<title>([^<]+)</title>", text, re.I)
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text, re.I)
    canon_match = re.search(
        r'<link\s+rel="canonical"\s+href="https://propellercopack\.com([^"]*)"',
        text,
        re.I,
    )
    h1_blocks = re.findall(r"<h1\b[^>]*>([\s\S]*?)</h1>", text, re.I)
    h1_text = strip_tags_fragment(h1_blocks[0]) if h1_blocks else ""
    h1_match = re.findall(r"<h1\b", text, re.I)

    hrefs = re.findall(r'href="([^"]+)"', text, re.I)
    internal_links = []
    for href in hrefs:
        link = normalize_link(href, slug)
        if link:
            internal_links.append(link)

    canon_path = canon_match.group(1).strip() if canon_match else ""
    title_plain = title_match.group(1).strip() if title_match else ""
    canonical_ok = bool(canon_match) and norm_canonical_path(canon_path) == norm_canonical_path(slug)

    return {
        "slug": slug,
        "title_text": title_plain,
        "description_text": desc_match.group(1).strip() if desc_match else "",
        "canonical_path": canon_path,
        "title_present": bool(title_match),
        "description_present": bool(desc_match and desc_match.group(1).strip()),
        "canonical_present": bool(canon_match),
        "canonical_ok": canonical_ok,
        "description_has_html": bool(desc_match and "<" in desc_match.group(1)),
        "h1_count": len(h1_match),
        "h1_text": h1_text,
        # Home title is brand-heavy; skip overlap heuristic for /
        "title_h1_mismatch": slug != "/"
        and title_h1_mismatch_heuristic(title_plain, h1_text),
        "word_count": word_count_from_html(text),
        "internal_links_raw_count": len(internal_links),
        "internal_links": internal_links,
    }


def compute_pagerank(rows: list[dict]) -> dict[str, float]:
    slugs = sorted({r["slug"] for r in rows})
    slug_set = set(slugs)
    outgoing = {
        r["slug"]: [l for l in r["internal_links"] if l in slug_set] for r in rows
    }
    n = len(slugs)
    d = 0.85
    pr = {s: 1.0 / n for s in slugs}
    for _ in range(40):
        nxt = {s: (1 - d) / n for s in slugs}
        for s in slugs:
            links = outgoing[s]
            if not links:
                share = d * pr[s] / n
                for t in slugs:
                    nxt[t] += share
            else:
                share = d * pr[s] / len(links)
                for t in links:
                    nxt[t] += share
        pr = nxt
    return pr


def run_live_checks() -> dict:
    xml = SITEMAP.read_text(encoding="utf-8")
    root = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [n.text for n in root.findall("sm:url/sm:loc", ns) if n.text]
    results = []
    bad = 0
    for url in urls:
        status = 0
        error = ""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = int(resp.getcode())
        except Exception as exc:  # noqa: BLE001
            status = 0
            error = str(exc)
        if status >= 400 or status == 0:
            bad += 1
        results.append({"url": url, "status": status, "error": error})
    return {"total": len(urls), "bad_count": bad, "results": results}


def main() -> None:
    ap = argparse.ArgumentParser(description="Crawl local HTML, live sitemap HTTP checks, write seo/audit-cache.json")
    ap.add_argument(
        "--force-live",
        action="store_true",
        help="Always re-fetch live HTTP status (ignore cache reuse for sitemap URLs).",
    )
    args = ap.parse_args()

    rows = sorted([parse_page(p) for p in collect_pages()], key=lambda r: r["slug"])
    pr = compute_pagerank(rows)
    slug_counts = defaultdict(int)
    for r in rows:
        slug_counts[r["slug"]] += 1

    inputs_hash = compute_inputs_hash()
    prev: dict = {}
    if CACHE.exists():
        try:
            prev = json.loads(CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = {}

    live_checks_source = "fresh_fetch"
    if (
        not args.force_live
        and prev.get("inputs_hash") == inputs_hash
        and isinstance(prev.get("live_checks"), dict)
    ):
        prev_live = prev["live_checks"]
        if prev_live.get("results"):
            live = prev_live
            live_checks_source = "reused_cache_unchanged_inputs"
        else:
            live = run_live_checks()
    else:
        live = run_live_checks()
        if args.force_live:
            live_checks_source = "forced_fresh_fetch"

    canonical_mismatch_slugs = [r["slug"] for r in rows if not r["canonical_ok"]]
    title_h1_mismatch_slugs = [r["slug"] for r in rows if r["title_h1_mismatch"]]

    out = {
        "generated_on": str(date.today()),
        "inputs_hash": inputs_hash,
        "live_checks_source": live_checks_source,
        "page_count": len(rows),
        "rows": rows,
        "missing_meta_slugs": [
            r["slug"]
            for r in rows
            if not (r["title_present"] and r["description_present"] and r["canonical_present"])
        ],
        "bad_h1_slugs": [r["slug"] for r in rows if r["h1_count"] != 1],
        "desc_html_slugs": [r["slug"] for r in rows if r["description_has_html"]],
        "canonical_mismatch_slugs": canonical_mismatch_slugs,
        "title_h1_mismatch_slugs": title_h1_mismatch_slugs,
        "duplicate_slugs": sorted([s for s, c in slug_counts.items() if c > 1]),
        "pagerank_full": sorted(pr.items(), key=lambda kv: kv[1], reverse=True),
        "pagerank_top": sorted(pr.items(), key=lambda kv: kv[1], reverse=True)[:10],
        "live_checks": live,
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({**out, "rows": f"[{len(rows)} pages]"}, indent=2))


if __name__ == "__main__":
    main()
