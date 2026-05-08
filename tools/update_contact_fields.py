from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INSERT_BLOCK = """    <div class="propeller-form-group">
      <label for="company">Company</label>
      <input id="company" name="company" type="text" required />
    </div>

    <div class="propeller-form-group">
      <label for="phone">Phone</label>
      <input id="phone" name="phone" type="tel" required />
    </div>

"""

ANCHOR = """    <div class="propeller-form-group">
      <label for="name">Name</label>
      <input id="name" name="name" type="text" required />
    </div>

"""


def update_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if 'id="contactForm"' not in text:
        return False
    if 'id="company"' in text and 'id="phone"' in text:
        return False
    if ANCHOR not in text:
        return False
    text = text.replace(ANCHOR, ANCHOR + INSERT_BLOCK, 1)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    updated = []
    targets = [ROOT / "index.html"] + sorted(ROOT.glob("*/index.html"))
    for path in targets:
        if not path.exists():
            continue
        if update_file(path):
            updated.append(path.relative_to(ROOT).as_posix())
    print(f"updated {len(updated)} files")
    for rel in updated:
        print(rel)


if __name__ == "__main__":
    main()
