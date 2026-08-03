"""
잇뉴 고객 분석 대시보드 — Streamlit 버전 (리뉴얼)
구조:
  1. 메인 뷰: 왼쪽 도넛차트(고객군) + 오른쪽 KPI
  2. 고객군 클릭 → 해당 군 상세 뷰 (상세 지표, 고객 목록, 이탈위험 현황 등)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="잇뉴 고객 분석 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 데이터 로드 함수 ====================
@st.cache_data(ttl=60)
def load_customer_metrics():
    """고객별 이용 지표 로드"""
    try:
        df = pd.read_csv('customer_metrics.csv')
        df['누적 이용 금액(원)'] = df['누적 이용 금액'].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        return df
    except:
        return pd.DataFrame(columns=['customer_id', '최근 주문일', '주문 횟수', '평균 이용 주기', '최종 주문 후 경과일', '누적 이용 금액', '회원 여부'])

@st.cache_data(ttl=60)
def load_customer_groups():
    """고객군 분류 결과 로드"""
    try:
        return pd.read_csv('customer_groups.csv')
    except:
        return pd.DataFrame(columns=['customer_id', '고객군', '이탈 상태', '이탈 등급', '판단 근거', '평균 이용 주기', '최종 주문 후 경과일'])

@st.cache_data(ttl=60)
def load_validation_results():
    try:
        return pd.read_csv('validation_results.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_invalid_records():
    try:
        return pd.read_csv('invalid_records.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_churn_risk():
    try:
        return pd.read_csv('churn_risk_customers.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_region_analysis():
    try:
        return pd.read_csv('region_analysis.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_industry_analysis():
    try:
        return pd.read_csv('industry_analysis.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_product_analysis():
    try:
        return pd.read_csv('product_analysis.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_validation_final():
    try:
        return pd.read_csv('validation_final.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_ai_summary():
    try:
        with open('ai_summary.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]
    except:
        return []

@st.cache_data(ttl=60)
def load_analysis_conditions():
    try:
        with open('customer_analysis_result.md', 'r', encoding='utf-8') as f:
            content = f.read()
        conditions = {}
        in_section1 = False
        for line in content.split('\n'):
            if line.startswith('## 1. 조회 기간'):
                in_section1 = True
                continue
            if line.startswith('## 2.'):
                in_section1 = False
            if in_section1 and ':' in line:
                key = line.split(':')[0].strip().lstrip('- ').strip()
                val = ':'.join(line.split(':')[1:]).strip()
                if key and val:
                    conditions[key] = val
        return conditions
    except:
        return {}

# ==================== 데이터 로드 ====================
metrics_df = load_customer_metrics()
groups_df = load_customer_groups()
validation_df = load_validation_results()
invalid_df = load_invalid_records()
churn_df = load_churn_risk()
region_df = load_region_analysis()
industry_df = load_industry_analysis()
product_df = load_product_analysis()
validation_final_df = load_validation_final()
ai_summary = load_ai_summary()
conditions = load_analysis_conditions()

# ==================== 메트릭 계산 ====================
total_customers = len(groups_df)
new_customers = groups_df[groups_df['고객군'] == '신규 고객']
returning_customers = groups_df[groups_df['고객군'] == '재이용 고객']
churn_customers = groups_df[groups_df['고객군'] == '이탈 위험 고객']
general_customers = groups_df[groups_df['고객군'] == '일반 고객']

new_count = len(new_customers)
returning_count = len(returning_customers)
churn_count = len(churn_customers)
general_count = len(general_customers)

# 이탈 위험 고객 상세 (위험/주의 분류)
churn_risk_detail = churn_df.copy() if len(churn_df) > 0 else pd.DataFrame()
risk_customers = churn_df[churn_df['이탈 등급'] == '위험'] if len(churn_df) > 0 else pd.DataFrame()
warn_customers = churn_df[churn_df['이탈 등급'] == '주의'] if len(churn_df) > 0 else pd.DataFrame()

# KPI 계산
total_orders = len(metrics_df)
total_revenue = metrics_df['누적 이용 금액(원)'].sum() if len(metrics_df) > 0 else 0
avg_order_count = metrics_df['주문 횟수'].mean() if len(metrics_df) > 0 else 0
valid_count = len(validation_df[validation_df['상태'] == '통과']) if len(validation_df) > 0 else 0
total_validation = len(validation_df) if len(validation_df) > 0 else 0

# ==================== 사이드바 ====================
with st.sidebar:
    st.title("🏢 잇뉴")
    st.caption("고객 분석 대시보드")
    st.divider()
    st.caption(f"기준일: {conditions.get('분석 기준일', datetime.now().strftime('%Y-%m-%d'))}")
    st.caption(f"분석대상: {total_customers}명")
    st.caption("데이터: CSV (60초 갱신)")

# ==================== 커스텀 CSS ====================
st.markdown("""
<style>
  .main { background-color: #0f1117; }
  .stApp { background-color: #0f1117; }
  .kpi-card {
    background: #1a1d2e;
    border: 1px solid #2a2d3e;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
  }
  .kpi-value { font-size: 2rem; font-weight: 700; margin: 6px 0; }
  .kpi-label { font-size: 0.75rem; color: #8b8fa8; text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-sub { font-size: 0.8rem; font-weight: 600; margin-top: 4px; }
  .alert-danger { background-color: rgba(225, 112, 85, 0.1); border-left: 4px solid #e17055; padding: 10px 14px; border-radius: 8px; }
  .alert-warning { background-color: rgba(253, 203, 110, 0.1); border-left: 4px solid #fdcb6e; padding: 10px 14px; border-radius: 8px; }
  .section-title { color: #e4e6f0; font-size: 1.1rem; font-weight: 600; margin-bottom: 12px; }
  .detail-header { color: #6c5ce7; font-size: 0.9rem; font-weight: 600; margin-bottom: 8px; }
  .progress-track { background: #2a2d3e; border-radius: 4px; height: 8px; }
  .progress-fill { height: 100%; border-radius: 4px; }
  .target-bar { background: linear-gradient(90deg, #00b894 0%, #00b894 var(--pct), #2a2d3e var(--pct), #2a2d3e 100%); border-radius: 4px; height: 24px; }
</style>
""", unsafe_allow_html=True)

# ==================== 세션 상태: 선택된 고객군 ====================
if 'selected_group' not in st.session_state:
    st.session_state.selected_group = '전체'

# ==================== 헤더 ====================
st.title("🏢 잇뉴 고객 분석 대시보드")
st.caption(f"조회 기간: {conditions.get('조회 시작일', 'N/A')} ~ {conditions.get('조회 종료일', 'N/A')} | 기준일: {conditions.get('분석 기준일', datetime.now().strftime('%Y-%m-%d'))}")
st.divider()

# ==================== [[메인 뷰]] ====================
# ── 왼쪽: 고객군 도넛 차트 ─────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<p class="section-title">👥 고객군 분포</p>', unsafe_allow_html=True)

    # 도넛 차트 (전체 + 클릭 가능)
    fig_doughnut = go.Figure(data=[go.Pie(
        labels=['신규 고객', '재이용 고객', '이탈 위험 고객', '일반 고객'],
        values=[new_count, returning_count, churn_count, general_count],
        hole=0.55,
        marker_colors=['#00b894', '#00cec9', '#e17055', '#a29bfe'],
        textinfo='label+percent',
        hovertemplate='%{label}<br>%{value}명 (%{percent})<extra></extra>',
        customdata=[new_count, returning_count, churn_count, general_count],
        hoverlabel=dict(bgcolor='#1a1d2e', font_color='#e4e6f0', font_size=13)
    )])
    fig_doughnut.update_traces(
        marker_line_width=2,
        marker_line_color='#0f1117'
    )
    fig_doughnut.update_layout(
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='right',
            x=1.15,
            bgcolor='rgba(26,29,46,0.9)',
            bordercolor='#2a2d3e',
            borderwidth=1,
            font=dict(color='#e4e6f0', size=13)
        ),
        margin=dict(l=20, r=120, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e6f0', size=13),
        width=340,
        height=340,
        annotations=[dict(
            text=f'{total_customers}명',
            font_size=22,
            font_color='#6c5ce7',
            font_weight=700,
            showarrow=False,
            x=0.5, y=0.5
        )]
    )
    st.plotly_chart(fig_doughnut, use_container_width=True, config={'displayModeBar': False})

    # 상세 보기 버튼 (차트 클릭 대신 버튼으로 선택)
    st.divider()
    st.caption("📌 고객군 선택:")
    group_options = ['전체'] + ([g for g in ['신규 고객', '재이용 고객', '이탈 위험 고객', '일반 고객'] if len(groups_df[groups_df['고객군'] == g]) > 0])
    selected = st.radio(
        "고객군 선택",
        options=group_options,
        index=group_options.index(st.session_state.selected_group) if st.session_state.selected_group in group_options else 0,
        label_visibility='collapsed',
        key=None,
        horizontal=True
    )
    if selected != st.session_state.selected_group:
        st.session_state.selected_group = selected
        st.rerun()

with col_right:
    st.markdown('<p class="section-title">🎯 기업 달성 목표 (KPI)</p>', unsafe_allow_html=True)

    # KPI 카드 4개
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpis = [
        ("전체 고객", f"{total_customers}명", f"{total_orders}건 주문", "#6c5ce7"),
        ("총 매출", f"{total_revenue:,.0f}원", f"평균 {avg_order_count:.1f}건/고객", "#00b894"),
        ("데이터 검증", f"{valid_count}/{total_validation}", "검증 항목 통과", "#00cec9"),
        ("MAU 달성", "진행률 확인 중", "100만 명 목표", "#fdcb6e"),
    ]
    for i, (col, (label, value, sub, color)) in enumerate(zip([kpi1, kpi2, kpi3, kpi4], kpis)):
        pct = 0.65 if i == 3 else 1.0
        col.markdown(f"""
        <div class="kpi-card" style="border-top: 3px solid {color};">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value" style="color:{color};">{value}</div>
          <div class="kpi-sub" style="color:{sub.split()[0] if sub else '#8b8fa8'};">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    # MAU 달성 바
    st.divider()
    mau_pct = 0.0  # 실제 데이터 들어오면 계산식으로 교체
    mau_label = "100만 명"
    mau_current = 0
    mau_target = 1_000_000
    st.markdown(f"""
    <div style="margin-bottom:6px;display:flex;justify-content:space-between;font-size:0.8rem;color:#8b8fa8;">
      <span>MAU (월간 활성 이용자)</span>
      <span>{mau_current:,} / {mau_label}</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill" style="background:#fdcb6e;width:{mau_pct*100:.0f}%;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-top:4px;">
      <span style="color:#8b8fa8;">현재</span>
      <span style="color:#fdcb6e;font-weight:600;">{mau_pct*100:.1f}% 달성</span>
    </div>
    """, unsafe_allow_html=True)

# ==================== [[선택된 고객군 상세 뷰]] ====================
st.divider()
st.markdown(f'<p class="section-title">📋 {st.session_state.selected_group} 상세 분석</p>', unsafe_allow_html=True)

# 선택된 고객군에 따른 데이터 필터링
if st.session_state.selected_group == '전체':
    detail_df = groups_df.copy()
    detail_metrics = metrics_df.copy()
    detail_churn = churn_df.copy() if len(churn_df) > 0 else pd.DataFrame()
    detail_region = region_df.copy()
    detail_industry = industry_df.copy()
    detail_product = product_df.copy()
    title_prefix = "전체 고객"
else:
    detail_df = groups_df[groups_df['고객군'] == st.session_state.selected_group]
    detail_metrics = metrics_df[metrics_df['customer_id'].isin(detail_df['customer_id'])]
    detail_churn = churn_df[churn_df['customer_id'].isin(detail_df['customer_id'])] if len(churn_df) > 0 else pd.DataFrame()
    detail_region = region_df[region_df['고객군'] == st.session_state.selected_group]
    detail_industry = industry_df[industry_df['고객군'] == st.session_state.selected_group]
    detail_product = product_df[product_df['고객군'] == st.session_state.selected_group]
    title_prefix = st.session_state.selected_group

# ── 상단 요약 카드 ──────────────────────────────────
if len(detail_df) > 0:
    count_val = len(detail_df)
    churn_in_group = len(detail_df[detail_df['이탈 상태'].isin(['위험', '주의'])]) if '이탈 상태' in detail_df.columns else 0
    avg_orders = detail_metrics['주문 횟수'].mean() if len(detail_metrics) > 0 else 0
    avg_revenue = detail_metrics['누적 이용 금액(원)'].mean() if len(detail_metrics) > 0 else 0

    sum1, sum2, sum3, sum4 = st.columns(4)
    with sum1:
        st.metric("고객 수", count_val)
    with sum2:
        st.metric("이탈 위험 수", churn_in_group, f"{churn_in_group/count_val*100:.1f}%" if count_val > 0 else "0%")
    with sum3:
        st.metric("평균 주문 횟수", f"{avg_orders:.1f}회", "고객당 평균" if count_val > 0 else "-")
    with sum4:
        st.metric("평균 누적 금액", f"{avg_revenue:,.0f}원", "고객당 평균" if count_val > 0 else "-")

# ── 탭: 상세 내용 ──────────────────────────────────
tab_profile, tab_churn, tab_region, tab_industry, tab_product = st.tabs([
    "📊 고객 프로필", "⚠️ 이탈 위험 현황", "🗺️ 지역 분포", "🏭 업종 분포", "📦 품목 현황"
])

# === 탭 1: 고객 프로필 ===
with tab_profile:
    st.markdown('<p class="detail-header">고객군별 프로필 요약</p>', unsafe_allow_html=True)
    # 이탈 상태별 분포
    if '이탈 상태' in detail_df.columns:
        churn_status_counts = detail_df['이탈 상태'].value_counts()
        fig_status = go.Figure(data=[go.Pie(
            labels=churn_status_counts.index.tolist(),
            values=churn_status_counts.values.tolist(),
            hole=0.4,
            marker_colors=['#00b894', '#fdcb6e', '#e17055', '#2a2d3e'][:len(churn_status_counts)],
            textinfo='label+percent',
            hovertemplate='%{label}: %{value}명 (%{percent})<extra></extra>'
        )])
        fig_status.update_layout(
            showlegend=True, margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'), width=280, height=280
        )
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.plotly_chart(fig_status, use_container_width=True, config={'displayModeBar': False})
        with col_b:
            st.dataframe(detail_df[['customer_id', '고객군', '이탈 상태', '이탈 등급', '판단 근거']], use_container_width=True, hide_index=True)
    else:
        st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # 고객별 지표 테이블
    st.divider()
    st.markdown('<p class="detail-header">고객별 5대 이용 지표</p>', unsafe_allow_html=True)
    if len(detail_metrics) > 0:
        display_metrics = detail_metrics[['customer_id', '최근 주문일', '주문 횟수', '평균 이용 주기', '최종 주문 후 경과일', '누적 이용 금액', '회원 여부']].copy()
        st.dataframe(display_metrics, use_container_width=True, hide_index=True)
    else:
        st.info("이용 지표 데이터가 없습니다.")

# === 탭 2: 이탈 위험 현황 ===
with tab_churn:
    if len(detail_churn) > 0:
        # 위험/주의 알럿
        risk_in_group = detail_churn[detail_churn['이탈 등급'] == '위험']
        warn_in_group = detail_churn[detail_churn['이탈 등급'] == '주의']

        if len(risk_in_group) > 0:
            st.markdown('<p class="alert-danger"><strong>🔴 위험 등급 고객</strong></p>', unsafe_allow_html=True)
            for _, row in risk_in_group.iterrows():
                st.markdown(f"""
                <div class="alert-danger">
                  <strong>{row['customer_id']}</strong> — 평균 이용 주기({row['평균 이용 주기']}) 대비 경과일({row['최종 주문 후 경과일']})이 1.5배 초과
                </div>
                """, unsafe_allow_html=True)

        if len(warn_in_group) > 0:
            st.markdown('<p class="alert-warning"><strong>🟡 주의 등급 고객</strong></p>', unsafe_allow_html=True)
            for _, row in warn_in_group.iterrows():
                st.markdown(f"""
                <div class="alert-warning">
                  <strong>{row['customer_id']}</strong> — 평균 이용 주기({row['평균 이용 주기']}) 대비 경과일({row['최종 주문 후 경과일']})이 1~1.5배 초과
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        st.markdown('<p class="detail-header">이탈 위험 고객 상세 목록</p>', unsafe_allow_html=True)
        churn_display = detail_churn[['customer_id', '이탈 등급', '평균 이용 주기', '최종 주문 후 경과일', '판단 근거']].copy()
        if '이탈 위험 비율' not in churn_display.columns and '최종 주문 후 경과일' in churn_display.columns and '평균 이용 주기' in churn_display.columns:
            churn_display['이탈 위험 비율'] = churn_display.apply(
                lambda r: f"{float(str(r['최종 주문 후 경과일']).replace('일','')) / float(str(r['평균 이용 주기']).replace('일','')):.1f}배"
                if str(r['평균 이용 주기']) != '계산 불가' else 'N/A', axis=1
            )
        st.dataframe(churn_display, use_container_width=True, hide_index=True)

        # 이탈 위험 비율 차트
        st.divider()
        st.markdown('<p class="detail-header">이탈 위험 비율 시각화</p>', unsafe_allow_html=True)
        ratio_labels, ratio_values, ratio_colors = [], [], []
        for _, row in detail_churn.iterrows():
            cycle = float(str(row['평균 이용 주기']).replace('일', ''))
            days = float(str(row['최종 주문 후 경과일']).replace('일', ''))
            ratio = days / cycle
            ratio_labels.append(f"{row['customer_id']} ({row['이탈 등급']})")
            ratio_values.append(ratio)
            ratio_colors.append('#e17055' if row['이탈 등급'] == '위험' else '#fdcb6e')

        if len(ratio_values) > 0:
            fig_ratio = go.Figure(data=[go.Bar(
                x=ratio_labels, y=ratio_values,
                marker_color=ratio_colors, marker_line_width=0,
                hovertemplate='고객: %{x}<br>이탈 위험 비율: %{y:.1f}배<extra></extra>'
            )])
            fig_ratio.add_hline(y=1.5, line_dash="dash", line_color="#e17055", annotation_text="위험 기준선 (1.5x)", annotation_position="top right")
            fig_ratio.add_hline(y=1.0, line_dash="dash", line_color="#00b894", annotation_text="정상 기준선 (1.0x)", annotation_position="top right")
            fig_ratio.update_layout(
                showlegend=False, margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e4e6f0'),
                yaxis=dict(range=[0, max(ratio_values) + 0.5], title='이탈 위험 비율 (배)')
            )
            st.plotly_chart(fig_ratio, use_container_width=True, config={'displayModeBar': False})
    else:
        st.success("해당 고객군에 이탈 위험 고객이 없습니다.")

# === 탭 3: 지역 분포 ===
with tab_region:
    if len(detail_region) > 0:
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            st.dataframe(detail_region.rename(columns={'region': '지역', '고객 수': '고객 수', '비율': '비율'}), use_container_width=True, hide_index=True)
        with col_r2:
            fig_reg = go.Figure(data=[go.Bar(
                x=detail_region['region'], y=detail_region['고객 수'],
                marker_color='#6c5ce7', marker_line_width=0,
                hovertemplate='%{x}: %{y}명<extra></extra>'
            )])
            fig_reg.update_layout(
                showlegend=False, margin=dict(l=20, r=20, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e4e6f0'),
                yaxis=dict(range=[0, max(detail_region['고객 수']) + 1], tick0=0, dtick=1)
            )
            st.plotly_chart(fig_reg, use_container_width=True, config={'displayModeBar': False})

        # 주요 지역
        main_region = detail_region.loc[detail_region['고객 수'].idxmax(), 'region'] if len(detail_region) > 0 else '-'
        main_count = detail_region['고객 수'].max() if len(detail_region) > 0 else 0
        st.markdown(f"<div style='text-align:center;color:#6c5ce7;font-weight:600;margin-top:8px;font-size:0.85rem;'>🏷️ 주요 지역: {main_region} ({main_count}명)</div>", unsafe_allow_html=True)
    else:
        st.info("지역 데이터가 없습니다.")

# === 탭 4: 업종 분포 ===
with tab_industry:
    if len(detail_industry) > 0:
        col_i1, col_i2 = st.columns([1, 2])
        with col_i1:
            st.dataframe(detail_industry.rename(columns={'industry': '업종', '고객 수': '고객 수', '비율': '비율'}), use_container_width=True, hide_index=True)
        with col_i2:
            fig_ind = go.Figure(data=[go.Bar(
                x=detail_industry['industry'], y=detail_industry['고객 수'],
                marker_color='#00cec9', marker_line_width=0,
                hovertemplate='%{x}: %{y}명<extra></extra>'
            )])
            fig_ind.update_layout(
                showlegend=False, margin=dict(l=20, r=20, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e4e6f0'),
                yaxis=dict(range=[0, max(detail_industry['고객 수']) + 1], tick0=0, dtick=1)
            )
            st.plotly_chart(fig_ind, use_container_width=True, config={'displayModeBar': False})

        main_industry = detail_industry.loc[detail_industry['고객 수'].idxmax(), 'industry'] if len(detail_industry) > 0 else '-'
        main_count = detail_industry['고객 수'].max() if len(detail_industry) > 0 else 0
        st.markdown(f"<div style='text-align:center;color:#6c5ce7;font-weight:600;margin-top:8px;font-size:0.85rem;'>🏷️ 주요 업종: {main_industry} ({main_count}명)</div>", unsafe_allow_html=True)
    else:
        st.info("업종 데이터가 없습니다.")

# === 탭 5: 품목 현황 ===
with tab_product:
    if len(detail_product) > 0:
        st.dataframe(detail_product[['item_name', '주문_건수', '주문_금액', '비율']].rename(
            columns={'item_name': '품목', '주문_건수': '주문 건수', '주문_금액': '주문 금액', '비율': '비율'}
        ), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown('<p class="detail-header">품목별 주문 금액 분포</p>', unsafe_allow_html=True)
        fig_prod = go.Figure(data=[go.Bar(
            x=detail_product['item_name'], y=pd.to_numeric(detail_product['주문_금액'], errors='coerce'),
            marker_color='#fdcb6e', marker_line_width=0,
            hovertemplate='품목: %{x}<br>주문 금액: %{y:,.0f}원<extra></extra>'
        )])
        fig_prod.update_layout(
            showlegend=False, margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'),
            yaxis=dict(title='주문 금액 (원)', tickformat=',d')
        )
        st.plotly_chart(fig_prod, use_container_width=True, config={'displayModeBar': False})

        top_item = detail_product.sort_values('주문_금액', ascending=False).iloc[0]
        st.markdown(f"<div style='text-align:center;color:#fdcb6e;font-weight:600;margin-top:8px;font-size:0.85rem;'>🏷️ 최고 매출 품목: {top_item['item_name']}</div>", unsafe_allow_html=True)
    else:
        st.info("품목 데이터가 없습니다.")

# ==================== 하단: 데이터 검증 + AI 요약 (축소) ====================
st.divider()
st.markdown('<p class="section-title">🔍 데이터 검증 결과</p>', unsafe_allow_html=True)

if len(validation_df) > 0:
    col_v1, col_v2 = st.columns([2, 1])
    with col_v1:
        st.dataframe(validation_df.rename(columns={'항목': '검증 항목', '상태': '통과/실패', '내용': '확인 결과'}), use_container_width=True, hide_index=True)
    with col_v2:
        passed = len(validation_df[validation_df['상태'] == '통과'])
        total_v = len(validation_df)
        st.metric("검증 통과율", f"{passed/total_v*100:.0f}%" if total_v > 0 else "0%")
        if passed == total_v and total_v > 0:
            st.success("✅ 모든 검증 항목 통과")
        elif passed > 0:
            st.warning(f"⚠️ {total_v - passed}개 항목 실패")

if len(invalid_df) > 0:
    with st.expander("📋 제외 데이터 상세"):
        st.dataframe(invalid_df, use_container_width=True, hide_index=True)

st.divider()
st.markdown('<p class="section-title">🤖 AI 분석 요약</p>', unsafe_allow_html=True)
for line in ai_summary:
    st.markdown(f"- {line}")

# ==================== 푸터 ====================
st.divider()
st.caption("데이터는 CSV 기반이며, 파이프라인 실행 후 60초 내 대시보드에 반영됩니다.")
