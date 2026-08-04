---
name: openrouter-item-classifier
description: 미분류 품목을 OpenRouter API로 전달하여 가장 적합한 표준 품목 후보와 카테고리 후보를 생성한다.
---

## 목적 및 범위
- 분류 사전에 없는 품목에 대해 OpenRouter API를 호출해 표준 품목과 카테고리, 분류 근거를 추천받는다.
- **포함**: API 호출 준비, 프롬프트 구성, 응답 수신, 응답 상태 추적, 호출 실패 재시도
- **제외**: 응답 파싱, 유효성 검사, 신뢰도 계산, 분류 사전 갱신

## 작업 절차
1. `unmapped-item-selector`가 반환한 미분류 품목 목록을 입력받는다.
2. OpenRouter API 설정값(모델, 엔드포인트, API 키, 타임아웃, 재시도 횟수)을 로드한다.
3. 각 품목명에 대해 표준 품목·카테고리 추천을 위한 프롬프트를 구성한다.
4. API로 요청을 전송하고 응답을 대기한다.
5. 응답 성공 시 원문 응답 또는 응답 식별자를 기록한다.
6. 응답 실패/타임아웃 시 재시도 로직에 따라 최대 지정 횟수만큼 재요청한다.
7. 모든 시도 후에도 응답이 없으면 “분류 불가” 상태로 표시한다.
8. API 응답 원문과 함께, 분류 대상 품목 목록을 결과 객체로 반환한다.

## 사용 규칙 및 제약 사항
- API 키는 시스템 환경변수 또는 안전한 설정 파일에서 읽어오며, 로그에 노출하지 않는다.
- 한 번의 배치 호출에 포함되는 품목 수는 API 요청 제한을 초과하지 않도록 분할한다.
- 모델 응답은 항상 JSON 형식을 우선으로 요청하되, 비JSON 응답도 수용 가능한 파싱 단계로 넘긴다.
- 동일 종목에 대해 연속 실패할 경우, 해당 품목은 수동 검토 대상으로 표시한다.
- API 호출 간격은 서버 부하를 고려해 최소 지연을 적용한다.
- 프롬프트 구성에는 품목명, 기존 카테고리 목록, 표준 품목 목록, 분류 기준을 포함한다.

## 템플릿
입력:
- `unmapped_dataset`: 미분류 품목 데이터셋
- `openrouter_config`: {model, base_url, api_key, timeout, retry_count}
- `allowed_standard_items`: 허용 표준 품목 목록
- `allowed_categories`: 허용 카테고리 목록

출력:
- `raw_responses`: {row_id, raw_name, api_response_text, status}[]
- `failed_items`: API 호출 실패 품목 목록
- `response_metadata`: {model_used, latency_ms, request_count}

실행 예시:
1. “코카355캔” → API 프롬프트 전송
2. 응답: {standard_item: "코카콜라 355ml", category: "음료", reason: "..."}
3. 응답 원문 저장
4. 실패 항목 재시도 후 결과 반영
