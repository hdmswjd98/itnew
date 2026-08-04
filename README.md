# 🏢 잇뉴 (ITNEW) — 통합 분석 플랫폼

AI 기반 **고객 분석**, **월간 리포트**, **품목 데이터 분석**을 하나의 리포지토리에서 관리하는 통합 프로젝트입니다.

## 🗂️ 브랜치 구조

| 브랜치 | 담당 | 설명 |
|---|---|---|
| `main` | — | 통합 가이드 + 프로젝트 개요 (이 파일) |
| `customer-analysis` | 데이터분석팀 | **고객 분석 대시보드** — 고객군 분류, 이탈위험 스코어링, 특성 분석 |
| `monthly-report` | 운영팀 | **월간 리포트 자동 생성** — 정기 리포트 템플릿 & 자동화 |
| `product-analysis` | 상품기획팀 | **품목 자동분류 & 품목 데이터 분석** — 품목명 분류, 품목별 수요 분석 |

## 🚀 빠른 시작

### 대시보드별 클론 & 실행

```bash
# 1) 고객 분석 대시보드
git clone -b customer-analysis https://github.com/hdmswjd98/itnew.git customer-analysis
cd customer-analysis
pip install -r requirements.txt
# 데이터 준비 후:
python3 -m streamlit run app.py
# → http://localhost:8501

# 2) 월간 리포트 (개발 중)
git clone -b monthly-report https://github.com/hdmswjd98/itnew.git monthly-report
cd monthly-report

# 3) 품목 분석 (개발 중)
git clone -b product-analysis https://github.com/hdmswjd98/itnew.git product-analysis
cd product-analysis
```

### 공통 설정

```bash
# Python 가상환경 (선택)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 데이터 폴더

원본 CSV는 `data/input/`에 넣고, 파이프라인이 생성하는 분석 결과는
`data/output/`에 저장됩니다. 두 폴더는 Git에 올라가지 않습니다.

```text
data/
├── input/
│   ├── members.csv
│   ├── orders.csv
│   ├── deliveries.csv
│   └── invalid_orders.csv
└── output/
    ├── customer_metrics.csv
    ├── customer_groups.csv
    └── ...
```

```bash
python3 -m services.customer.pipeline
python3 -m streamlit run app.py
```

## 📊 3대 대시보드 개요

### 1. 고객분석 대시보드 (`customer-analysis` 브랜치)

**고객군 분류 + 이탈위험 스코어링 + 특성 분석** 결과를 실시간 시각화

| 기능 | 설명 |
|---|---|
| 고객군 분류 | 신규 / 재이용 / 이탈위험 / 일반 (우선순위 적용) |
| 이탈위험 스코어링 | 정상/주의/위험/적용안함 (평균이용주기 vs 경과일) |
| 특성 분석 | 지역·업종·품목별 군별 분포 + AI 요약 |
| 검증 | 10개 항목 자동 검증 (데이터 정합성 확인) |

**핵심 지표 (고객별 5대)**
- 최근 주문일 · 주문 횟수 · 평균 이용 주기 · 최종 주문 후 경과일 · 누적 이용 금액

**대시보드 섹션 (11개)**
1. 조회 기간 및 분석 조건 → 2. 데이터 검증 결과 → 3. 고객군별 현황 → 4. 고객별 이용 지표 → 5. 고객군 분류 결과 → 6. 이탈 위험 고객 목록 → 7. 고객군별 지역 특성 → 8. 고객군별 업종 특성 → 9. 고객군별 품목 분석 → 10. AI 분석 요약 → 11. 분석 결과 검증 결과

### 2. 월간 리포트 (`monthly-report` 브랜치)

**정기 리포트 자동 생성** — 매월 분석 결과를 Markdown/PDF 리포트로 자동 작성

| 기능 | 설명 |
|---|---|
| 리포트 템플릿 | 11개 섹션 자동 채움 |
| PDF 변환 | Streamlit → PDF export |
| 이메일 발송 | (향후) Gmail/슬랙 자동 전송 |
| 히스토리 관리 | 월별 리포트 아카이빙 |

### 3. 품목 분석 (`product-analysis` 브랜치)

**품목명 자동 분류 + 품목별 수요 분석** 대시보드

| 기능 | 설명 |
|---|---|
| 품목명 자동 분류 | NLP/규칙 기반 품목 카테고리 분류 |
| 품목별 수요 분석 | 주문량·금액·추이 분석 |
| 카테고리별 현황 | 품목명 → 대분류/중분류 매핑 |
| 수요 예측 | (향후) 시계열 기반 수요 예측 |

## 🔄 데이터 흐름

```
┌─────────────────────────────────────────────────────┐
│                  공통 데이터 소스                      │
│  members.csv · orders.csv · deliveries.csv           │
│  (팀 내 공유 스토리지 / Supabase / S3)               │
└──────┬──────────────┬──────────────┬───────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────────┐
│ 고객분석  │  │ 월간리포트│  │  품목 분석    │
│ (pipeline│  │ (report  │  │  (product    │
│  실행)   │  │  생성)   │  │   분석)      │
└────┬─────┘  └────┬─────┘  └──────┬───────┘
     │              │              │
     ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────────┐
