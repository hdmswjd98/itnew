# 📦 품목 분석 대시보드 (Product Analysis Dashboard)

`item_name`(품목명) 자동 분류 및 품목별 수요 분석 대시보드입니다.

## 🚀 빠른 시작

```bash
git clone -b product-analysis https://github.com/hdmswjd98/itnew.git
cd itnew
pip install -r requirements.txt
# 데이터 준비 후 실행
streamlit run product_dashboard.py
# → http://localhost:8501
```

## 🎯 핵심 기능

| 기능 | 설명 | 상태 |
|---|---|---|
| **품목명 자동 분류** | 주문 데이터에서 품목명 추출 → 카테고리 자동 분류 (NLP / 규칙 기반) | 🔄 개발 중 |
| **품목별 수요 분석** | 품목별 주문량·금액·추이 분석 | 🔄 개발 중 |
| **카테고리별 현황** | 대분류/중분류별 고객군 분포 | 🔄 개발 중 |
| **수요 예측 (향후)** | 시계열 기반 품목별 수요 예측 | ⏳ 예정 |

## 📁 프로젝트 구조 (예정)

```
itnew/
├── product_dashboard.py        # 품목 분석 Streamlit 대시보드
├── product_classifier.py       # 품목명 자동 분류기
├── product_analyzer.py         # 품목별 수요 분석 모듈
├── requirements.txt            # Python 패키지 의존성
├── .gitignore
├── data/                       # 품목 데이터
│   └── items.csv               # 품목명 원본 데이터
├── output/                     # 분석 결과 (gitignore)
│   ├── product_classification.csv
│   ├── product_demand_analysis.csv
│   └── category_summary.csv
└── README.md
```

## 🛠️ 개발 계획

### Phase 1: 품목명 자동 분류기
- [ ] `orders.csv`의 `item_name` 컬럼 추출
- [ ] 품목명 전처리 (특수문자 제거, 정규화)
- [ ] 규칙 기반 카테고리 매핑 (예: "커피" → 음료, "빵" → 베이커리)
- [ ] 분류 결과 CSV 저장 (`product_classification.csv`)

### Phase 2: 품목별 수요 분석
- [ ] 품목별 주문량·금액·추이 계산
- [ ] 고객군별 품목 선호도 분석 (신규/재이용/이탈위험)
- [ ] 월별/연별 트렌드 분석
- [ ] 분석 결과 CSV 저장 (`product_demand_analysis.csv`)

### Phase 3: Streamlit 대시보드
- [ ] 품목별 주문량/금액 차트 (Plotly)
- [ ] 카테고리별 스택드 바 차트
- [ ] 고객군별 품목 선호도 비교
- [ ] 기간별 필터링 (월별/연별)

### Phase 4: 대시보드 고도화 (향후)
- [ ] 품목명 자동 분류 NLP 모델 적용
- [ ] 수요 예측 알고리즘 (시계열)
- [ ] Supabase 연동 (실시간 데이터)
- [ ] 이메일 리포트 자동 발송

## 📊 예상 산출물

| 산출물 | 설명 |
|---|---|
| `product_classification.csv` | 품목명 → 카테고리 분류 결과 |
| `product_demand_analysis.csv` | 품목별 주문량·금액·추이 |
| `category_summary.csv` | 카테고리별 요약 통계 |
| `product_dashboard.py` | Streamlit 대화형 대시보드 |

## 📬 팀 협업

| 담당 | 브랜치 | 주요 작업 |
|---|---|---|
| 데이터 분석가 | `product-analysis` | 분류기 개발, 분석 로직 |
| 상품 기획자 | `product-analysis` | 카테고리 정의 검토, 지표 설계 |
| 프론트엔지니어 | `product-analysis` | 대시보드 UI/UX |

## 🔗 연관 프로젝트

- **[고객분석 대시보드](https://github.com/hdmswjd98/itnew/tree/customer-analysis)**: 고객군 분류 + 이탈위험 스코어링
- **[월간 리포트](https://github.com/hdmswjd98/itnew/tree/monthly-report)**: 정기 리포트 자동 생성
