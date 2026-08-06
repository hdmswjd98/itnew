# spec.md — Next.js 대시보드 빌드·실행 (또는 정적 HTML 요약)

## 목표
분석 산출물(`data/output/*.csv`)을 기반으로 Next.js 대시보드를 설치·빌드·실행하고,
브라우저로 접근할 수 없는 환경이거나 사용자가 명시적으로 요청하면 같은 데이터를
정적 HTML 요약으로도 제공한다.

## 맥락
대상: 최종 사용자(운영 담당자), 데모 시연
사용 목적: 분석 결과를 시각적으로 확인 — 실행 환경이 브라우저 접근을 지원하지
않아도(예: 타임리 샌드박스) 결과를 확인할 수 있어야 함

## 범위
포함: `npm install`(필요시)·`build`·`start`(또는 `dev`) 실행, 헬스체크,
`services.report.dashboard_artifact`로 정적 HTML 요약 생성
제외: 데이터 재계산(Next.js API가 담당 — HTML 요약본도 API 결과를 그대로 옮길 뿐
자체적으로 다시 계산하지 않음), 실제 브라우저 외부 노출 보장

## 제약
- 분석 스킬이 최소 1개 이상 완료돼 있어야 한다(참조할 CSV가 있어야 함)
- 외부 접근이 제한된 실행 환경(샌드박스 등)에서는 브라우저 접속 대신
  로컬 `curl`/HTML 요약으로 성공 여부를 판단한다
- HTML 요약본을 만들 때도 Next.js 서버(`/api/customers`, `/api/products`)를 호출해서
  나온 값을 그대로 쓴다 — 조회기간 계산 로직을 파이썬으로 다시 구현하지 않는다
- 채팅에서 즉흥적으로 새 스크립트를 짜지 않고, `services/report/dashboard_artifact.py`만 쓴다

## 출력 형식
접속 URL(`http://localhost:3000`) 또는 `dashboard_artifact.html`(정적 HTML 요약,
`.gitignore` 대상)

## 성공 기준
- [ ] `npm run build`(또는 `dev`) 실행이 에러 없이 완료됨
- [ ] `curl http://localhost:3000/api/customers`가 200 OK와 정상 데이터를 반환함
- [ ] (HTML 요약 요청 시) `dashboard_artifact.html`이 생성되고, KPI·고객군·지역·품목
      섹션에 실제 숫자가 채워져 있음(빈 값·"데이터 없음"만 있으면 실패)
