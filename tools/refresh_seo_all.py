"""Run audit cache refresh, SEO report HTML, and hero-image index rebuild."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    py = sys.executable
    subprocess.check_call([py, str(ROOT / "tools" / "seo_refresh_audit.py"), "--force-live"], cwd=ROOT)
    subprocess.check_call([py, str(ROOT / "tools" / "generate_seo_report.py")], cwd=ROOT)
    subprocess.check_call([py, str(ROOT / "tools" / "rebuild_hero_index.py")], cwd=ROOT)
    print("Done: audit-cache.json, seo/index.html, seo/hero-images/index.html")


if __name__ == "__main__":
    main()
