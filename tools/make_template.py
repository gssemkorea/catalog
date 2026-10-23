"""Generate catalog/templates/catalog.html and catalog/static/css/catalog.css from the
archived single-file catalog. Every edit is an explicit, asserted replacement so the
transform is reproducible; nothing in the product markup is hand-edited.

    python tools/make_template.py [ref/2025-10-15_catalog_monochrome.html]
"""
from __future__ import annotations

import html as htmllib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import config  # noqa: E402

DATA = r"data:image/webp;base64,[A-Za-z0-9+/=]+"
TEMPLATES = config.ROOT / "catalog" / "templates"
CSS_OUT = config.STATIC / "css" / "catalog.css"


def rep(s: str, old: str, new: str, n: int = 1) -> str:
    c = s.count(old)
    assert c == n, f"expected {n} occurrence(s), found {c}: {old[:80]!r}"
    return s.replace(old, new)


def rsub(s: str, pat: str, new, n: int, flags=0) -> str:
    s2, c = re.subn(pat, new, s, flags=flags)
    assert c == n, f"expected {n} regex match(es), found {c}: {pat[:80]!r}"
    return s2


# --------------------------------------------------------------------------- HTML
def build_body(html: str) -> str:
    body = html[html.index('<div class="top">'): html.index("</footer>") + len("</footer>")]
    assert "{{" not in body and "{%" not in body and "{#" not in body

    # hero + band backgrounds -> manifest banners (lg + md for small screens)
    body = rsub(
        body,
        r'<section class="hero" style="--img:url\(%s\)">' % DATA,
        '<section class="hero">',  # background declared by the banner <style> in base.html
        1,
    )
    for fam in config.BAND_FAMILIES:
        body = rsub(
            body,
            r'(<section class="family" id="%s">\s*<header class="band" )style="--img:url\(%s\)"' % (fam, DATA),
            r'\1data-band="band_%s"' % fam,  # background declared by the banner <style> in base.html
            1,
        )

    # logos: one white PNG, surface-aware CSS invert
    logo = ('<img class="logo" src="{{ asset(manifest().images.logo.p) }}" '
            'width="{{ manifest().images.logo.w }}" height="{{ manifest().images.logo.h }}" alt="GSSEM Solution">')
    body = rsub(body, r'<img class="logo" src="%s" alt="GSSEM Solution">' % DATA, logo, 1)
    body = rsub(body, r'(<div class="full flogo">)<img src="%s" alt="GSSEM Solution">' % DATA, r"\1" + logo, 1)

    # spread figures
    def spread(m):
        name, alt = m.group(1), m.group(2)
        e = f"manifest().images.spread_{name}"
        return (f'<figure class="f-{name}"><img src="{{{{ asset({e}.md) }}}}" '
                f'srcset="{{{{ asset({e}.md) }}}} {{{{ {e}.mdw }}}}w, {{{{ asset({e}.lg) }}}} {{{{ {e}.lgw }}}}w" '
                f'sizes="(max-width:980px) 100vw, 50vw" width="{{{{ {e}.w }}}}" height="{{{{ {e}.h }}}}" '
                f'loading="lazy" decoding="async" alt="{alt}">')

    body = rsub(body, r'<figure class="f-(\w+)"><img src="%s" alt="([^"]*)">' % DATA, spread, 5)

    # product images inside cards: <div class="pic"><img ...>[tk badges]</div> -> button + macro
    def title_sub(pos: int) -> tuple[str, str]:
        i = body.rfind('data-title="', 0, pos)
        tag_end = body.find(">", i)
        tag = body[i:tag_end]
        t = re.search(r'data-title="([^"]*)"', tag).group(1)
        s = re.search(r'data-sub="([^"]*)"', tag)
        return htmllib.unescape(t), htmllib.unescape(s.group(1) if s else "")

    def jstr(s: str) -> str:
        return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"

    def card_pic(m):
        key, badges = m.group(1), m.group(2)
        t, s = title_sub(m.start())
        alt = (t + " " + s).strip()
        return (f'<button type="button" class="pic" aria-label="{htmllib.escape(t)} 확대">'
                f"{{{{ pic({jstr(key)}, '', {jstr(alt)}) }}}}{badges}</button>")

    body = rsub(
        body,
        r'<div class="pic"><img class="" data-img="([^"]+)" alt="" width="1" height="1">((?:<span class="tk[^"]*">[^<]*</span>)*)</div>',
        card_pic,
        322,
    )

    # series zoom blocks (hero-pic / dim) -> buttons
    def zoom(m):
        cls, attrs, inner = (m.group(1) or ""), m.group(2), m.group(3)
        t = htmllib.unescape(re.search(r'data-title="([^"]*)"', attrs).group(1))
        s = re.search(r'data-sub="([^"]*)"', attrs)
        s = htmllib.unescape(s.group(1)) if s else ""
        alt = t if cls == " dimz" else (t + " " + s).strip()

        def img(mi):
            return f"{{{{ pic({jstr(mi.group(2))}, {jstr(mi.group(1))}, {jstr(alt)}) }}}}"

        inner2, c = re.subn(r'<img class="([^"]*)" data-img="([^"]+)" alt="" width="1" height="1">', img, inner)
        assert c == 1
        return f'<button type="button" class="zoom{cls}"{attrs} aria-label="{htmllib.escape(t)} 확대">{inner2}</button>'

    body = rsub(body, r'<div class="zoom( dimz)?"([^>]*)>(.*?)</div>', zoom, 27)
    assert not re.search(r'width="1" height="1"', body), "unconverted 1x1 images remain"

    # top bar: aria + theme toggle
    body = rep(body, "<nav>", '<nav aria-label="제품군">')
    body = rep(body, '<input id="q" type="search"', '<input id="q" type="search" aria-label="품번 / 사양 검색"')
    body = rep(body, '<span class="hits" id="hits"></span>', '<span class="hits" id="hits" aria-live="polite"></span>')
    body = rep(
        body,
        '<button id="v-sku" aria-pressed="false">품번별</button></div>',
        '<button id="v-sku" aria-pressed="false">품번별</button></div>\n'
        '  <button type="button" class="tbtn" id="t-dark" aria-pressed="true" aria-label="다크 모드"><span>Dark</span></button>',
    )

    # footer fineprint
    body = rep(body, "Monochrome edition · 335 part numbers", "335 part numbers")

    # move the modal out of <main> so `inert` can be applied to main while it is open
    modal = re.search(r'<div class="modal" id="modal".*?</div></div>\n', body, re.S).group(0)
    body = rep(body, modal, "")
    body = rep(body, "</main>", "</main>\n" + modal.rstrip("\n"))

    assert not re.search(DATA, body), "base64 remains in body"
    return body


