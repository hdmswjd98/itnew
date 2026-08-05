---
name: metrics-calculator
description: [고객분석] 고객별 최근 주문일, 주문 횟수, 평균 이용 주기, 최종 주문 후 경과일, 누적 이용 금액을 계산한다.
---
# 고객분석 영역
# 실제 실행 코드: services/customer/



## 목적
통합된 주문 데이터에서 고객별 5대 이용 지표를 산출한다.

## 사용 시점
data-merger 로 통합 데이터셋 생성 후

## 계산 항목
| 지표 | 계산 방법 |
| --- | --- |
| 최근 주문일 | 고객별 max(order_date) |
| 주문 횟수 | 고객별 count(distinct order_id) |
| 평균 이용 주기 | 정렬된 주문일 간격의 평균 (3건 미만이면 "계산 불가") |
| 최종 주문 후 경과일 | 기준일 - 최근 주문일 (음수면 0) |
| 누적 이용 금액 | 고객별 sum(order_amount) |

## 실행 방법
```bash
python .pi/skills/metrics-calculator/scripts/calc_metrics.py
```

## 출력
- customer_metrics.csv

## 제약
- 1~2회 주문 고객의 평균 이용 주기는 "계산 불가"
- 평균 이용 주기는 주문 간격이 2개 이상 확보되는 전체 주문 3회부터 계산
- 모든 금액은 정수 원 단위
- 경과일은 정수
