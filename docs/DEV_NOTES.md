# 개발 노트 (Osteo-Fit CMF 카탈로그)

기준일 2026-10-23. 카탈로그 데이터·이미지에서 아직 해결되지 않은 항목을 기록한다. 해결되면 이 파일과 `tools/config.py`의 해당 표를 같이 갱신한다.

## 1. 사진이 없는 모델 → 유사 모델 사진으로 임시 대체

카드에 "사진 없음" 빈 칸이 남지 않도록 비슷한 모델의 사진을 대신 보여준다. 페이지에는 표시하지 않는다(사용자 결정 2026-10-23). `tools/config.py`의 `SUBSTITUTE` 표가 원천이고, 템플릿의 해당 카드 앞에 Jinja 주석(`{# 160-3003 … #}`)으로 위치를 남겨 두었다. 빌드 리포트 `SUBSTITUTE_PHOTOS` 항목으로 감사할 수 있다.

| 품번 | 품명 | 대체 사진 | 비고 |
|---|---|---|---|
| 160-3003 | Mid Plate Straight 2 Hole large | 160-3002 (2 Hole medium) | 2013판 160-2001/2002 → 2026판 3001/3002/3003. large 실촬영 필요 |
| 160-4050 | Mid Plate Square small | 160-4051 (Square) | small 실촬영 필요 |

실제 사진이 생기면: `final_product_img\Osteo-Mid Plates\<품번>.png`에 넣고 `SUBSTITUTE`에서 해당 줄을 지운 뒤 `tools/build_assets.py` 실행. 템플릿의 Jinja 주석은 `catalog.html`과 `tools/make_template.py`의 `CONTENT_FIXES`에서 함께 지운다.

## 2. 구 HTML에서 추출한 사진만 있는 품번 (legacy, 장변 ≤800px)

`160-OR-090 / 160-OR-100 / 160-OR-145`(Right 앵커 플레이트 실촬영본), `dim_gs1~4`(치수도, 흰 배경·알파 없음 → 다크 모드에서 흰 사각형), `new_case`, `new_visidisk`. 1254px 원본 PNG 확보 시 `final_product_img` 해당 폴더에 넣으면 빌드가 자동으로 우선 사용한다.

## 3. 좌우 반전으로 생성한 사진

`160-0000` ← `160-1000` 좌우 반전(구 HTML과 동일). 레이저 마킹 글자가 뒤집히므로 실촬영본으로 교체 권장.

## 4. 배너 사진 라이선스

`assets_src/banners.json`의 사진은 전부 `license: unverified`(AdobeStock, iStock 등 스톡). 외부 공개 전 확인. `tools/release.py --public`은 미확인 상태에서 중단된다. band_mini(2560px)·band_maxi(3500px)는 4K에서 1.5배 이하 확대된다.

## 5. 품번 수 불일치

카탈로그 HTML 335종 vs 품목 마스터 CSV(`Gssem_Solution\DB\16_OsteoFit CMF 품목.csv`) 272종. CSV 구동 렌더링(Phase 2) 전에 정합 필요.

## 6. 카탈로그 원문 오탈자 (그대로 둠)

Complation→Completion, Calvanium→Calvarium, Retactor→Retractor, Organizer Bloc→Block. 제품 담당 확인 후 일괄 수정.
