from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ROOT.glob("*/index.html"):
    t = p.read_text(encoding="utf-8")
    t2 = t.replace('<script src="../js/jqBootstrapValidation.js"></script>\r\n', "").replace(
        '<script src="../js/jqBootstrapValidation.js"></script>\n', ""
    )
    if t != t2:
        p.write_text(t2, encoding="utf-8")
        print("stripped", p.relative_to(ROOT))
