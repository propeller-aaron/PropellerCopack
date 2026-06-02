"""Regenerate SEO audit, hero index, and unified status dashboard."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def run(script: str) -> None:
    path = TOOLS / script
    print(f"\n==> {script}")
    subprocess.run([sys.executable, str(path)], check=True, cwd=ROOT)


def main() -> None:
    run("seo_refresh_audit.py")
    run("rebuild_hero_index.py")
    run("generate_status_page.py")
    print("\nAll status artifacts regenerated.")


if __name__ == "__main__":
    main()
