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
원본 엑셀은 `data/raw/`에 넣으면 된다. 거기에 없으면 워크스페이스 루트에서도 자동으로
찾는다(`find_source_excel()`이 두 위치를 순서대로 확인) — 채팅에 엑셀을 업로드하면
워크스페이스 루트에 자동 배치되는 실행 환경(예: 타임리)에서도 별도 이동 없이 바로
동작한다. 엑셀 파일은 어디에 있든 `.gitignore`(`*.xlsx`)로 git에서 제외되므로, 팀원은
이 파일을 별도 경로로 받아 각자 로컬(또는 각자 채팅)에 직접 넣어야 한다.

## 출력
- `data/input/members.csv`, `orders.csv`, `deliveries.csv` (익명화된 표준 CSV)
- `data/output/validation_results.csv`, `invalid_records.csv` (검증 결과)
- `data/output/valid_orders_raw.csv` (유효 주문만 남긴 데이터)
- `data/output/merged_data.csv` (다음 스킬들이 사용하는 병합 데이터셋)

## 자체 검증
`order_id`는 `import_real_data.py`가 순번으로 생성해 원래 중복이 있을 수 없다.
`orders.csv`에 중복 `order_id`가 있으면(앞단이 잘못됐다는 신호) 검증 리포트를 저장한
뒤 즉시 실패한다 (조용히 첫 건만 남기고 넘어가지 않는다).

## SPEC

### 목표
원본 엑셀(주문·회원)을 익명화된 표준 CSV로 변환·검증해, 이후 스킬들이 참조할
하나의 병합 데이터셋(`merged_data.csv`)을 만든다.

### 맥락
대상: `itnew-analysis-agent`(오케스트레이터), 이후 스킬(`calculate-customer-metrics` 등)
사용 목적: 뒤 단계 스킬들이 신뢰할 수 있는 단일 데이터셋을 참조하도록 함

### 범위
포함: 엑셀→CSV 변환(고객명 가명처리), GPS 좌표화(선택), 필수컬럼·중복·결측
검증, 유효 주문 필터링, members·orders·deliveries 조인
제외: 고객 지표 계산, 고객군 분류, 품목분류 (다른 스킬 담당)

### 제약
- 원본 엑셀은 `data/raw/` 또는 워크스페이스 루트에 있어야 한다
- 고객명은 SHA256 해시로 가명처리하며 원본 텍스트를 어떤 산출물에도 남기지 않는다
- 중복 `order_id` 발견 시 조용히 넘어가지 않고 즉시 실패한다
- GPS 좌표화는 `KAKAO_REST_API_KEY`가 없으면 생략한다(실패로 취급하지 않음)

### 출력 형식
파일명: `data/input/members.csv`, `orders.csv`, `deliveries.csv`,
`data/output/validation_results.csv`, `invalid_records.csv`, `valid_orders_raw.csv`,
`merged_data.csv`
인코딩: UTF-8-SIG

### 성공 기준
- [ ] `members.csv`/`orders.csv`/`deliveries.csv`가 생성됨
- [ ] `validation_results.csv`의 필수컬럼·중복 검증 항목이 모두 "통과"
- [ ] `merged_data.csv` 행수가 0보다 큼
- [ ] 중복 `order_id`가 없음(있으면 실패로 중단되어야 함)
