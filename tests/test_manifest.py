from tools import config


def test_required_keys_all_in_manifest(manifest):
    required = set(config.REQUIRED_KEYS.read_text(encoding="utf-8").split())
    missing = required - set(manifest["products"])
    assert not missing, f"keys without a product entry: {sorted(missing)}"


def test_template_keys_resolve(manifest, template_keys):
    pic_keys, data_keys = template_keys
    assert pic_keys == data_keys, "pic() calls and data-img attributes diverged"
    assert pic_keys <= set(manifest["products"])


def test_every_variant_file_exists(manifest):
    for key, e in manifest["products"].items():
        for v in ("t", "m", "f"):
            assert e[v].startswith("img/"), (key, v)
            assert (config.STATIC / e[v]).exists(), (key, v, e[v])
        assert e["w"] > 0 and e["h"] > 0


def test_banners_and_images_present(manifest):
    for name in ["hero"] + [f"band_{f}" for f in config.BAND_FAMILIES]:
        e = manifest["banners"][name]
        for v in ("xl", "lg", "md"):
            assert (config.STATIC / e[v]).exists(), (name, v)
    for name in [f"spread_{s}" for s in config.SPREADS]:
        e = manifest["images"][name]
        for v in ("lg", "md"):
            assert (config.STATIC / e[v]).exists(), (name, v)
    assert (config.STATIC / manifest["images"]["logo"]["p"]).exists()


def test_missing_report_is_empty():
    if config.MISSING.exists():
        assert config.MISSING.read_text(encoding="utf-8").strip() == ""


def test_legacy_fallbacks_do_not_grow(manifest):
    legacy = [k for k, e in manifest["products"].items() if e.get("origin") in ("legacy", "alias")]
    # 160-OR-090/100/145, dim_gs1..4, new_case, new_visidisk (+ anything new is a regression)
    assert len(legacy) <= 10, sorted(legacy)
