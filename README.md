# 🏢 잇뉴 고객 분석 대시보드 (Itnew Customer Analysis Dashboard)

AI 기반 고객 분석(고객군 분류, 이탈 위험 스코어링, 특성 분석) 결과를 **실시간으로 시각화**하는 Streamlit 대시보드입니다.

## 🚀 빠른 시작

### 1. 리포지토리 클론

```bash
git clone https://github.com/hdmswjd98/itnew.git
cd itnew
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터 준비

대시보드는 `customer_metrics.csv`, `customer_groups.csv`, `region_analysis.csv` 등의 분석 결과 CSV 를 읽어서 차트를 렌더링합니다.

**두 가지 방식:**

#### 방식 A: Timely 에서 파이프라인 실행 후 CSV 가져오기

1. Timely 환경에서 `customer-analysis-orchestrator` 실행
2. 생성된 CSV 파일들을 이 디렉토리에 복사
3. `streamlit run` 실행

#### 방식 B: 크론 자동화 (추천)

```bash
# 크론 등록 (매일 09:00 KST)
crontab -e
# 아래 줄 추가:
0 9 * * * cd /path/to/itnew && ./crons/run_pipeline.sh
```

### 4. 대시보드 실행

```bash
streamlit run streamlit_dashboard.py
```

브라우저에서 `http://localhost:8501` 로 접속!

---

## 📊 대시보드 구성 (11개 섹션)

| # | 섹션 | 내용 |
|---|---|---|
| 1 | 조회 기간 및 분석 조건 | 분석 기준일, 조회 기간, 대상 고객/주문 수 |
| 2 | 데이터 검증 결과 | 11개 검증 항목 통과/실패, 제외 데이터 상세 |
| 3 | 고객군별 현황 | 신규/재이용/이탈위험 고객 수·비율 (도넛 차트) |
| 4 | 고객별 이용 지표 | 5대 지표 테이블 + 주문횟수/누적금액/주기비교 차트 |
| 5 | 고객군 분류 결과 | 신규/재이용/이탈위험/일반 분류 + 이탈상태 분포 |
| 6 | 이탈 위험 고객 목록 | 위험/주의 등급 알럿 + 이탈위험비율 차트 + 기준선 |
| 7 | 고객군별 지역 특성 | 군별 지역 분포 (스택드 바) + 주요 지역 |
| 8 | 고객군별 업종 특성 | 군별 업종 분포 (스택드 바) + 주요 업종 |
| 9 | 고객군별 품목 분석 | 탭 전환(신규/재이용/이탈위험) + 이중축 차트 |
| 10 | AI 분석 요약 | 5문장 인사이트 (데이터 기반) |
| 11 | 분석 결과 검증 결과 | 10개 검증 항목 통과/실패 |

---

## 🔄 데이터 흐름

```
[Timely 분석 환경]                    [대시보드 배포 환경]
      │                                      │
      │ 1. 파이프라인 실행                     │
      │    (customer-analysis-orchestrator)   │
      │         │                             │
      │         ▼                             │
      │    CSV 결과 생성                      │
      │    (customer_metrics.csv 등)          │
      │         │                             │
      ├────────┼─────────────────────────────┤
      │        │ CSV 파일 공유                  │
      │        │ (git push / SCP / Supabase)  │
      │        │                             │
      ▼        ▼                             │
[대시보드] ◄───┘                             │
streamlit_dashboard.py                       │
  ├─ @st.cache_data(ttl=60)                 │
  │    def load_*():                        │
  │        return pd.read_csv("*.csv") ◄────┘
  │
  └─ Plotly 차트로 실시간 렌더링
```

---

## 🌐 배포 가이드

### Streamlit Cloud (무료, 가장 간편)

1. https://streamlit.io/cloud 에서 GitHub 계정 연동
2. `itnew` 리포지토리 선택
3. 메인 파일: `streamlit_dashboard.py`
4. "Deploy!" 클릭 → 약 2분 후 URL 생성

### Hugging Face Spaces (무료)

