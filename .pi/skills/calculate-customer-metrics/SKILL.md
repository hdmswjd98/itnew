---
name: calculate-customer-metrics
description: 병합 데이터셋으로 고객별 평균 주문주기·최종 주문 후 경과일 등 이용 지표를 계산한다.
---

## 목적
`prepare-customer-data`가 만든 병합 데이터셋을 고객 단위로 집계해, 이후 이탈위험 판정과
고객군 분류에 필요한 순수 지표(최근 주문일, 전체 주문 횟수, 평균 이용 주기, 최종 주문 후
경과일, 누적 배송 수량)를 계산한다.

## 사용 시점
`prepare-customer-data` 완료 후 (`merged_data.csv` 필요)

## 실행 방법
```bash
python3 -m services.customer.metrics
```

## 출력
- `data/output/customer_metrics.csv`

## 자체 검증
결과 행 수가 `merged_data.csv`의 고유 고객 수와 다르거나 `customer_id`가 중복되면
그 자리에서 즉시 실패한다 (전체 파이프라인 끝까지 기다리지 않음).

## SPEC

### 목표
병합 데이터셋으로 고객별 이용 지표(최근 주문일·전체 주문 횟수·평균 이용
주기·최종 주문 후 경과일·누적 배송 수량)를 계산한다.

### 맥락
대상: `classify-customer-groups`(이탈위험 판정 입력), 대시보드 고객 상세 테이블
사용 목적: 이탈위험 판정과 고객군 분류에 필요한 순수 지표 확보

### 범위
포함: 고객 단위 집계(최근주문일, 전체주문횟수, 평균이용주기, 경과일, 누적수량, 회원여부)
제외: 이탈위험 등급 판정, 고객군 최종 분류 (`classify-customer-groups` 담당)

### 제약
- 평균 이용 주기는 주문 3회 이상부터 계산한다(1~2회는 "계산 불가"로 명시, 추측하지 않음)
- 선행 조건: `merged_data.csv`가 존재해야 한다

### 출력 형식
파일명: `data/output/customer_metrics.csv`
컬럼: `customer_id`, 최근 주문일, 주문 횟수, 평균 이용 주기, 최종 주문 후 경과일,
누적 배송 수량, 회원 여부

### 성공 기준
- [ ] `customer_metrics.csv` 행수 = `merged_data.csv`의 고유 고객 수
- [ ] `customer_id` 중복 없음
- [ ] 필수 컬럼이 전부 존재
