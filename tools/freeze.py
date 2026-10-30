"""Render the catalog to a static folder that works over file:// and any static host.

    python tools/freeze.py [--out dist]

Produces <out>/index.html and <out>/static/... (only the files the page references
plus every product variant so the zoom modal works offline).
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import config  # noqa: E402
from catalog import create_app  # noqa: E402

# route -> file under <out>; every page sits at the root so relative static/ paths work.
# GitHub Pages serves /3d from 3d.html.
PAGES = {"/": "index.html", "/3d": "3d.html"}

STATIC_REF = re.compile(r"""(?<![\w/])static/([A-Za-z0-9_./@-]+?)(?:\?v=[0-9a-f]+)?(?=["')\s,])""")


def freeze(out: Path) -> tuple[Path, int]:
    app = create_app({"ASSET_BASE": "static", "TESTING": True})
    out.mkdir(parents=True, exist_ok=True)
    refs: set[str] = set()
    with app.test_client() as c:
        for route, name in PAGES.items():
            r = c.get(route)
            assert r.status_code == 200, (route, r.status)
            html = r.get_data(as_text=True)
            html = re.sub(r"(static/[^\"'\s)]+?)\?v=[0-9a-f]+", r"\1", html)
            (out / name).write_text(html, encoding="utf-8", newline="\n")
            refs |= set(STATIC_REF.findall(html))

    man = app.extensions["manifest"]
    for e in man.get("products", {}).values():
        for v in ("t", "m", "f"):
            refs.add(e[v])
    src_root = Path(app.static_folder)
    n = 0
    for rel in sorted(refs):
        s = src_root / rel
        if not s.exists():
            print("WARN missing static file:", rel)
            continue
        d = out / "static" / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        if not d.exists() or d.stat().st_size != s.stat().st_size or d.stat().st_mtime_ns < s.stat().st_mtime_ns:
            shutil.copy2(s, d)
        n += 1
    return out / "index.html", n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=config.DIST)
    args = ap.parse_args()
    config.assert_safe_output(args.out)
    index, n = freeze(args.out)
    total = index.stat().st_size + sum(f.stat().st_size for f in (args.out / "static").rglob("*") if f.is_file())
    print(f"{index}  files={n}  size={total/1_048_576:.1f} MB")


if __name__ == "__main__":
    main()
