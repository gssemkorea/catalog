import json
import re
from pathlib import Path

import pytest

from catalog import create_app
from tools import config

TEMPLATE = (config.ROOT / "catalog" / "templates" / "catalog.html").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def app():
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def manifest():
    if not config.MANIFEST.exists():
        pytest.skip("manifest.json not built yet (run tools/build_assets.py)")
    return json.loads(config.MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def template_keys():
    """Every product key the template asks pic() for, plus every data-img on a card/zoom."""
    pic_keys = set(re.findall(r"\{\{ pic\('([^']+)'", TEMPLATE))
    data_keys = {k for k in re.findall(r'data-img="([^"]*)"', TEMPLATE) if k}
    return pic_keys, data_keys
