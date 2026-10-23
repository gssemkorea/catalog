"""Turn the frozen dist/index.html into one self-contained HTML file (USB / e-mail).

    python tools/inline.py [dist/index.html] [--out dist/Osteo-Fit_CMF_Catalog.html]
                           [--width 640] [--quality 80] [--max-mb 9] [--theme dark|light]

CSS and JS are inlined and every static/ image becomes a data: URI. Product photos are
embedded ONCE per key (not once per <img>): the tags keep only data-img and the page
script fills src from window.CAT, exactly like the original single-file catalogue.
Each product is re-encoded from the 800w variant to --width/--quality so the file stays
small; the zoom modal reuses the same image.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import mimetypes
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import config  # noqa: E402

mimetypes.add_type("image/webp", ".webp")
PRODUCT_RE = re.compile(r"products/(.+?)-(?:400|800|full)\.[0-9a-f]{8}\.webp$")


def data_uri_file(path: Path, cache: dict) -> str:
    key = str(path)
    if key not in cache:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        cache[key] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    return cache[key]


def product_uri(path: Path, width: int, quality: int) -> tuple[str, int, int]:
    with Image.open(path) as im:
        im = im.convert("RGBA") if "A" in im.getbands() else im.convert("RGB")
        if im.width > width:
            im = im.resize((width, max(1, round(im.height * width / im.width))), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=quality, method=6)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii"), im.width, im.height


def inline(index: Path, out: Path, width: int, quality: int, theme: str | None) -> int:
    root = index.parent
    html = index.read_text(encoding="utf-8")
    cache: dict = {}

    # css / js / preloads
    html = re.sub(r'<link rel="stylesheet" href="(static/[^"]+)">',
                  lambda m: "<style>\n" + (root / m.group(1)).read_text(encoding="utf-8") + "\n</style>", html)
    html = re.sub(r'<script src="(static/[^"]+)" defer></script>',
                  lambda m: "<script>\n" + (root / m.group(1)).read_text(encoding="utf-8") + "\n</script>", html)
    html = re.sub(r'<link rel="preload" as="image"[^>]*>\n?', "", html)
    # banner <style>: drop the @media (md / xl) variants so each photo is embedded once
    def banners_lg_only(m):
        body = re.sub(r"@media[^{]*\{(?:[^{}]*\{[^{}]*\})*\s*\}", "", m.group(1))
        return '<style id="banners">' + body + "</style>"
    html = re.sub(r'<style id="banners">(.*?)</style>', banners_lg_only, html, flags=re.S)

    # product map: one re-encoded data URI per key
    cat_m = re.search(r"<script>window\.CAT=(\{.*?\})</script>", html, re.S)
    cat = json.loads(cat_m.group(1))
    for key, e in cat["p"].items():
        uri, w, h = product_uri(root / e["m"], width, quality)
        e.update(m=uri, f=None, mw=w, fw=None)  # modal falls back to m
    cat_json = json.dumps(cat, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace(cat_m.group(0), "<script>window.CAT=" + cat_json + "</script>")

    # <img> tags
    def img_tag(m):
        tag = m.group(0)
        src = re.search(r'\ssrc="(static/[^"]+)"', tag).group(1)
        pm = PRODUCT_RE.search(src)
        tag = re.sub(r'\s(?:srcset|sizes)="[^"]*"', "", tag)
        if pm:  # product: drop src, keep key; script fills it from window.CAT
            return re.sub(r'\ssrc="static/[^"]+"', f' data-img="{pm.group(1)}"', tag)
        return re.sub(r'\ssrc="static/[^"]+"', ' src="' + data_uri_file(root / src, cache) + '"', tag)

    html = re.sub(r'<img\b[^>]*\ssrc="static/[^"]+"[^>]*>', img_tag, html)

    # css custom-property backgrounds in inline styles
    html = re.sub(r"url\((static/[^)]+)\)", lambda m: "url(" + data_uri_file(root / m.group(1), cache) + ")", html)

    if theme:
        html = html.replace('<html lang="ko">', f'<html lang="ko" data-theme="{theme}">', 1)

    left = re.findall(r".{0,80}static/[^\"')\s]+", re.sub(r"data:[^\"')]+", "", html))
    assert not left, "static/ references remain:\n" + "\n".join(left[:10])
    out.write_text(html, encoding="utf-8", newline="\n")
    return out.stat().st_size


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("index", type=Path, nargs="?", default=config.DIST / "index.html")
    ap.add_argument("--out", type=Path, default=config.DIST / "Osteo-Fit_CMF_Catalog.html")
    ap.add_argument("--width", type=int, default=640, help="product image width embedded (default 640)")
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--max-mb", type=float, default=9.0)
    ap.add_argument("--theme", choices=["dark", "light"], default=None,
                    help="default theme when the viewer has no stored preference")
    args = ap.parse_args()
    config.assert_safe_output(args.out)
    size = inline(args.index, args.out, args.width, args.quality, args.theme)
    mb = size / 1_048_576
    print(f"{args.out}  {mb:.2f} MB (limit {args.max_mb} MB)")
    return 0 if mb <= args.max_mb else 1


if __name__ == "__main__":
    sys.exit(main())
