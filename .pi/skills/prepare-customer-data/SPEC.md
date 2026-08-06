# spec.md — 고객 분석용 데이터셋 준비

## 목표
원본 엑셀(주문·회원)을 익명화된 표준 CSV로 변환·검증해, 이후 스킬들이 참조할
하나의 병합 데이터셋(`merged_data.csv`)을 만든다.

## 맥락
대상: `itnew-analysis-agent`(오케스트레이터), 이후 스킬(`calculate-customer-metrics` 등)
사용 목적: 뒤 단계 스킬들이 신뢰할 수 있는 단일 데이터셋을 참조하도록 함

## 범위
포함: 엑셀→CSV 변환(고객명 가명처리), GPS 좌표화(선택), 필수컬럼·중복·결측
검증, 유효 주문 필터링, members·orders·deliveries 조인
제외: 고객 지표 계산, 고객군 분류, 품목분류 (다른 스킬 담당)

## 제약
- 원본 엑셀은 `data/raw/` 또는 워크스페이스 루트에 있어야 한다
- 고객명은 SHA256 해시로 가명처리하며 원본 텍스트를 어떤 산출물에도 남기지 않는다
- 중복 `order_id` 발견 시 조용히 넘어가지 않고 즉시 실패한다
- GPS 좌표화는 `KAKAO_REST_API_KEY`가 없으면 생략한다(실패로 취급하지 않음)

## 출력 형식
파일명: `data/input/members.csv`, `orders.csv`, `deliveries.csv`,
`data/output/validation_results.csv`, `invalid_records.csv`, `valid_orders_raw.csv`,
`merged_data.csv`
인코딩: UTF-8-SIG

## 성공 기준
- [ ] `members.csv`/`orders.csv`/`deliveries.csv`가 생성됨
- [ ] `validation_results.csv`의 필수컬럼·중복 검증 항목이 모두 "통과"
- [ ] `merged_data.csv` 행수가 0보다 큼
- [ ] 중복 `order_id`가 없음(있으면 실패로 중단되어야 함)