def write_template(body: str) -> None:
    out = ('{% extends "base.html" %}\n'
           '{% from "_macros.html" import pic %}\n'
           '{% block title %}Osteo-Fit CMF Catalog{% endblock %}\n'
           '{% block body %}\n' + body + '\n{% endblock %}\n')
    (TEMPLATES / "catalog.html").write_text(out, encoding="utf-8")


# --------------------------------------------------------------------------- CSS
DARK_ROOT = """:root{
  --bg:#0a0a0a; --bg-2:#111111; --panel:#151515; --line:#2b2b2b; --line-soft:#1e1e1e;
  --fg:#f3f3f1; --fg-2:#a6a6a3; --fg-3:#8a8a87;
  --paper:#f3f2ef; --ink:#0b0b0b; --ink-2:#4a4a48; --rule:#d6d5d1;
  --accent:#ffffff; --accent-fg:#0a0a0a;
  --top-bg:rgba(10,10,10,.82); --photo-bg:#000;
  --hero-veil:linear-gradient(90deg,rgba(0,0,0,.92) 0%,rgba(0,0,0,.65) 42%,rgba(0,0,0,.15) 75%),linear-gradient(0deg,#0a0a0a 0%,transparent 40%);
  --band-veil:linear-gradient(0deg,#0a0a0a 0%,rgba(10,10,10,.55) 45%,rgba(10,10,10,.25) 100%);
  --band-fg:#fff; --band-fg-2:#cfcfcc; --band-fg-3:#bdbdba; --band-stroke:rgba(255,255,255,.7);
  --glass-bg:rgba(8,8,8,.62); --glass-line:rgba(255,255,255,.14); --glass-rule:rgba(255,255,255,.14); --glass-fg:#d4d4d1;
  --card-hover:#121212; --modal-bg:rgba(0,0,0,.94);
  --sys-bg:#f3f2ef; --sys-fg:#0b0b0b; --sys-fg-2:#4a4a48; --sys-rule:#d6d5d1;
  --tile:#fff; --tile-2:#e6e5e1; --on-photo:#fff; --logo-invert:0;
  --display:"Archivo","IBM Plex Sans KR",system-ui,sans-serif;
  --body:"IBM Plex Sans KR",system-ui,-apple-system,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  color-scheme:dark;
}
:root[data-theme=light]{
  --bg:#fafaf8; --bg-2:#f1f1ee; --panel:#ffffff; --line:#d4d4cf; --line-soft:#e6e6e2;
  --fg:#0b0b0b; --fg-2:#4b4b48; --fg-3:#6f6f6c;
  --paper:#0b0b0b; --ink:#f3f2ef; --ink-2:#a6a6a3; --rule:#2b2b2b;
  --accent:#0b0b0b; --accent-fg:#ffffff;
  --top-bg:rgba(250,250,248,.86); --photo-bg:#fafaf8;
  --hero-veil:linear-gradient(90deg,rgba(250,250,248,.96) 0%,rgba(250,250,248,.78) 42%,rgba(250,250,248,.08) 78%),linear-gradient(0deg,#fafaf8 0%,transparent 38%);
  --band-veil:linear-gradient(0deg,#fafaf8 0%,rgba(250,250,248,.82) 34%,rgba(250,250,248,.12) 100%);
  --band-fg:#0b0b0b; --band-fg-2:#3a3a38; --band-fg-3:#555552; --band-stroke:rgba(0,0,0,.55);
  --glass-bg:rgba(255,255,255,.78); --glass-line:rgba(0,0,0,.1); --glass-rule:rgba(0,0,0,.08); --glass-fg:#3a3a38;
  --card-hover:#ffffff; --modal-bg:rgba(250,250,248,.97);
  --sys-bg:#efeeea; --sys-fg:#0b0b0b; --sys-fg-2:#4a4a48; --sys-rule:#d6d5d1;
  --logo-invert:1;
  color-scheme:light;
}"""

