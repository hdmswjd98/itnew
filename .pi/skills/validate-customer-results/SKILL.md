---
name: validate-customer-results
description: 파이프라인 전체 산출물의 정합성을 최종 확인한다 (합계·중복·결측·원본 대비 일치).
---

## 목적
1~4번 스킬(prepare-customer-data, calculate-customer-metrics, classify-customer-groups,
analyze-customer-patterns)의 산출물을 모두 모아, 계산 과정에서 눈에 안 띄는 버그(중복 분류,
합계 불일치, 원본 대비 유실 등)가 없는지 마지막으로 재확인하는 안전장치다.

검증 항목: 고객별 지표 누락, 신규·재이용 분류 충돌, 이탈위험 판단 근거·필수 컬럼, 주문
횟수별 이탈 분석 기준 일치, 고객군별 인원 합계, 지역/업종/품목 수치 합계, 중복 order_id
처리, 비회원 고객 표시 등.

**참고**: 이 스킬의 결과(`validation_final.csv`)는 Next.js 대시보드가 읽지 않는다 —
콘솔에 ✅/❌로 출력되는 개발자용 QA 체크리스트다. 실패 항목이 있으면 해당 단계부터
재실행한다.

## 사용 시점
`analyze-customer-patterns` 완료 후, 파이프라인의 마지막 검증 단계

## 실행 방법
```bash
python3 -m services.customer.run_validation
```

## 출력
- `data/output/validation_final.csv`
- 콘솔에 항목별 통과/실패 및 원인 출력
