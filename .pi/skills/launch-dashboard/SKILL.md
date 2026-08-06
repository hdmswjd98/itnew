---
name: launch-dashboard
description: Next.js 웹 대시보드를 설치·기동하고, 브라우저 접근이 안 되는 환경에서는 정적 HTML 요약을 생성한다.
---

## 목적
분석 산출물(`data/output/*.csv`)이 준비된 뒤, 실제 사용자가 보는 Next.js 대시보드를
띄운다. 대시보드는 고객분석·운영현황·월간리포트·품목 자동분류 4개 화면을 제공하며,
CSV를 직접 읽거나(고객분석·품목분석) 파이썬을 그때그때 호출하는 방식(월간리포트)으로
동작한다.

브라우저로 접근할 수 없는 실행 환경(예: 타임리 샌드박스)이거나 사용자가 명시적으로
"HTML로 만들어줘"라고 요청하면, Next.js 서버는 그대로 로컬에 띄운 채 그 API를 호출해
정적 HTML 요약을 대신 생성한다. **이때도 계산은 전부 이미 검증된 Next.js API가
하고, HTML 생성 스크립트는 그 결과를 옮기기만 한다** — 즉흥적으로 채팅에서 파이썬을
새로 짜지 않고 이 스킬이 가리키는 스크립트만 쓴다. HTML 요약본은 실제 대시보드와
동일하게 **운영현황·고객분석·품목분류 3개 탭**(CSS 라디오버튼 방식, 외부 JS 의존
없음)으로 구성된다.

## 사용 시점
`prepare-customer-data`, `classify-customer-groups`, `classify-products` 등 필요한
분석 스킬이 최소 1회 이상 완료된 뒤 (대시보드가 참조하는 CSV가 있어야 함)

## 실행 방법
```bash
cd web
npm install   # node_modules 없을 때만
npm run dev   # 개발 모드 (또는 npm run build && npm run start)
```

브라우저 접근이 안 되거나 HTML 요청 시:
```bash
python3 -m services.report.dashboard_artifact                                  # 전체 기간
python3 -m services.report.dashboard_artifact --from 2026-06-01 --to 2026-06-07  # 특정 기간
```
Next.js 서버가 로컬(`http://localhost:3000`)에 떠 있어야 한다. 결과는 리포지토리
루트의 `dashboard_artifact.html`로 저장된다(`.gitignore` 대상).

## 출력
- 실행 중인 대시보드 URL (기본 `http://localhost:3000`), 또는
- `dashboard_artifact.html` (정적 HTML 요약)
