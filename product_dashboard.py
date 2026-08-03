"""
잇뉴 품목 분석 대시보드 — Streamlit 버전
품목명 자동분류 결과와 품목별 수요 분석을 실시간으로 시각화합니다.

사용법:
    streamlit run product_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path
import plotly.graph_objects as go

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="잇뉴 품목 분석 대시보드",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 데이터 로드 함수 ====================
@st.cache_data(ttl=60)
def load_product_classification():
    """품목명 분류 결과 로드"""
    try:
        return pd.read_csv('output/product_classification.csv')
    except:
        return pd.DataFrame(columns=['order_id', 'item_name', 'order_date', 'customer_id', '대분류', '중분류'])

@st.cache_data(ttl=60)
def load_category_summary():
    """대분류별 요약 로드"""
    try:
        return pd.read_csv('output/category_summary.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_subcategory_summary():
    """중분류별 요약 로드"""
    try:
        return pd.read_csv('output/subcategory_summary.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_top_products():
    """상위 품목 로드"""
    try:
        return pd.read_csv('output/top_products.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_demand_analysis():
    """수요 분석 결과 로드 (고객군 연계)"""
    try:
        return pd.read_csv('output/product_demand_analysis.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_demand_subcategory():
    """중분류 × 고객군 수요 분석 로드"""
    try:
        return pd.read_csv('output/product_demand_subcategory.csv')
    except:
        return pd.DataFrame()

# ==================== 데이터 로드 ====================
classification_df = load_product_classification()
category_summary_df = load_category_summary()
subcategory_summary_df = load_subcategory_summary()
top_products_df = load_top_products()
demand_analysis_df = load_demand_analysis()
demand_subcategory_df = load_demand_subcategory()

# ==================== 메트릭 계산 ====================
total_orders = len(classification_df)
unique_products = classification_df['item_name'].nunique() if len(classification_df) > 0 else 0
unique_categories = classification_df['대분류'].nunique() if len(classification_df) > 0 else 0
unique_subcategories = classification_df['중분류'].nunique() if len(classification_df) > 0 else 0

# ==================== 사이드바 ====================
with st.sidebar:
    st.title("📦 잇뉴")
    st.markdown("### 품목 분석 대시보드")
    st.divider()

    st.subheader("📋 분석 요약")
    st.metric("전체 주문 건수", f"{total_orders:,}")
    st.metric("고유 품목명", f"{unique_products:,}")
    st.metric("대분류 수", f"{unique_categories}")
    st.metric("중분류 수", f"{unique_subcategories}")

    st.divider()
    st.subheader("🔄 데이터 갱신")
    st.caption("접속 시마다 최신 분석 결과를 자동으로 읽어옵니다")
    st.caption("파이프라인 실행 후 약 60초 내 대시보드 갱신됨")

    st.divider()
    st.caption("Made with ❤️ by Timely")

# ==================== 메인 헤더 ====================
st.title("📦 잇뉴 품목 분석 대시보드")
st.caption(f"분석 기준일: {datetime.now().strftime('%Y-%m-%d')} | 총 {total_orders:,}건 주문 분석")
st.divider()

# ==================== KPI ROW ====================
st.subheader("📈 핵심 지표")
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.markdown(f"""
    <div style="background:#1a1d2e;border:1px solid #2a2d3e;border-radius:12px;padding:20px;text-align:center;">
      <div style="font-size:0.8rem;color:#8b8fa8;text-transform:uppercase;letter-spacing:0.5px;">전체 주문</div>
      <div style="font-size:2.2rem;font-weight:700;margin:8px 0 4px;">{total_orders:,}</div>
      <div style="font-size:0.8rem;color:#6c5ce7;font-weight:600;margin-top:4px;">{unique_categories}개 대분류</div>
    </div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
    <div style="background:#1a1d2e;border:1px solid #2a2d3e;border-radius:12px;padding:20px;text-align:center;">
      <div style="font-size:0.8rem;color:#8b8fa8;text-transform:uppercase;letter-spacing:0.5px;">품목 수</div>
      <div style="font-size:2.2rem;font-weight:700;margin:8px 0 4px;">{unique_products:,}</div>
      <div style="font-size:0.8rem;color:#00cec9;font-weight:600;margin-top:4px;">{unique_subcategories}개 중분류</div>
    </div>
    """, unsafe_allow_html=True)
with kpi3:
    if len(category_summary_df) > 0:
        top_category = category_summary_df.loc[category_summary_df['주문_건수'].idxmax(), '대분류']
        top_pct = category_summary_df.loc[category_summary_df['주문_건수'].idxmax(), '비율']
    else:
        top_category, top_pct = '-', '-'
    st.markdown(f"""
    <div style="background:#1a1d2e;border:1px solid #2a2d3e;border-radius:12px;padding:20px;text-align:center;">
      <div style="font-size:0.8rem;color:#8b8fa8;text-transform:uppercase;letter-spacing:0.5px;">최다 카테고리</div>
      <div style="font-size:2.2rem;font-weight:700;margin:8px 0 4px;">{top_category}</div>
      <div style="font-size:0.8rem;color:#e17055;font-weight:600;margin-top:4px;">{top_pct}%</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ==================== SECTION: 대분류별 현황 ====================