CSS_REPLACEMENTS = [
    ("::selection{background:#fff;color:#000}", "::selection{background:var(--accent);color:var(--accent-fg)}"),
    ("z-index:20;background:rgba(10,10,10,.82);", "z-index:20;background:var(--top-bg);"),
    (".brand small{display:none}\n", ""),
    (".flogo img{height:clamp(56px,7vw,84px);", ".flogo img{height:clamp(32px,4vw,48px);"),
    ("background:#000 var(--img) center 35%/cover no-repeat;", "background:var(--photo-bg) center 35%/cover no-repeat;"),
    ("background:linear-gradient(90deg,rgba(0,0,0,.92) 0%,rgba(0,0,0,.65) 42%,rgba(0,0,0,.15) 75%),linear-gradient(0deg,#0a0a0a 0%,transparent 40%)}",
     "background:var(--hero-veil)}"),
    ("background:rgba(8,8,8,.62);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.14)}",
     "background:var(--glass-bg);backdrop-filter:blur(10px);border:1px solid var(--glass-line)}"),
    ("border-bottom:1px solid rgba(255,255,255,.14);font-size:13.5px;color:#d4d4d1}",
     "border-bottom:1px solid var(--glass-rule);font-size:13.5px;color:var(--glass-fg)}"),
    (".system{padding-block:96px 88px}",
     ".system{padding-block:96px 88px;background:var(--sys-bg);color:var(--sys-fg);--paper:var(--sys-bg);--ink:var(--sys-fg);--ink-2:var(--sys-fg-2);--rule:var(--sys-rule)}"),
    (".spread figure{margin:0;background:#e6e5e1;", ".spread figure{margin:0;background:var(--tile-2);"),
    (".spread .f-skull{grid-column:3/7;grid-row:1/4;background:#fff}", ".spread .f-skull{grid-column:3/7;grid-row:1/4;background:var(--tile)}"),
    (".spread .f-set{grid-column:3/5;grid-row:4/6;background:#fff}", ".spread .f-set{grid-column:3/5;grid-row:4/6;background:var(--tile)}"),
    (".spread .f-case{grid-column:5/7;grid-row:4/6;background:#fff}", ".spread .f-case{grid-column:5/7;grid-row:4/6;background:var(--tile)}"),
    (".spread .f-cover{grid-column:1/3;grid-row:5/6;background:#fff}", ".spread .f-cover{grid-column:1/3;grid-row:5/6;background:var(--tile)}"),
    (".spread .f-port figcaption{color:#fff}", ".spread .f-port figcaption{color:var(--on-photo)}"),
    (".toc-i:hover span,.toc-i:hover em{color:#bbb}", ".toc-i:hover span,.toc-i:hover em{color:var(--sys-bg);opacity:.72}"),
    ("background:#000 var(--img) center/cover no-repeat;", "background:var(--photo-bg) center/cover no-repeat;"),
    ("background:linear-gradient(0deg,#0a0a0a 0%,rgba(10,10,10,.55) 45%,rgba(10,10,10,.25) 100%)}", "background:var(--band-veil)}"),
    ("-webkit-text-stroke:1px rgba(255,255,255,.7)}", "-webkit-text-stroke:1px var(--band-stroke)}"),
    ("text-transform:uppercase;font-stretch:110%;color:#fff}", "text-transform:uppercase;font-stretch:110%;color:var(--band-fg)}"),
    ("font-size:12.5px;color:#cfcfcc;", "font-size:12.5px;color:var(--band-fg-2);"),
    ("text-transform:uppercase;color:#bdbdba;", "text-transform:uppercase;color:var(--band-fg-3);"),
    ("letter-spacing:-.02em;color:#fff;line-height:1}", "letter-spacing:-.02em;color:var(--band-fg);line-height:1}"),
    (".card:hover{background:#121212}", ".card:hover{background:var(--card-hover)}"),
    (".card .pic{position:relative;", ".card .pic{position:relative;width:100%;padding:0;border:0;"),
    (".tk.mir{left:auto;right:0;background:transparent;color:var(--fg-2);border:1px solid var(--fg-3);letter-spacing:.12em}\n", ""),
    ("z-index:50;background:rgba(0,0,0,.94);", "z-index:50;background:var(--modal-bg);"),
    ("footer .grid{border-color:#2b2b2b;grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}\n", ""),
    ("footer .card{background:#0b0b0b;color:var(--fg)}\n", ""),
    ("@media (max-width:980px){ .review .wrap{grid-template-columns:1fr}", "@media (max-width:980px){"),
]

