---
name: analyze-customer-patterns
description: 고객군별 지역·업종(회원유형)·품목 분포와 AI 요약문을 생성한다.
---

## 목적
`classify-customer-groups`가 붙인 고객군 라벨을 기준으로 지역별·업종별·품목별 분포를
집계하고, 계산 결과만을 근거로 한 자연어 요약문을 만든다.

**참고**: 이 스킬의 지역·업종 집계 산출물(`region_analysis.csv`, `industry_analysis.csv`)은
"이 스킬을 마지막으로 실행한 시점의 최신 달" 기준 고객군으로 계산돼 있어, 웹 대시보드가
조회기간을 바꿔서 보는 실시간 분류와는 다를 수 있다. Next.js 쪽에서는 이 두 CSV를 읽지
않고 같은 값을 자체적으로 재계산한다(`web/src/app/api/customers/route.ts`). 이 스킬은
품목별 분포(`product_analysis.csv`)와 AI 요약문(`ai_summary.txt`) 생성 용도로 유지한다.

## 사용 시점
`classify-customer-groups` 완료 후

## 실행 방법
```bash
python3 -m services.customer.analyze_patterns
```

## 출력
- `data/output/group_counts.csv`, `region_analysis.csv`, `industry_analysis.csv`, `product_analysis.csv`
- `data/output/ai_summary.txt`

## 자체 검증
지역별·업종별 인원 합계가 분석 대상 전체 고객수와 다르면 즉시 실패한다.

## SPEC

### 목표
고객군 라벨을 기준으로 지역별·업종별·품목별 분포를 집계하고, 계산 결과만을
근거로 한 자연어 요약문을 생성한다.

### 맥락
대상: `validate-customer-results`(통합검증 입력), 참고용 배치 리포트
사용 목적: 고객군별 특성(어느 지역/업종/품목이 많은지) 파악

### 범위
포함: 지역별/업종별/품목별 분포 집계, `ai_summary.txt` 자연어 요약문 생성
제외: 조회기간에 따른 실시간 재계산 (대시보드는 이 스킬의 지역·업종 CSV를
읽지 않고 자체적으로 다시 계산함 — 이 산출물은 배치 시점 기준 참고용)

### 제약
- 요약문은 계산된 숫자만 근거로 작성하며, 데이터에 없는 원인·추측을 만들지 않는다
- 지역별·업종별 인원 합계는 반드시 전체 분석 대상 고객 수와 일치해야 한다

### 출력 형식
파일명: `data/output/group_counts.csv`, `region_analysis.csv`, `industry_analysis.csv`,
`product_analysis.csv`, `ai_summary.txt`

### 성공 기준
- [ ] 지역별 분포 인원 합계 = 분석 대상 고객 수
- [ ] 업종별 분포 인원 합계 = 분석 대상 고객 수
- [ ] `ai_summary.txt`가 비어있지 않음
