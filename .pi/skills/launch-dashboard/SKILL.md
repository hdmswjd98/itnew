---
name: launch-dashboard
description: Next.js 웹 대시보드를 설치·기동하고 접속 주소를 반환한다.
---

## 목적
분석 산출물(`data/output/*.csv`)이 준비된 뒤, 실제 사용자가 보는 Next.js 대시보드를
띄운다. 대시보드는 고객분석·운영현황·월간리포트·품목 자동분류 4개 화면을 제공하며,
CSV를 직접 읽거나(고객분석·품목분석) 파이썬을 그때그때 호출하는 방식(월간리포트)으로
동작한다.

## 사용 시점
`prepare-customer-data`, `classify-customer-groups`, `classify-products` 등 필요한
분석 스킬이 최소 1회 이상 완료된 뒤 (대시보드가 참조하는 CSV가 있어야 함)

## 실행 방법
```bash
cd web
npm install   # node_modules 없을 때만
npm run dev   # 개발 모드 (또는 npm run build && npm run start)
```

## 출력
- 실행 중인 대시보드 URL (기본 `http://localhost:3000`)