│ CSV 결과 │  │ MD/PDF   │  │  CSV/DB 결과  │
│ 생성     │  │ 리포트   │  │  (품목 매칭)  │
└────┬─────┘  └────┬─────┘  └──────┬───────┘
     │              │              │
     └──────────────┼──────────────┘
                    ▼
           ┌──────────────────┐
           │  대시보드 렌더링  │
           │  (Streamlit /    │
           │   웹 UI)         │
           └──────────────────┘
```

## 🛠️ 기술 스택

| 계층 | 기술 |
|---|---|
| 대시보드 프레임워크 | [Streamlit](https://streamlit.io) (Python) |
| 차트 라이브러리 | [Plotly](https://plotly.com/python/) (인터랙티브) |
| 데이터 처리 | [Pandas](https://pandas.pydata.org/) |
| 데이터 저장 | CSV (현재) → Supabase (향후) |
| 배포 | Streamlit Cloud / Hugging Face Spaces / 로컬 |
| 자동화 | Bash + Cron |
| 리포트 생성 | pandas + markdown + (향후) weasyprint/pdfkit |

## 🌐 배포 가이드

### Streamlit Cloud (무료, 추천)

1. https://streamlit.io/cloud 에서 GitHub 계정 연동
2. `itnew` 리포지토리 선택 → 원하는 브랜치 선택
3. 메인 파일: `app.py`
4. "Deploy!" 클릭 → 약 2분 후 URL 생성

### 로컬 / 사내 서버

```bash
git clone -b <브랜치명> https://github.com/hdmswjd98/itnew.git
cd itnew
pip install -r requirements.txt
python3 -m streamlit run app.py
# → http://localhost:8501
```

### Supabase 연동 (향후 업그레이드)

CSV 대신 Supabase Storage/API 에서 데이터를 실시간 조회:

```python
import supabase
import os

@st.cache_data(ttl=60)
def load_customer_metrics():
    client = supabase.create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    response = client.table('customer_metrics').select('*').execute()
    return pd.DataFrame(response.data)
```

## 📁 통합 프로젝트 구조

```
itnew/
├── app.py                       # 통합 Streamlit 실행 파일
├── dashboards/
│   ├── customer/
│   │   ├── page.py              # 고객분석 화면 진입점
│   │   └── sections.py          # 고객분석 화면 구성
│   ├── monthly/
│   │   ├── page.py              # 월간리포트 화면 진입점
│   │   └── sections.py          # 월간리포트 화면 구성
│   └── product/
│       ├── page.py              # 품목분석 화면 진입점
│       └── sections.py          # 품목분석 화면 구성
├── services/                    # 화면과 분리된 분석·저장 로직
│   ├── customer/                # 고객분석 파이프라인
│   ├── monthly/                 # 월간보고서 저장·내보내기
│   └── product/                 # 품목 분류·수요 분석
├── data/
│   ├── input/                   # 공통 원본 데이터
│   ├── output/                  # 공통 실행 산출물
│   └── sample/                  # 공개 가능한 예제 데이터
├── shared/
│   ├── navigation.py            # 공통 사이드바
│   ├── paths.py                 # 공통 데이터 경로
│   └── theme.py                 # 라이트·다크 테마
├── requirements.txt
└── README.md
```

## 🔐 보안 주의사항

- **`.env` 파일은 절대 Git 에 커밋하지 마세요** (`.gitignore` 에 포함)
- **고객 개인정보(CSV)** 가 포함된 파일은 Private 리포지토리로 관리
- Supabase API 키는 `.env` 에 저장, 프로덕션에서 **RLS 설정 필수**
- Streamlit Cloud 배포 시 secrets 설정에서 환경변수 관리
- 민감 데이터는 `data/` 폴더에 두고 `.gitignore` 로 제외 권장

## 📝 담당 브랜치 전환 방법

```bash
# 전체 프로젝트 클론 (main)
git clone https://github.com/hdmswjd98/itnew.git
cd itnew

# 고객분석 대시보드만 보기
git checkout customer-analysis

# 월간 리포트만 보기
git checkout monthly-report

# 품목 분석만 보기
git checkout product-analysis

# 다시 통합 가이드로
git checkout main
```

## 🤝 팀 협업 가이드

| 역할 | 브랜치 | 주요 작업 |
|---|---|---|
| 데이터 분석가 | `customer-analysis` | 파이프라인 개선, 지표 추가, 대시보드 UI 개선 |
| 운영 담당자 | `monthly-report` | 리포트 템플릿 작성, 이메일 발송 설정 |
| 상품 기획자 | `product-analysis` | 품목명 분류 규칙 정의, 수요 분석 지표 설계 |

### 브랜치 작업 흐름

```bash
# 1. 최신 main 가져오기
git checkout main
git pull origin main

# 2. 작업할 브랜치로 전환
git checkout customer-analysis

# 3. main 의 최신 내용을 브랜치에 반영 (필요시)
git merge main

# 4. 작업 & 커밋
git add .
git commit -m "feat: 신규 지표 추가"
git push origin customer-analysis

# 5. main 에 반영 (필요시 PR 생성)
git checkout main
git merge customer-analysis
git push origin main
```

## 📄 라이선스

MIT License
