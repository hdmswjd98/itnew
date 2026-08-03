---
name: data-merger
description: 고객 ID를 기준으로 회원·주문 데이터를, 주문 ID를 기준으로 주문·배송 데이터를 연결하고 분석용 통합 데이터셋을 생성한다.
---

## 목적
검증된 데이터를 customer_id 와 order_id 로 조인하여 analysis-ready 통합 테이블을 만든다.

## 사용 시점
data-loader 로 파일 로드 후, metrics-calculator 실행 전

## 실행 방법
```bash
python .pi/skills/data-merger/scripts/merge_data.py
```

## 연결 규칙
- 회원 ↔ 주문: customer_id 기준 left join (주문 데이터에 회원이 없어도 주문 데이터는 유지)
- 주문 ↔ 배송: order_id 기준 left join
- 중복 order_id: 첫 번째 행만 유지
- member 에 없는 customer_id: region/industry 를 "미상"으로 채움

## 출력
- merged_data.csv (통합 데이터셋)