1. https://huggingface.co/spaces 에서 "Create new Space"
2. SDK: Streamlit 선택
3. GitHub 리포지토리 연결
4. 자동 배포

### 로컬 / 사내 서버

```bash
git clone https://github.com/hdmswjd98/itnew.git
cd itnew
pip install -r requirements.txt
streamlit run streamlit_dashboard.py
# → http://localhost:8501
```

### Supabase 연동 (향후 업그레이드)

CSV 파일 대신 Supabase Storage 에서 데이터를 직접 읽어오도록 업그레이드:

```python
# streamlit_dashboard.py
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

`.env` 또는 Streamlit secrets:
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

---

## 📁 프로젝트 구조

```
itnew/
├── streamlit_dashboard.py      # 메인 대시보드 (Streamlit + Plotly)
├── requirements.txt            # Python 패키지 의존성
├── .gitignore                  # Git 제외 파일 목록
├── README.md                   # 이 파일
├── .env.example                # 환경변수 템플릿
├── data/                       # (선택) 샘플 데이터
│   ├── members.csv
│   ├── orders.csv
│   ├── deliveries.csv
│   └── invalid_orders.csv
├── analysis/                   # (선택) 분석 결과 CSV
│   ├── customer_metrics.csv
│   ├── customer_groups.csv
│   ├── region_analysis.csv
│   ├── industry_analysis.csv
│   ├── product_analysis.csv
│   ├── churn_risk_customers.csv
│   └── ai_summary.txt
└── crons/                      # 자동화 스크립트
    └── run_pipeline.sh         # 파이프라인 실행 + 크론 가이드
```

---

## 🔐 보안 주의사항

- **`.env` 파일은 절대 Git 에 커밋하지 마세요** (`.gitignore` 에 이미 포함)
- **고객 개인정보(CSV)** 가 포함된 파일은 Private 리포지토리로 관리하거나 Git 에서 제외
- Supabase API 키는 `.env` 에 저장하고, 프로덕션에서는 **RLS(Row Level Security)** 설정 필수
- Streamlit Cloud 배포 시 secrets 설정에서 환경변수 관리

---

## 🛠️ 기술 스택

| 계층 | 기술 |
|---|---|
| 대시보드 프레임워크 | [Streamlit](https://streamlit.io) (Python) |
| 차트 라이브러리 | [Plotly](https://plotly.com/python/) (인터랙티브) |
| 데이터 처리 | [Pandas](https://pandas.pydata.org/) |
| 데이터 저장 | CSV (현재) → Supabase (향후) |
| 배포 | Streamlit Cloud / Hugging Face Spaces / 로컬 |
| 자동화 | Bash + Cron |

---

## 📝 다루는 분석 지표

### 고객별 5대 이용 지표
- **최근 주문일**: 고객별 최신 주문 날짜
- **주문 횟수**: 고객별 총 주문 건수
- **평균 이용 주기**: 주문 간 간격의 평균 (일)
- **최종 주문 후 경과일**: 기준일 − 최근 주문일
- **누적 이용 금액**: 고객별 총 주문 금액 합계

### 고객군 분류 (우선순위 적용)
1. **신규 고객**: 조회 기간 내 최초 주문
2. **이탈 위험 고객**: 2회 이상 주문 + 경과일 > 평균 이용 주기
3. **재이용 고객**: 조회 기간 이전 주문 + 조회 기간 내 재주문
4. **일반 고객**: 위 3가지 모두 미해당

### 이탈 위험 등급
| 등급 | 조건 | 조치 |
|---|---|---|
| 🟢 정상 | 경과일 ≤ 평균 이용 주기 | 모니터링 |
| 🟡 주의 | 평균 주기 < 경과일 ≤ 1.5×평균 | 선제적 관리 |
| 🔴 위험 | 경과일 > 1.5×평균 이용 주기 | 즉각 재방문 유도 |
| ⚪ 적용 안 함 | 평균 이용 주기 계산 불가 | 별도 관찰 |

---

## 📄 라이선스

MIT License
