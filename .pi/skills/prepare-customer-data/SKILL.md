---
name: prepare-customer-data
description: 원본 엑셀(또는 이미 존재하는 input CSV)을 검증된 병합 데이터셋으로 변환한다.
---

## 목적
분석 파이프라인의 첫 단계로, 원본 엑셀을 익명화된 표준 CSV(members/orders/deliveries)로
변환하고, 필수 컬럼·중복·결측을 검증한 뒤, 유효한 주문만 남겨 하나의 병합 데이터셋으로
합친다. "분석 가능한 데이터셋 준비"라는 하나의 목적 아래 4개 스크립트를 순서대로 실행한다.

## 사용 시점
파이프라인 시작 시, 또는 원본 엑셀이 갱신됐을 때

## 실행 방법
```bash
python3 -m services.customer.import_real_data   # 엑셀 → members/orders/deliveries.csv 변환 (익명화 포함)
python3 -m services.customer.geocode             # 배송지 GPS 좌표화 (선택, KAKAO_REST_API_KEY 없으면 자동 생략)
python3 -m services.customer.validate_and_load   # 필수컬럼·중복·결측 검증 + 유효 주문만 필터링
python3 -m services.customer.merge_data          # members·orders·deliveries 조인
```
원본 엑셀은 `data/raw/`에 넣어야 한다 (`import_real_data.py`의 `find_source_excel()`이
이 폴더에서 `.xlsx` 파일을 찾는다). `data/raw/`는 `.gitignore`에 걸려있어 git에는
올라가지 않으므로, 팀원은 이 파일을 별도 경로로 받아 로컬의 `data/raw/`에 직접 넣어야 한다.

## 출력
- `data/input/members.csv`, `orders.csv`, `deliveries.csv` (익명화된 표준 CSV)
- `data/output/validation_results.csv`, `invalid_records.csv` (검증 결과)
- `data/output/valid_orders_raw.csv` (유효 주문만 남긴 데이터)
- `data/output/merged_data.csv` (다음 스킬들이 사용하는 병합 데이터셋)
