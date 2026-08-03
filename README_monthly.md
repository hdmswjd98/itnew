# 📅 월간 리포트 자동화 (Monthly Report Automation)

매월 분석 결과를 Markdown/PDF 리포트로 자동 생성하는 도구입니다.

## 🚀 빠른 시작

```bash
git clone -b monthly-report https://github.com/hdmswjd98/itnew.git
cd itnew
pip install -r requirements.txt
# 설정 후 실행
python generate_report.py
# → output/2026-07월간리포트.md
```

## 🎯 핵심 기능

| 기능 | 설명 | 상태 |
|---|---|---|
| **리포트 자동 생성** | 11개 대시보드 섹션을 Markdown 리포트로 자동 채움 | 🔄 개발 중 |
| **PDF 변환** | Markdown → PDF 렌더링 (weasyprint/pdfkit) | ⏳ 예정 |
| **이메일 발송** | 생성된 리포트를 이메일/슬랙으로 자동 전송 | ⏳ 예정 |
| **히스토리 관리** | 월별 리포트 아카이빙 및 버전 관리 | ⏳ 예정 |
| **주기적 실행** | 크론/스케줄러 기반 매월 자동 실행 | ⏳ 예정 |

## 📁 프로젝트 구조 (예정)

```
itnew/
├── generate_report.py          # 월간 리포트 생성 스크립트
├── requirements.txt            # Python 패키지 의존성
├── .gitignore
├── README.md                   # 이 파일
├── templates/                  # 리포트 템플릿
│   └── monthly_report.md.j2    # Jinja2 템플릿
├── output/                     # 생성된 리포트 (gitignore)
│   └── 2026-07월간리포트.md
└── scheduler/                  # 스케줄러 설정
    ├── run_monthly_report.sh   # 월간 리포트 실행 스크립트
    └── crontab.txt             # 크론 설정 예시
```

## 🛠️ 개발 계획

### Phase 1: 리포트 템플릿 작성
- [ ] Jinja2 템플릿 작성 (`templates/monthly_report.md.j2`)
- [ ] 11개 섹션 템플릿 정의
- [ ] 변수 바인딩 로직 구현

### Phase 2: 리포트 생성 스크립트
- [ ] CSV 데이터 읽기 (customer_metrics.csv 등)
- [ ] 템플릿 렌더링 (Jinja2)
- [ ] Markdown 파일 저장 (`output/YYYY-MM월간리포트.md`)
- [ ] 실행 로그 기록

### Phase 3: PDF 변환
- [ ] weasyprint 설치 및 설정
- [ ] Markdown → HTML 변환 (markdown 라이브러리)
- [ ] HTML → PDF 변환 (weasyprint)
- [ ] PDF 스타일링 (CSS)

### Phase 4: 이메일 발송
- [ ] Gmail API 설정 (또는 SMTP)
- [ ] 리포트 PDF 첨부 이메일 발송
- [ ] 슬랙 웹훅 통합 (선택)
- [ ] 발송 실패 시 재시도 로직

### Phase 5: 스케줄러 & 히스토리
- [ ] 크론 등록 (매월 1일 09:00)
- [ ] 월별 리포트 아카이빙
- [ ] 리포트 메타데이터 관리 (JSON)
- [ ] 웹 대시보드에서 리포트 목록 조회 (향후)

## 📊 예상 산출물

| 산출물 | 설명 |
|---|---|
| `output/YYYY-MM월간리포트.md` | 월간 리포트 Markdown |
| `output/YYYY-MM월간리포트.pdf` | 월간 리포트 PDF |
| `scheduler/run_monthly_report.sh` | 리포트 생성 실행 스크립트 |
| `templates/monthly_report.md.j2` | Jinja2 리포트 템플릿 |

## 🔗 연관 프로젝트

- **[고객분석 대시보드](https://github.com/hdmswjd98/itnew/tree/customer-analysis)**: 리포트의 데이터 소스
- **[품목 분석](https://github.com/hdmswjd98/itnew/tree/product-analysis)**: 품목별 리포트 확장 (향후)

## 📬 팀 협업

| 담당 | 브랜치 | 주요 작업 |
|---|---|---|
| 데이터 분석가 | `monthly-report` | 리포트 템플릿 작성, 데이터 바인딩 |
| 운영 담당자 | `monthly-report` | 이메일 발송 설정, 스케줄러 관리 |
| 프론트엔지니어 | `monthly-report` | PDF 스타일링, 웹 뷰어 개발 |

## 📝 월간 리포트 포함 내용 (11개 섹션)

| # | 섹션 | 내용 |
|---|---|---|
| 1 | 조회 기간 및 분석 조건 | 분석 기준일, 조회 기간, 대상 고객/주문 수 |
| 2 | 데이터 검증 결과 | 11개 검증 항목 통과/실패, 제외 데이터 상세 |
| 3 | 고객군별 현황 | 신규/재이용/이탈위험 고객 수·비율 |
| 4 | 고객별 이용 지표 | 5대 지표 테이블 |
| 5 | 고객군 분류 결과 | 신규/재이용/이탈위험/일반 분류 |
| 6 | 이탈 위험 고객 목록 | 위험/주의 등급 알럿 |
| 7 | 고객군별 지역 특성 | 군별 지역 분포 |
| 8 | 고객군별 업종 특성 | 군별 업종 분포 |
| 9 | 고객군별 품목 분석 | 탭 전환 + 이중축 차트 |
| 10 | AI 분석 요약 | 5문장 인사이트 |
| 11 | 분석 결과 검증 결과 | 10개 검증 항목 통과/실패 |

## 🚀 실행 예시

```bash
# 수동 실행
python generate_report.py --month 2026-07

# 크론으로 자동 실행 (매월 1일 09:00)
0 9 1 * * cd /path/to/itnew && python generate_report.py --month $(date +\%Y-\%m)
```
