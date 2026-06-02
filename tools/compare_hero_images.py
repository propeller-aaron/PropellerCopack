"""Compare bloc-7 hero images between src and live pages."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "PropellerCopack v.3"

from apply_v3_from_src import SLUG_MAP  # noqa: E402


def hero_img(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    block = re.search(r'id="bloc-7">([\s\S]*?)<!-- bloc-7 END -->', text, re.I)
    if not block:
        return None
    img = re.search(r'data-src="([^"]+)"', block.group(1))
    return img.group(1) if img else None


def main() -> None:
    mismatches = []
    for src_slug, live_slug in sorted(SLUG_MAP.items()):
        si = hero_img(SRC / src_slug / "index.html")
        li = hero_img(ROOT / live_slug / "index.html")
        ok = si == li
        if not ok and si and li:
            ok = si.replace("../img/", "") == li.replace("../img/", "")
        status = "OK" if ok else "MISMATCH"
        print(f"{status} {src_slug} -> {live_slug}")
        print(f"  src:  {si}")
        print(f"  live: {li}")
        if not ok:
            mismatches.append((live_slug, src_slug, si, li))

    print(f"\n{len(mismatches)} mismatches in mapped pages")


if __name__ == "__main__":
    main()
