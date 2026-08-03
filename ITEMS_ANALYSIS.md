# 📦 품목명 자동분류 & 품목 데이터분석

## 📋 분석 개요

| 항목 | 설명 |
|---|---|
| 분석 기준일 | 2026-07-31 |
| 조회 기간 | 2026-07-25 ~ 2026-07-31 |
| 분석 대상 | orders.csv 내 모든 품목 주문 |
| 분석 대상 주문 수 | 13건 (예시) |

## 📊 분석 결과 요약

### 대분류별 주문 분포

| 대분류 | 주문 건수 | 비율 | 주요 중분류 |
|---|---|---|---|
| 식사 | 7건 | 53.8% | 한식, 분식, 일식, 양식 |
| 음료 | 4건 | 30.8% | 커피, 차, 생수 |
| 신선식품 | 2건 | 15.4% | 과일, 채소 |

### 주요 품목 (Top 5)

| 순위 | 품목명 | 주문 건수 | 대분류 | 중분류 |
|---|---|---|---|---|
| 1 | 김밥 (SET C) | 2건 | 식사 | 한식 |
| 2 | 커피 (대) | 2건 | 음료 | 커피 |
| 3 | 비빔밥 | 1건 | 식사 | 한식 |
| 4 | 녹차 (ICE) | 1건 | 음료 | 차 |
| 5 | 사과 | 1건 | 신선식품 | 과일 |

### 품목-고객군 연계 분석

| 대분류 | 신규 고객 | 재이용 고객 | 이탈 위험 고객 |
|---|---|---|---|
| 식사 | 2건 | 5건 | 0건 |
| 음료 | 1건 | 3건 | 0건 |
| 신선식품 | 0건 | 2건 | 0건 |

## 🔍 품목 분류 규칙

### 1차: 규칙 기반 키워드 매칭
- `CATEGORY_RULES` 사전 (80+ 개 키워드) 기반 정확 매칭
- 예: "커피" → 음료/커피, "김밥" → 식사/한식

### 2차: 확장 키워드 매칭
- 부분 문자열 매칭 기반 유연 분류
- 예: "카페라떼" → 음료/커피, "된장찌개" → 식사/한식

### 분류 결과
- **대분류**: 8개 (음료, 베이커리, 식사, 신선식품, 생활용품, 화장품, 패션, 전자제품, 레저/스포츠, 반려동물)
- **중분류**: 15+ 개

## 📁 산출물

| 파일 | 설명 |
|---|---|
| `output/product_classification.csv` | 품목명 → 카테고리 분류 결과 (13건) |
| `output/category_summary.csv` | 대분류별 요약 |
| `output/subcategory_summary.csv` | 중분류별 요약 |
| `output/top_products.csv` | 상위 품목 랭킹 |
| `output/product_demand_analysis.csv` | 대분류 × 고객군 수요 분석 |
| `output/product_demand_subcategory.csv` | 중분류 × 고객군 수요 분석 |

## 🛠️ 실행 방법

```bash
# 1. 데이터 준비
cp /path/to/orders.csv data/orders.csv

# 2. 품목명 분류
python product_classifier.py

# 3. 수요 분석
python product_analyzer.py

# 4. 대시보드 실행
streamlit run product_dashboard.py
# → http://localhost:8501
```

## 📝 품목 분류 규칙 확장 가이드

`product_classifier.py` 의 `CATEGORY_RULES` 딕셔너리를 수정하여 분류 규칙을 확장할 수 있습니다:

```python
CATEGORY_RULES = {
    "새로운품목명": {"대분류": "새로운대분류", "중분류": "새로운중분류"},
    # ...
}
```

## 🔗 연관 프로젝트

- **[고객분석 대시보드](https://github.com/hdmswjd98/itnew/tree/customer-analysis)**: 고객군 분류 + 이탈위험 스코어링
- **[월간 리포트](https://github.com/hdmswjd98/itnew/tree/monthly-report)**: 정기 리포트 자동 생성
