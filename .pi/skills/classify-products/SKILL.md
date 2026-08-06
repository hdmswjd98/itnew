---
name: classify-products
description: 주문 품목명을 대분류·중분류로 규칙 기반 자동분류한다 (LLM 미사용).
---

## 목적
`data/input/orders.csv`의 `item_name`을 대분류/중분류로 분류한다. 확인 결과 이 로직은
**100% 규칙 기반**이다 — LLM 호출은 코드 어디에도 없다. 분류 우선순위:

1. 정규화 (`normalizer.py`) — 유니코드 NFC, 공백 정리, 소문자화
2. 기업 우선 규칙 (`rules.py`) — `config/product_classification_rules.csv`에서 활성화된
   규칙을 우선순위 순으로 매칭 (Next.js 검토 화면에서 사용자가 수기 지정하면 이 CSV에 저장됨)
3. 도메인 정규식 규칙 (`classifier.py`의 `DOMAIN_RULES`)
4. 키워드 사전 매칭 (`CATEGORY_RULES`, 100여 개)
5. 확장 키워드 매칭 (마지막 fallback)
6. 매칭 안 되면 "기타"

## 사용 시점
`prepare-customer-data` 완료 후 (`orders.csv` 필요), 고객분석 파이프라인과 독립적으로
언제든 실행 가능

## 실행 방법
```bash
python3 -m services.product.classifier
```
Next.js에서는 `/api/products/actions`의 `refresh`(재분류) · `save_rules`(사용자 수기
분류를 규칙 CSV에 저장 후 재분류) 액션이 이 스크립트를 그대로 호출한다.

## 출력
- `data/output/product_classification.csv` (주문별 분류 결과)
- `data/output/category_summary.csv`

## 자체 검증
분류 결과 행 수가 `orders.csv`와 다르거나(누락된 주문 있음), 대분류·중분류가 비어있는
행이 있으면 즉시 실패한다.
