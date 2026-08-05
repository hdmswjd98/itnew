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
