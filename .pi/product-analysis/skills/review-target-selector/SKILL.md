---
name: review-target-selector
description: [품목분석] 신뢰도 부족, 불일치, 검증 실패 품목을 검토하여 사용자 확인이 필요한 목록으로 선별한다.
---
# 품목분석 영역
# 실제 실행 코드: services/product/



## 목적 및 범위
- 자동 분류가 끝나도 신뢰도 부족, 일관성 불일치, 검증 실패 등으로 인해 사용자 확인이 필요한 품목을 하나의 검토 대상 목록으로 통합한다.
- **포함**: 검토 대상 통합, 우선순위 정렬, 검토 사유 태깅, 사용자 리뷰 데이터 구조 생성
- **제외**: 실제 사용자 승인/수정 처리, 분류 사전 갱신

## 작업 절차
1. `classification-consistency-checker`, `standard-item-validator`, `category-validator`, `classification-confidence-calculator`의 결과를 입력받는다.
2. 다음 조건에 해당하는 품목을 검토 대상으로 선별한다.
   - 신뢰도 < 임계치
   - 일관성 불일치
   - 표준 품목 검증 실패
   - 카테고리 검증 실패
   - API 분류 실패
3. 각 검토 대상 품목에 대해 주요 사유(1순위, 2순위)를 태깅한다.
4. 검토 우선순위는 신뢰도 낮은 순 → 불일치 건 → 검증 실패 순으로 정렬한다.
5. 사용자 검토용 데이터 구조(원본, 정규화, AI 추천, 근거, 신뢰도, 사유)를 생성한다.
6. 검토 대상 목록과 요약 메트릭을 반환한다.

## 사용 규칙 및 제약 사항
- 자동 승인 조건을 충족한 품목은 검토 대상에서 제외한다.
- 검토 대상은 원본 품목명, 정규화 품목명, AI 추천, 근거를 반드시 포함해야 한다.
- 동일 품목이 여러 사유로 검토 대상이 된 경우, 가장 심각한 사유 1개를 우선 표시한다.
- 검토 목록은 사용자가 일괄 승인/수정할 수 있도록 행 단위 편집 가능한 형태로 구성한다.
- 검토 대상 건수 임계치를 초과하면 배치 분할 뷰를 제공한다.
- 검토 목록에 포함되지 않은 품목은 자동 승인 가능 상태로 간주한다.

## 템플릿
입력:
- `classified_responses`: 분류 완료 결과 데이터셋
- `confidence_threshold`: 자동 승인 임계치
- `max_review_batch`: 검토 대상 최대 배치 크기

출력:
- `review_targets`: {row_id, raw_name, normalized_name, recommended_item, category, confidence_score, reason, priority}[]
- `review_summary`: {total, low_confidence, inconsistent, validation_failed, api_failed}
- `auto_approved_count`: 자동 승인 건수

실행 예시:
1. 신뢰도 부족 12건 + 불일치 5건 + 검증 실패 3건
2. 우선순위 정렬
3. 검토 대상 20건 목록 생성
4. 자동 승인 180건 분리
