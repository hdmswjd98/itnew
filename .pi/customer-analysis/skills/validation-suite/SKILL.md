---
name: validation-suite
description: [고객분석] 분석 결과의 지표 누락, 분류 충돌, 이탈 위험 판단 근거, 인원 합계 일치, 원본 데이터 수치 일치를 검증한다.
---
# 고객분석 영역
# 실제 실행 코드: services/customer/



## 목적
파이프라인의 각 단계 출력물이 spec.md 의 성공 기준을 충족하는지 최종 검증한다.

## 검증 항목
| # | 검증 항목 | 확인 방법 |
| --- | --- | --- |
| 1 | 고객별 지표 누락 | customer_metrics.csv 의 customer_id 수 == 분석 대상 고객 수 |
| 2 | 분류 충돌 | customer_groups.csv 에서 동일 customer_id 가 2개 이상 군집에 속하는지 |
| 3 | 이탈 분석 결과 | 필수 컬럼과 모든 고객의 판단 근거가 있는지 |
| 4 | 주문 횟수별 기준 | 1회=판정 제외, 2회=판정 보류, 3회 이상이면서 평균 주기 계산 가능=분석 대상인지 |
| 5 | 분석 대상 합계 | 분석 대상 고객 집합 == 정상·주의·위험 고객 집합인지 |
| 6 | 인원 합계 일치 | customer_groups.csv 의 군별 인원 합 == 분석 대상 고객 수 |
| 7 | 지역 수치 일치 | region_analysis.csv 의 고객 수 합 == 분석 대상 고객 수 |
| 8 | 업종 수치 일치 | industry_analysis.csv 의 고객 수 합 == 분석 대상 고객 수 |
| 9 | 품목 수치 일치 | product_analysis.csv 의 주문 건수 합 == 분석 대상 주문 건수 |
| 10 | 원본 데이터 일치 | 전체 주문 금액 합 == 원본 orders.csv 의 금액 합 (유효 데이터 기준) |
| 11 | 중복 order_id 처리 | valid_orders.csv 에 동일 order_id 가 2회 이상 등장하지 않는지 |
| 12 | 비회원 고객 별도 표시 | members.csv 에 없는 customer_id 가 "비회원"으로 표시됐는지 |

이탈 위험률은 `위험 등급 고객 수 ÷ 이탈 분석 대상 고객 수 × 100`으로 검증하며 전체 고객 수를 분모로 사용하지 않는다.

## 실행 방법
```bash
python .pi/skills/validation-suite/scripts/run_validation.py
```

## 출력
- validation_final.csv (검증 항목별 통과/실패/원인)
- 검증 실패 시 콘솔에 실패 항목 목록 출력

## 제약
- 원본 데이터 수치와 분석 결과 수치가 일치해야 함
- 임의로 데이터를 수정하지 않음
- 모든 결과는 한국어
