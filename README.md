# Osteo-Fit CMF Catalog

단일 HTML 카탈로그(다크/화이트 통합, OS 테마 추종 + 토글)를 Flask로 서빙하고, 링크 버전과 단일 파일 버전으로 내보내는 프로젝트.

```
catalog/        Flask 패키지 (templates, static/css, static/js, static/img = 빌드 산출물)
assets_src/     빌드 입력: legacy/(구 HTML에서 추출), banners.json, overrides.json, required_keys.txt
tools/          build_assets.py, make_template.py, freeze.py, inline.py, release.py, extract_legacy.py
tests/          pytest
ref/            2025-10-15 구 카탈로그 2종 (보관)
dist/           내보내기 결과 (git 제외)
```

원본 제품 사진은 `C:\workspace\company_db\Product_img\final_product_img` (읽기 전용). 빌드는 이를 읽어 `catalog/static/img/products/`에 400/800/full webp를 만든다.

## 실행

```powershell
python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
$env:PYTHONUTF8=1

python tools/build_assets.py            # 이미지 파생 + manifest.json (증분)
flask --app catalog run --debug         # http://127.0.0.1:5000/
pytest
python tools/freeze.py                  # dist/index.html + dist/static/  (file:// 가능)
python tools/inline.py                  # dist/Osteo-Fit_CMF_Catalog.html (단일 파일)
python tools/release.py [--public]      # build → pytest → freeze → inline
```

`tools/extract_legacy.py`와 `tools/make_template.py`는 구 HTML에서 1회 변환할 때만 필요하다. 마크업을 바꾸려면 `catalog/templates/catalog.html`을 직접 편집한다.

## 이미지 키 해석 순서

1. `assets_src/overrides.json` (명시 매핑)
2. `final_product_img/**/<key>.png`
3. `tools/config.py` MIRROR (좌우 반전 생성)
4. ALIAS (스프레드 이미지와 동일한 키)
5. `assets_src/legacy/products/<key>.webp`
6. → `catalog/static/img/missing.txt`

결과 요약은 `catalog/static/img/build_report.txt`. 히어로/밴드 사진은 `assets_src/banners.json`에서 교체한다(현재 전부 `license: unverified` → `release.py --public` 차단).

## 데이터

Phase 1(현재)은 마크업 고정. 품목 마스터 CSV(`Gssem_Solution\DB\16_OsteoFit CMF 품목.csv`, 272종)와 카탈로그(335종) 정합 후 Phase 2에서 CSV 구동으로 전환한다.
