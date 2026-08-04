---
name: classification-confidence-calculator
description: AI 응답과 검증 결과를 기반으로 품목 분류 신뢰도(Confidence Score)를 계산한다.
---

## 목적 및 범위
- 표준 품목 및 카테고리 매칭 결과, 유사도, 사전 일치 여부, AI 응답의 completeness 등을 종합하여 분류 신뢰도를 수치화한다.
- **포함**: 신뢰도 점수 산출, 점수 정규화, 임계치 기반 상태 분류, 계산 로그 기록
- **제외**: 분류 승인/거부 판정, 분류 사전 갱신, 통계 생성

## 작업 절차
1. `standard-item-validator`와 `category-validator`를 통과한 응답 데이터셋을 입력받는다.
2. 각 품목에 대해 다음 요소를 가중 합산하여 신뢰도를 계산한다.
   - 사전 일치 여부
   - 표준 품목 유사도 점수
   - 카테고리 유사도 점수
   - AI 응답 completeness(근거 문장 존재 여부 등)
3. 가중치는 설정값으로 관리하되, 기본값은 사전 일치 0.4, 유사도 0.3, completeness 0.3으로 한다.
4. 최종 점수를 0~1 범위로 정규화한다.
5. 신뢰도 임계치와 비교하여 “자동 확정 / 검토 필요”를 구분한다.
6. 계산 결과를 데이터셋에 필드 추가하고, 계산 로그를 반환한다.

## 사용 규칙 및 제약 사항
- 신뢰도 점수는 동일 품목이라도 원본 텍스트가 다르면 별도로 계산한다.
- 사전 완전 일치 품목은 기본적으로 높은 가중치를 부여하되, AI가 다른 값으로 제안하면 신뢰도를 하락시킨다.
- 모델 응답이 불완전하거나 근거 필드가 비어 있으면 completeness 점수를 감점한다.
- 신뢰도 임계치는 관리자가 설정할 수 있으며, 기본값은 0.75다.
- 계산된 신뢰도는 사용자에게 즉시 공개해야 하며, 반올림은 소수점 둘째자리까지 한다.
- 신뢰도 계산 로직 변경 시 버전 번호를 함께 기록하여 재현 가능하게 한다.

## 템플릿
입력:
- `validated_responses`: 검증 통과 응답 데이터셋
- `weights`: {dictionary_match, similarity, completeness}
- `confidence_threshold`: 자동 확정 임계치(기본 0.75)

출력:
- `scored_responses`: {row_id, raw_name, standard_item, category, confidence_score, auto_approve_gap}[]
- `boundary_items`: 임계치 근처 품목 목록
- `confidence_log`: {item, score, factors}[]

실행 예시:
1. 사전 일치 + 유사도 0.95 + completeness 1.0 → confidence 0.92
2. 유사 매칭 + 유사도 0.88 + completeness 0.6 → confidence 0.71 → 검토 필요
3. 결과 데이터셋에 confidence_score 추가
