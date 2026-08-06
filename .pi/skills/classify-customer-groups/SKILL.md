---
name: classify-customer-groups
description: 이탈위험 등급을 산정하고, 신규·일반·재이용·이탈위험 고객군을 최종 분류한다.
---

## 목적
`calculate-customer-metrics`의 지표를 바탕으로 이탈위험 등급(정상/주의/위험, 또는 판정
제외·보류)을 매기고, 그 결과와 첫 주문일을 함께 판단해 각 고객을 신규/일반/재이용/이탈위험
중 하나로 최종 분류한다. 두 로직이 서로 강하게 엮여있어 하나의 스킬로 묶는다.

분류 우선순위: 신규(첫 주문이 분석 기준월 내) > 이탈위험(등급 주의·위험) > 재이용(주문
2회 이상) > 일반.

**참고**: Next.js 대시보드는 이 스킬이 만든 `customer_groups.csv`의 "고객군" 값을 그대로
쓰지 않는다 — 조회기간에 맞춰 웹 API(`web/src/app/api/customers/route.ts`)에서 동일한
분류 로직을 실시간으로 재계산한다(신규 판정 기준이 "이 스킬 실행 시점의 최신 달"이 아니라
"사용자가 지금 보고 있는 기간"이어야 하기 때문). 이 CSV의 다른 컬럼(등급·평균주기 등)과
`analyze-customer-patterns`의 배치 집계용으로는 여전히 사용된다.

## 사용 시점
`calculate-customer-metrics` 완료 후

## 실행 방법
```bash
python3 -m services.customer.churn
python3 -m services.customer.classify
```

## 출력
- `data/output/churn_scores.csv`
- `data/output/customer_groups.csv`
- `data/output/churn_risk_customers.csv`

## 자체 검증
`churn.py`: 결과 행 수가 `customer_metrics.csv`와 다르거나 이탈 위험 등급에 알 수 없는
값이 있으면 즉시 실패. `classify.py`: 결과가 비어있거나, 한 고객이 중복으로 들어갔거나,
고객군에 알 수 없는 값(신규/일반/재이용/이탈위험 4개 외)이 있으면 즉시 실패.

## SPEC

### 목표
이탈위험 등급을 산정하고, 그 결과와 첫 주문일을 근거로 각 고객을
신규/일반/재이용/이탈위험 중 하나로 최종 분류한다.

### 맥락
대상: `analyze-customer-patterns`(패턴 분석 입력), 대시보드(단, "고객군" 값 자체는
조회기간 기준으로 웹에서 실시간 재계산되며 이 산출물의 값을 그대로 쓰지 않음)
사용 목적: 고객군별 운영 인사이트(이탈 선제 관리, 재이용 고객 관리) 제공

### 범위
포함: 이탈위험 등급 산정(정상/주의/위험/판정제외/판정보류), 고객군 분류
(신규/일반/재이용/이탈위험)
제외: 지역·업종·품목 패턴 분석 (`analyze-customer-patterns` 담당)

### 제약
- 분류 우선순위는 고정: 신규 > 이탈위험 > 재이용 > 일반
- 신규 판정 기준: 첫 주문이 "이 스킬 실행 시점의 최신 분석월" 내 (배치 시점 고정 기준)
- LLM 판단을 쓰지 않는다 — 규칙 기반 결정론적 계산만 수행

### 출력 형식
파일명: `data/output/churn_scores.csv`, `customer_groups.csv`, `churn_risk_customers.csv`

### 성공 기준
- [ ] `customer_groups.csv`가 비어있지 않음
- [ ] 한 고객이 두 고객군에 중복으로 들어가지 않음
- [ ] "고객군" 값이 신규/일반/재이용/이탈위험 4개 중 하나
- [ ] "이탈 위험 등급"이 정상/주의/위험/판정제외/판정보류 중 하나
