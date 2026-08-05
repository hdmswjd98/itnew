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
