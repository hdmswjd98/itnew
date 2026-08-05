---
name: run-customer-analysis
description: |
  [고객분석] 첨부된 엑셀 파일(잇뉴 주문·회원 데이터)을 받아 고객분석 전체 파이프라인을 자동 실행한다.
  엑셀 → CSV 변환 → validate → load → merge → metrics → churn → classify → pattern → validate → report 순서로 실행되며,
  완료 후 data/output/ 의 결과 파일 목록과 고객군 분포, AI 요약을 요약 출력한다.
  실행 코드: services/customer/import_real_data.py → services/customer/pipeline.py
model: claude-haiku-4-5
---

# run-customer-analysis

사용자가 잇뉴 주문·회원 데이터 엑셀 파일을 Timely 대화에 첨부하면, 이 스킬이 파일 경로를 찾아 고객분석 파이프라인을 끝까지 자동 실행한다.

## 실행 순서

1. **첨부 엑셀 탐색**
   - 프로젝트 루트 직하 `*.xlsx` 조회 → 없으면 상위 디렉토리 rglob `*.xlsx` → 환경변수 `ATTACHED_FILE`/`EXCEL_PATH` 확인.
2. **Excel → CSV 변환** (`services/customer/import_real_data.py`)
   - 두 시트(`주문_2026년1-6월` / `회원_전체누적`)를 pandas로 읽고 members.csv / orders.csv / deliveries.csv / invalid_orders.csv 로 변환, `data/input/`에 저장.
3. **데이터 검증** (1단계)
4. **데이터 로드** (2단계) — `data/input/*.csv` 읽기 → `valid_orders_raw.csv`
5. **데이터 병합** (3단계)
6. **고객별 지표 계산** (4단계) — MAU 등
7. **이탈 위험 점수 산정** (5단계) — churn grade
8. **고객군 분류** (6단계) — 신규/재이용/이탈위험/일반
9. **패턴 분석** (7단계) — 지역·업종·품목 통계
10. **최종 검증** (8단계)
11. **보고서 생성** (9단계) — `data/output/customer_analysis_result.md`
12. **결과 요약 출력**
    - data/output/ 파일 목록
    - 고객군 분포 (신규/재이용/이탈위험/일반 수·비율)
    - AI 요약(ai_summary.txt) 앞부분
    - Next.js 대시보드 실행 안내 (`cd web && npm run dev`)

## 사전 조건

- Excel 파일에 두 시트 `주문_2026년1-6월`, `회원_전체누적` 포함.
- 프로젝트 루트에 `services/`, `data/` 구조 존재 (`services/customer/pipeline.py`, `services/customer/import_real_data.py`).
- `data/input/`, `data/output/` 디렉토리 존재.

## 주의사항

- 실제 회원·주문 데이터(PII)가 포함되므로 결과 CSV는 Git에 올리지 않는다 (`.gitignore` 적용).
- 엑셀 파일에 여러 개가 있을 경우 가장 먼저 찾은 1개를 사용.
