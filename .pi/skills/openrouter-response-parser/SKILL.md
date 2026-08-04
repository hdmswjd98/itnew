---
name: openrouter-response-parser
description: OpenRouter API 응답을 지정된 JSON 구조로 변환하여 이후 검증·계산 단계로 전달한다.
---

## 목적 및 범위
- OpenRouter에서 받은 원문 응답을 시스템이 기대하는 내부 JSON 스키마로 정규화·변환한다.
- **포함**: JSON 파싱, 키 매핑, 누락 필드 채움, 비JSON 응답 구조화, 응답 타입 분류
- **제외**: 유효성 검사, 신뢰도 계산, 분류 승인

## 작업 절차
1. `openrouter-item-classifier`의 원문 응답 배열을 입력받는다.
2. 각 응답에 대해 JSON 타입이 아닌 경우, 정규 표현식으로 후보 필드를 추출한다.
3. 기대되는 키(standard_item, category, reason, confidence_raw)를 기준으로 매핑한다.
4. 누락된 필드는 기본값(빈 문자열, null, 0)으로 채운다.
5. 파싱 결과가 모호한 경우 “파싱 경고” 플래그를 설정한다.
6. 파싱 완료 응답을 표준 JSON 배열로 직렬화한다.
7. 파싱 결과와 함께 경고 목록을 반환한다.

## 사용 규칙 및 제약 사항
- 파싱은 원문 응답의 의미를 변경하지 않는 선에서 수행한다.
- 숫자형 confidence 값은 0~1 범위 또는 0~100 범위를 모두 수용하되, 내부 기준은 0~1로 통일한다.
- 필수 키가 모두 누락된 응답은 “무효 응답”으로 표시하고, 이후 `standard-item-validator`에서 반려한다.
- 파싱 과정에서 원본 응답 텍스트는 삭제하지 않고 `raw_response` 필드에 보존한다.
- 프롬프트 간섭으로 인한 추가 텍스트(주석, 설명문)는 파싱 시 제거한다.
- JSON 구조가 변경된 경우 스키마 버전과 함께 기록해 호환성을 추적한다.

## 템플릿
입력:
- `raw_responses`: {row_id, raw_name, api_response_text}[]
- `expected_schema`: {standard_item, category, reason, confidence_raw}

출력:
- `parsed_responses`: {row_id, raw_name, standard_item, category, reason, confidence_raw, parse_warning}[]
- `invalid_responses`: 파싱 실패 응답 목록
- `parse_summary`: {total, parsed, failed, warnings}

실행 예시:
1. 원문: “추천 품목: 코카콜라 355ml, 카테고리: 음료”
2. 정규식 파싱 → {standard_item: "코카콜라 355ml", category: "음료"}
3. 누락 필드 채움(reason: "", confidence_raw: null)
4. 파싱 결과 반환