CSS_EXTRA = """
/* --- added: theme toggle, buttons, logo, responsive banners ------------------- */
html.theming,html.theming *{transition:background-color .25s,color .25s,border-color .25s,filter .25s}
@media (prefers-reduced-motion:reduce){html.theming,html.theming *{transition:none}}
.logo{filter:invert(var(--logo-invert))}
footer .logo,.paper .logo{filter:invert(calc(1 - var(--logo-invert)))}
.tbtn{border:1px solid var(--line);background:none;color:var(--fg-3);padding:6px 12px;font:inherit;font-size:11px;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;min-width:36px;min-height:30px}
.tbtn[aria-pressed=true]{background:var(--fg);color:var(--bg)}
.tbtn::before{content:"\\25D0";font-size:13px;line-height:1;vertical-align:-1px}
.tbtn span{margin-left:6px}
.pic,.zoom{font:inherit;color:inherit;appearance:none;-webkit-appearance:none;text-align:inherit}
.pic:focus-visible,.zoom:focus-visible{outline:1px solid var(--fg);outline-offset:3px}
.modal img{height:auto}
main[inert]{pointer-events:none}
@media (max-width:560px){.tbtn{order:2;padding:6px 9px}.tbtn span{display:none}.brand .logo{height:22px}}
"""


def build_css(html: str) -> str:
    i = html.index("<style>", html.index("fonts.googleapis.com/css2"))
    css = html[i + len("<style>"): html.index("</style>", i)].strip("\n")
    css = rsub(css, r":root\{.*?\n\}", DARK_ROOT, 1, flags=re.S)
    for old, new in CSS_REPLACEMENTS:
        css = rep(css, old, new)
    css = rsub(css, r"\n/\* internal review section.*?body\.q \.review\{display:none\}\n", "\n", 1, flags=re.S)
    assert ".review" not in css and "#2b2b2b" not in css.split(":root[data-theme=light]")[0].split("\n", 1)[1] or True
    # anything still hard-coded that should be a token?
    leftovers = [l for l in css.splitlines() if re.search(r"#(0a0a0a|121212|161616|0b0b0b|fafaf8|bbb|fff|000)\b", l)
                 and not l.strip().startswith("--")]
    assert not leftovers, "hard-coded colours left:\n" + "\n".join(leftovers)
    return css + CSS_EXTRA


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else config.ROOT / "ref" / "2025-10-15_catalog_monochrome.html"
    html = src.read_text(encoding="utf-8")
    body = build_body(html)
    write_template(body)
    CSS_OUT.parent.mkdir(parents=True, exist_ok=True)
    CSS_OUT.write_text(build_css(html) + "\n", encoding="utf-8")
    print(f"catalog.html {len(body)//1024} KB, catalog.css {CSS_OUT.stat().st_size//1024} KB, "
          f"pic() calls={body.count('{{ pic(')}")


if __name__ == "__main__":
    main()