st.subheader("📊 대분류별 현황")
if len(category_summary_df) > 0:
    col_cat_1, col_cat_2 = st.columns([1, 2])
    with col_cat_1:
        st.markdown("### 대분류별 주문 분포")
        fig_cat = go.Figure(data=[go.Bar(
            x=category_summary_df['대분류'],
            y=category_summary_df['주문_건수'],
            marker_color=['#6c5ce7', '#00cec9', '#fd79a8', '#fdcb6e', '#e17055', '#00b894', '#a29bfe', '#55efc4'][:len(category_summary_df)],
            marker_line_width=0,
            hovertemplate='대분류: %{x}<br>주문 건수: %{y:,}건 ({pct}%)<extra></extra>'
        )])
        fig_cat.update_layout(
            showlegend=False, margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'),
            yaxis=dict(range=[0, max(category_summary_df['주문_건수']) * 1.15], tick0=0)
        )
        st.plotly_chart(fig_cat, use_container_width=True, config={'displayModeBar': False})

    with col_cat_2:
        st.markdown("### 대분류별 상세 현황")
        display_cat = category_summary_df.copy()
        display_cat['주문_건수'] = display_cat['주문_건수'].apply(lambda x: f"{x:,}")
        display_cat['비율'] = display_cat['비율'].apply(lambda x: f"{x}%")
        st.dataframe(display_cat, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 대분류별 비율")
    for _, row in category_summary_df.iterrows():
        pct = float(row['비율'])
        cat_name = row['대분류']
        color = '#6c5ce7' if cat_name == category_summary_df.loc[category_summary_df['주문_건수'].idxmax(), '대분류'] else '#8b8fa8'
        st.markdown(f"""
        <div style="margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:0.85rem;">
            <span>{cat_name}</span>
            <span style="color:{color};font-weight:600;">{int(row['주문_건수']):,}건 ({pct:.1f}%)</span>
          </div>
          <div style="background:#2a2d3e;border-radius:4px;height:8px;">
            <div style="background:{color};border-radius:4px;height:100%;width:{pct}%;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== SECTION: 중분류별 현황 ====================
st.subheader("📊 중분류별 현황")
if len(subcategory_summary_df) > 0:
    col_sub_1, col_sub_2 = st.columns([1, 2])
    with col_sub_1:
        st.markdown("### 중분류별 주문 분포")
        fig_sub = go.Figure(data=[go.Bar(
            x=subcategory_summary_df['중분류'],
            y=subcategory_summary_df['주문_건수'],
            marker_color=['#6c5ce7', '#00cec9', '#fd79a8', '#fdcb6e', '#e17055', '#00b894', '#a29bfe', '#55efc4'][:len(subcategory_summary_df)],
            marker_line_width=0,
            hovertemplate='중분류: %{x}<br>주문 건수: %{y:,}건 ({pct}%)<extra></extra>'
        )])
        fig_sub.update_layout(
            showlegend=False, margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'),
            yaxis=dict(range=[0, max(subcategory_summary_df['주문_건수']) * 1.15], tick0=0)
        )
        st.plotly_chart(fig_sub, use_container_width=True, config={'displayModeBar': False})

    with col_sub_2:
        st.markdown("### 중분류별 상세 현황")
        display_sub = subcategory_summary_df.copy()
        display_sub['주문_건수'] = display_sub['주문_건수'].apply(lambda x: f"{x:,}")
        display_sub['비율'] = display_sub['비율'].apply(lambda x: f"{x}%")
        st.dataframe(display_sub, use_container_width=True, hide_index=True)

# ==================== SECTION: 상위 품목 ====================
st.subheader("🏆 상위 품목 분석")
if len(top_products_df) > 0:
    col_top_1, col_top_2 = st.columns([2, 1])
    with col_top_1:
        st.markdown("### Top 10 품목 (주문 건수)")
        fig_top = go.Figure(data=[go.Bar(
            x=top_products_df.head(10)['item_name'],
            y=top_products_df.head(10)['주문_건수'],
            marker_color=['#6c5ce7', '#00cec9', '#fd79a8', '#fdcb6e', '#e17055', '#00b894', '#a29bfe', '#55efc4', '#fab1a0', '#81ecec'],
            marker_line_width=0,
            hovertemplate='품목: %{x}<br>주문 건수: %{y:,}건 ({pct}%)<extra></extra>'
        )])
        fig_top.update_layout(
            showlegend=False, margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'),
            yaxis=dict(range=[0, max(top_products_df.head(10)['주문_건수']) * 1.15], tick0=0)
        )
        st.plotly_chart(fig_top, use_container_width=True, config={'displayModeBar': False})

    with col_top_2:
        st.markdown("### Top 10 품목 상세")
        display_top = top_products_df.head(10).copy()
        display_top['주문_건수'] = display_top['주문_건수'].apply(lambda x: f"{x:,}")
        display_top['비율'] = display_top['비율'].apply(lambda x: f"{x}%")
        st.dataframe(display_top, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 전체 품목 목록")
    st.dataframe(top_products_df, use_container_width=True, hide_index=True)

# ==================== SECTION: 고객군 × 품목 수요 분석 ====================
st.subheader("🎯 고객군별 품목 수요 분석")
if len(demand_analysis_df) > 0:
    st.markdown("### 대분류 × 고객군 수요 분석")
    st.dataframe(demand_analysis_df, use_container_width=True, hide_index=True)
else:
    st.info("고객군 연계 데이터가 없습니다. customer_groups.csv 와 함께 product_analyzer.py 를 실행해주세요.")

if len(demand_subcategory_df) > 0:
    st.divider()
    st.markdown("### 중분류 × 고객군 수요 분석")
    st.dataframe(demand_subcategory_df, use_container_width=True, hide_index=True)
else:
    st.info("중분류 × 고객군 연계 데이터가 없습니다.")

# ==================== SECTION: 품목명 분류기 ====================
st.divider()
st.subheader("🔧 품목명 자동 분류기")
st.markdown("""
### 분류 방식
품목명은 다음 두 가지 방식으로 분류됩니다:

1. **규칙 기반 매칭 (1차)**: 사전 정의된 키워드 사전을 기반으로 정확한 매칭
2. **키워드 확장 매칭 (2차)**: 부분 문자열 매칭을 통한 유연한 분류

### 분류 규칙 예시
| 품목명 | 대분류 | 중분류 |
|---|---|---|
| 아메리카노 | 음료 | 커피 |
| 김밥 | 식사 | 한식 |
| 사과 | 신선식품 | 과일 |
| 샴푸 | 생활용품 | 세면도구 |
| 노트북 | 전자제품 | 컴퓨터 |
| 티셔츠 | 패션 | 상의 |
""")

st.info("💡 **품목명을 더 정확히 분류하려면 `product_classifier.py` 의 `CATEGORY_RULES` 사전을 수정하세요.**")

# ==================== 푸터 ====================
st.divider()
st.caption("""
**개발 계획** | Phase 1: 품목명 분류기 → Phase 2: 수요 분석 → Phase 3: Streamlit 대시보드 → Phase 4: NLP 분류 & 수요 예측
""")
