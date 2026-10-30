import re

from tests.conftest import TEMPLATE


def test_index_renders(client, manifest, template_keys):
    r = client.get("/")
    assert r.status_code == 200
    assert r.mimetype == "text/html" and r.mimetype_params.get("charset", "").lower() == "utf-8"
    html = r.get_data(as_text=True)
    assert 'id="modal"' in html and "window.CAT=" in html
    assert "data:image" not in html, "base64 leaked into the rendered page"
    assert "{{" not in html and "{%" not in html
    # every pic() call produced an <img> (no key fell back to "no photo")
    pic_calls = TEMPLATE.count("{{ pic(")
    imgs = len(re.findall(r'<img class="(?:|hero-pic|dim)" src="/static/img/products/', html))
    assert imgs == pic_calls, (imgs, pic_calls)
    assert html.count('loading="lazy"') >= pic_calls
    # no empty alt on product images
    assert not re.search(r'<img class="(?:|hero-pic|dim)"[^>]*alt=""', html)
    # structure
    assert html.index("<title>") < html.index("</head>")
    assert '<meta charset="utf-8">' in html
    assert 'id="t-dark"' in html and 'aria-label="제품군"' in html


def test_head_order_boot_script_before_css(client):
    html = client.get("/").get_data(as_text=True)
    assert html.index("osteofit.theme") < html.index("catalog.css")


def test_img_redirect(client, manifest):
    r = client.get("/img/120-1004")
    assert r.status_code == 302 and r.headers["Location"].endswith(".webp")
    assert "-800." in r.headers["Location"]
    r = client.get("/img/120-1004?v=f")
    assert "-full." in r.headers["Location"]
    assert client.get("/img/nope").status_code == 404
    assert client.get("/img/120-1004?v=x").status_code == 400


def test_static_manifest_and_health(client, manifest):
    assert client.get("/static/img/manifest.json").status_code == 200
    j = client.get("/healthz").get_json()
    assert j["ok"] and j["products"] == len(manifest["products"])


def test_sample3d_page(client):
    r = client.get("/3d")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "<model-viewer" in html and "/static/models/sample_star_plate.glb" in html
    assert 'id="t-dark"' in html and "{{" not in html
    assert client.get("/static/models/sample_star_plate.glb").status_code == 200
