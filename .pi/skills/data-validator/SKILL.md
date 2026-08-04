---
name: data-validator
description: 회원·주문·배송 CSV 데이터의 필수 컬럼, 결측값, 중복, 타입 오류를 검증하고 제외 데이터 목록을 생성한다.
---

## 목적
분석 파이프라인의 첫 단계로, members.csv / orders.csv / deliveries.csv / invalid_orders.csv 의 데이터 품질을 검증한다.

## 사용 시점
파이프라인 시작 시, 또는 데이터 소스를 변경했을 때

## 실행 방법
```bash
python .pi/skills/data-validator/scripts/validate.py
```

## 검증 항목
| # | 항목 | 파일 |
| --- | --- | --- |
| 1 | 필수 컬럼 존재 여부 | members.csv, orders.csv, deliveries.csv |
| 2 | customer_id 결측 | orders.csv |
| 3 | order_id 결측 | orders.csv |
| 4 | 중복 order_id | orders.csv |
| 5 | 날짜 형식 오류 | orders.csv |
| 6 | 주문 금액 숫자 변환 | orders.csv |
| 7 | 배송 연결 오류 | deliveries.csv |
| 8 | 비회원 customer_id | orders.csv vs members.csv |

## 처리 규칙
- customer_id 결측 행: 분석에서 제외 후 invalid_records.csv 에 기록
- 중복 order_id: 첫 번째 행만 유효, 나머지는 제외 후 기록
- 날짜/금액 변환 불가 행: 제외 후 기록
- 제외 데이터는 `invalid_records.csv` 로 별도 저장
- 검증 결과는 `validation_results.csv` 로 저장

## 출력
- `validation_results.csv` — 검증 항목별 통과/실패/내용
- `invalid_records.csv` — 제외 데이터 상세 (order_id, customer_id, order_date, item_name, order_amount, 오류 사유)
