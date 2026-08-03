"""
잇뉴 고객 분석 대시보드 — Streamlit 버전
사용자가 접속할 때마다 최신 CSV 데이터를 읽어 실시간 차트를 렌더링합니다.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="잇뉴 고객 분석 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 커스텀 CSS ====================
st.markdown("""
<style>
  .main { background-color: #0f1117; }
  .stApp { background-color: #0f1117; }
  .sidebar .stSidebarNav { background-color: #1a1d2e; }
  h1, h2, h3 { color: #e4e6f0 !important; }
  .metric-card {
    background: #1a1d2e;
    border: 1px solid #2a2d3e;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
  }
  .kpi-value { font-size: 2.2rem; font-weight: 700; color: #e4e6f0; }
  .kpi-label { font-size: 0.8rem; color: #8b8fa8; text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-sub { font-size: 0.8rem; font-weight: 600; margin-top: 4px; }
  .kpi-total .kpi-sub { color: #6c5ce7; }
  .kpi-new .kpi-sub { color: #00b894; }
  .kpi-returning .kpi-sub { color: #00cec9; }
  .kpi-churn .kpi-sub { color: #e17055; }
  .kpi-order .kpi-sub { color: #e67e22; }
  .dataframe { background-color: #1a1d2e !important; border-radius: 8px; }
  .stDataFrame { background-color: #1a1d2e !important; }
  .stMarkdown { color: #e4e6f0 !important; }
  .alert-danger { background-color: rgba(225, 112, 85, 0.1); border-left: 4px solid #e17055; padding: 14px 18px; border-radius: 10px; color: #e4e6f0; }
  .alert-warning { background-color: rgba(253, 203, 110, 0.1); border-left: 4px solid #fdcb6e; padding: 14px 18px; border-radius: 10px; color: #e4e6f0; }
  .alert-success { background-color: rgba(0, 184, 148, 0.1); border-left: 4px solid #00b894; padding: 14px 18px; border-radius: 10px; color: #e4e6f0; }
  .progress-bar-container { background-color: #2a2d3e; border-radius: 4px; height: 8px; }
  .progress-fill { height: 100%; border-radius: 4px; }
  .stExpander { background-color: #1a1d2e !important; border-color: #2a2d3e !important; }
  .stExpander details summary { color: #e4e6f0 !important; font-weight: 600; }
  .stExpander details summary:hover { color: #6c5ce7 !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 데이터 로드 함수 ====================
@st.cache_data(ttl=60)  # 60초마다 캐시 갱신
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
        df = pd.read_csv('customer_groups.csv')
        return df
    except:
        return pd.DataFrame(columns=['customer_id', '고객군', '이탈 상태', '이탈 등급', '판단 근거', '평균 이용 주기', '최종 주문 후 경과일'])

@st.cache_data(ttl=60)
def load_validation_results():
    """검증 결과 로드"""
    try:
        df = pd.read_csv('validation_results.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_invalid_records():
    """제외 데이터 로드"""
    try:
        df = pd.read_csv('invalid_records.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_churn_risk():
    """이탈 위험 고객 목록 로드"""
    try:
        df = pd.read_csv('churn_risk_customers.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_region_analysis():
    """지역 분석 결과 로드"""
    try:
        df = pd.read_csv('region_analysis.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_industry_analysis():
    """업종 분석 결과 로드"""
    try:
        df = pd.read_csv('industry_analysis.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_product_analysis():
    """품목 분석 결과 로드"""
    try:
        df = pd.read_csv('product_analysis.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_validation_final():
    """최종 검증 결과 로드"""
    try:
        df = pd.read_csv('validation_final.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_ai_summary():
    """AI 요약문 로드"""
    try:
        with open('ai_summary.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]
    except:
        return []

@st.cache_data(ttl=60)
def load_analysis_conditions():
    """분석 조건 로드"""
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
group_counts = groups_df['고객군'].value_counts().to_dict()
new_count = group_counts.get('신규 고객', 0)
returning_count = group_counts.get('재이용 고객', 0)
churn_count = group_counts.get('이탈 위험 고객', 0)
general_count = group_counts.get('일반 고객', 0)
total_orders = len(metrics_df)
valid_count = len(validation_df[validation_df['상태'] == '통과']) if len(validation_df) > 0 else 0
total_validation = len(validation_df) if len(validation_df) > 0 else 0

# ==================== 사이드바 ====================
with st.sidebar:
    st.title("🏢 잇뉴")
    st.markdown("### 고객 분석 대시보드")
    st.divider()

    # 분석 조건 정보
    st.subheader("📋 분석 조건")
    if conditions:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("분석 기준일", conditions.get('분석 기준일', '-'))
            st.metric("조회 시작일", conditions.get('조회 시작일', '-'))
        with col2:
            st.metric("조회 종료일", conditions.get('조회 종료일', '-'))
            st.metric("분석 대상", f"{conditions.get('분석 대상 고객 수', '0')}명")
    else:
        st.metric("분석 기준일", datetime.now().strftime('%Y-%m-%d'))
        st.metric("분석 대상", f"{total_customers}명")

    st.divider()
    st.subheader("📊 빠른 요약")
    st.metric("전체 고객", total_customers)
    st.metric("신규 고객", new_count, f"{new_count/total_customers*100:.1f}%" if total_customers > 0 else "0%")
    st.metric("재이용 고객", returning_count, f"{returning_count/total_customers*100:.1f}%" if total_customers > 0 else "0%")
    st.metric("이탈 위험", churn_count, f"{churn_count/total_customers*100:.1f}%" if total_customers > 0 else "0%")

    if churn_count > 0:
        st.divider()
        st.warning("⚠️ 이탈 위험 고객 발생!")
        st.caption(f"{churn_count}명의 고객이 이탈 위험 상태입니다")

    st.divider()
    st.subheader("🔄 데이터 갱신")
    st.caption("접속 시마다 최신 CSV 데이터를 자동으로 읽어옵니다")
    st.caption("파이프라인 실행 후 약 60초 내 대시보드 갱신됨")

    # 사이드바 푸터
    st.divider()
    st.caption("Made with ❤️ by Timely")

# ==================== 메인 헤더 ====================
st.title("🏢 잇뉴 고객 분석 대시보드")
st.caption(f"분석 기준일: {conditions.get('분석 기준일', datetime.now().strftime('%Y-%m-%d'))} | 조회 기간: {conditions.get('조회 시작일', 'N/A')} ~ {conditions.get('조회 종료일', 'N/A')}")

st.divider()

# ==================== KPI ROW ====================
st.subheader("📈 핵심 지표")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.markdown(f"""
    <div class="metric-card kpi-total">
      <div class="kpi-label">전체 고객</div>
      <div class="kpi-value">{total_customers}</div>
      <div class="kpi-sub">{conditions.get('분석 대상 주문 수', '0')}건 주문</div>
    </div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
    <div class="metric-card kpi-new">
      <div class="kpi-label">신규 고객</div>
      <div class="kpi-value">{new_count}</div>
      <div class="kpi-sub">{new_count/total_customers*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
with kpi3:
    st.markdown(f"""
    <div class="metric-card kpi-returning">
      <div class="kpi-label">재이용 고객</div>
      <div class="kpi-value">{returning_count}</div>
      <div class="kpi-sub">{returning_count/total_customers*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
with kpi4:
    st.markdown(f"""
    <div class="metric-card kpi-churn">
      <div class="kpi-label">이탈 위험 고객</div>
      <div class="kpi-value">{churn_count}</div>
      <div class="kpi-sub">{churn_count/total_customers*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
with kpi5:
    st.markdown(f"""
    <div class="metric-card kpi-order">
      <div class="kpi-label">데이터 검증</div>
      <div class="kpi-value">{valid_count}/{total_validation}</div>
      <div class="kpi-sub">항목 통과</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ==================== SECTION: 데이터 검증 ====================
with st.expander("🔍 2. 데이터 검증 결과"):
    st.subheader("검증 항목별 결과")
    if len(validation_df) > 0:
        st.dataframe(
            validation_df.rename(columns={'항목': '검증 항목', '상태': '통과/실패', '내용': '확인 결과'}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("검증 결과 데이터를 찾을 수 없습니다.")

    st.divider()
    st.subheader("제외 데이터 상세")
    if len(invalid_df) > 0:
        st.dataframe(
            invalid_df.rename(columns={
                'order_id': 'order_id', 'customer_id': 'customer_id',
                'order_date': 'order_date', 'item_name': 'item_name',
                'order_amount': 'order_amount', '오류 사유': '오류 사유'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("제외 데이터가 없습니다.")

# ==================== SECTION: 고객군 현황 ====================
st.subheader("👥 고객군별 현황")
col1, col2 = st.columns([1, 2])
with col1:
    # 고객군 분포 도넛
    import plotly.graph_objects as go

    fig_doughnut = go.Figure(data=[go.Pie(
        labels=['신규 고객', '재이용 고객', '이탈 위험 고객'],
        values=[new_count, returning_count, churn_count],
        hole=0.6,
        marker_colors=['#00b894', '#00cec9', '#e17055'],
        textinfo='label+percent',
        hovertemplate='%{label}: %{value}명 (%{percent})<extra></extra>'
    )])
    fig_doughnut.update_layout(
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e6f0')
    )
    st.plotly_chart(fig_doughnut, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("### 고객군별 상세 현황")
    group_data = pd.DataFrame({
        '고객군': ['신규 고객', '재이용 고객', '이탈 위험 고객'],
        '고객 수': [new_count, returning_count, churn_count],
        '비율': [f"{new_count/total_customers*100:.1f}%", f"{returning_count/total_customers*100:.1f}%", f"{churn_count/total_customers*100:.1f}%"]
    })
    st.dataframe(group_data, use_container_width=True, hide_index=True, column_config={
        '고객군': st.column_config.TextColumn(width="medium"),
        '고객 수': st.column_config.NumberColumn(width="small"),
        '비율': st.column_config.TextColumn(width="small")
    })

    # 진행률 바
    st.divider()
    st.markdown("### 고객군별 비율")
    for group_name, count, color in [('신규 고객', new_count, '#00b894'), ('재이용 고객', returning_count, '#00cec9'), ('이탈 위험 고객', churn_count, '#e17055')]:
        pct = count / total_customers * 100 if total_customers > 0 else 0
        st.markdown(f"""
        <div style="margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.85rem;">
            <span>{group_name}</span>
            <span style="color: {color}; font-weight: 600;">{count}명 ({pct:.1f}%)</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-fill" style="width: {pct}%; background-color: {color};"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== SECTION: 고객별 이용 지표 ====================
st.subheader("📊 4. 고객별 이용 지표")
col_metrics_1, col_metrics_2 = st.columns(2)

with col_metrics_1:
    st.markdown("### 고객별 5대 이용 지표")
    if len(metrics_df) > 0:
        display_metrics = metrics_df[['customer_id', '최근 주문일', '주문 횟수', '평균 이용 주기', '최종 주문 후 경과일', '누적 이용 금액']].copy()
        st.dataframe(display_metrics, use_container_width=True, hide_index=True)
    else:
        st.warning("이용 지표 데이터를 찾을 수 없습니다.")

with col_metrics_2:
    st.markdown("### 주문 횟수 분포")
    if len(metrics_df) > 0:
        fig_orders = go.Figure(data=[go.Bar(
            x=metrics_df['customer_id'],
            y=metrics_df['주문 횟수'],
            marker_color=['#6c5ce7', '#00cec9', '#fd79a8', '#fdcb6e', '#e17055', '#00b894'],
            marker_line_width=0,
            hovertemplate='고객: %{x}<br>주문 횟수: %{y}회<extra></extra>'
        )])
        fig_orders.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'),
            yaxis=dict(range=[0, max(metrics_df['주문 횟수']) + 1], tick0=0, dtick=1)
        )
        st.plotly_chart(fig_orders, use_container_width=True, config={'displayModeBar': False})

    st.divider()
    st.markdown("### 누적 이용 금액 분포")
    if len(metrics_df) > 0:
        fig_amount = go.Figure(data=[go.Bar(
            x=metrics_df['customer_id'],
            y=metrics_df['누적 이용 금액(원)'],
            marker_color=['#6c5ce7', '#00cec9', '#fd79a8', '#fdcb6e', '#e17055', '#00b894'],
            marker_line_width=0,
            hovertemplate='고객: %{x}<br>누적 금액: %{y:,.0f}원<extra></extra>'
        )])
        fig_amount.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'),
            yaxis=dict(tickformat=',d', title='누적 이용 금액 (원)')
        )
        st.plotly_chart(fig_amount, use_container_width=True, config={'displayModeBar': False})

# 주기 vs 경과일 비교
st.divider()
st.markdown("### 평균 이용 주기 vs 최종 주문 후 경과일 비교")
if len(metrics_df) > 0:
    cycle_data = []
    days_data = []
    labels = []
    for _, row in metrics_df.iterrows():
        labels.append(row['customer_id'])
        cycle_raw = str(row['평균 이용 주기'])
        if cycle_raw != '계산 불가' and cycle_raw != '':
            cycle_data.append(float(cycle_raw.replace('일', '')))
        else:
            cycle_data.append(None)
        days_data.append(float(str(row['최종 주문 후 경과일']).replace('일', '')))

    fig_cycle = go.Figure()
    fig_cycle.add_trace(go.Bar(
        name='평균 이용 주기 (일)',
        x=labels,
        y=cycle_data,
        marker_color='rgba(108, 92, 231, 0.7)',
        marker_line_width=0,
        hovertemplate='고객: %{x}<br>평균 이용 주기: %{y:.0f}일<extra></extra>'
    ))
    fig_cycle.add_trace(go.Bar(
        name='최종 주문 후 경과일 (일)',
        x=labels,
        y=days_data,
        marker_color='rgba(253, 203, 110, 0.7)',
        marker_line_width=0,
        hovertemplate='고객: %{x}<br>경과일: %{y:.0f}일<extra></extra>'
    ))
    fig_cycle.update_layout(
        barmode='group',
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e6f0'),
        yaxis=dict(range=[0, max(days_data) + 10], title='일수'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig_cycle, use_container_width=True, config={'displayModeBar': False})

# ==================== SECTION: 고객군 분류 결과 ====================
st.subheader("🏷️ 5. 신규·재이용·이탈 위험 고객 분류 결과")
if len(groups_df) > 0:
    st.markdown("### 고객군 분류 결과 (우선순위: 신규 → 이탈위험 → 재이용)")
    display_groups = groups_df[['customer_id', '고객군', '이탈 상태', '이탈 등급', '판단 근거']].copy()
    st.dataframe(display_groups, use_container_width=True, hide_index=True)
else:
    st.warning("고객군 분류 결과를 찾을 수 없습니다.")

col_class_1, col_class_2 = st.columns(2)
with col_class_1:
    st.markdown("### 고객군별 고객 수")
    fig_group_bar = go.Figure(data=[go.Bar(
        y=['신규 고객', '재이용 고객', '이탈 위험 고객'],
        x=[new_count, returning_count, churn_count],
        orientation='h',
        marker_color=['#00b894', '#00cec9', '#e17055'],
        marker_line_width=0,
        hovertemplate='%{y}: %{x}명<extra></extra>'
    )])
    fig_group_bar.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e6f0'),
        xaxis=dict(range=[0, max(new_count, returning_count, churn_count) + 1], tick0=0, dtick=1)
    )
    st.plotly_chart(fig_group_bar, use_container_width=True, config={'displayModeBar': False})

with col_class_2:
    st.markdown("### 이탈 상태 분포")
    churn_status_counts = groups_df['이탈 상태'].value_counts()
    fig_churn_pie = go.Figure(data=[go.Pie(
        labels=churn_status_counts.index.tolist(),
        values=churn_status_counts.values.tolist(),
        hole=0.4,
        marker_colors={'정상': '#00b894', '주의': '#fdcb6e', '위험': '#e17055', '적용 안 함': '#2a2d3e'}.get(
            list(churn_status_counts.index), ['#00b894', '#fdcb6e', '#e17055', '#2a2d3e']),
        textinfo='label+percent',
        hovertemplate='%{label}: %{value}명 (%{percent})<extra></extra>'
    )])
    fig_churn_pie.update_layout(
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e6f0')
    )
    st.plotly_chart(fig_churn_pie, use_container_width=True, config={'displayModeBar': False})

# ==================== SECTION: 이탈 위험 고객 ====================
st.subheader("⚠️ 6. 이탈 위험 고객 목록 및 분류 근거")

# 위험 등급 알럿
if len(churn_df) > 0:
    risk_customers = churn_df[churn_df['이탈 등급'] == '위험']
    warn_customers = churn_df[churn_df['이탈 등급'] == '주의']

    if len(risk_customers) > 0:
        for _, row in risk_customers.iterrows():
            st.markdown(f"""
            <div class="alert-danger">
              <strong>🔴 위험 등급 고객: {row['customer_id']}</strong><br>
              평균 이용 주기({row['평균 이용 주기']}) 대비 경과일({row['최종 주문 후 경과일']})이 1.5배 초과 — 즉각적인 재방문 유도 조치 필요
            </div>
            """, unsafe_allow_html=True)

    if len(warn_customers) > 0:
        for _, row in warn_customers.iterrows():
            st.markdown(f"""
            <div class="alert-warning">
              <strong>🟡 주의 등급 고객: {row['customer_id']}</strong><br>
              평균 이용 주기({row['평균 이용 주기']}) 대비 경과일({row['최종 주문 후 경과일']})이 1~1.5배 초과 — 모니터링을 통한 선제적 관리 권장
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 이탈 위험 고객 상세 목록 (위험등급순 정렬)")
    if len(churn_df) > 0:
        churn_display = churn_df[['customer_id', '이탈 등급', '평균 이용 주기', '최종 주문 후 경과일', '판단 근거']].copy()
        # 이탈 위험 비율 계산
        churn_display['이탈 위험 비율'] = churn_display.apply(
            lambda r: f"{float(str(r['최종 주문 후 경과일']).replace('일','')) / float(str(r['평균 이용 주기']).replace('일','')):.1f}배"
            if str(r['평균 이용 주기']) != '계산 불가' else 'N/A', axis=1
        )
        st.dataframe(churn_display, use_container_width=True, hide_index=True)
    else:
        st.info("이탈 위험 고객이 없습니다.")

    st.divider()
    st.markdown("### 이탈 위험 비율 시각화")
    if len(churn_df) > 0:
        ratio_labels = []
        ratio_values = []
        ratio_colors = []
        for _, row in churn_df.iterrows():
            cycle = float(str(row['평균 이용 주기']).replace('일', ''))
            days = float(str(row['최종 주문 후 경과일']).replace('일', ''))
            ratio = days / cycle
            ratio_labels.append(f"{row['customer_id']} ({row['이탈 등급']})")
            ratio_values.append(ratio)
            ratio_colors.append('#e17055' if row['이탈 등급'] == '위험' else '#fdcb6e')

        fig_churn_ratio = go.Figure(data=[go.Bar(
            x=ratio_labels,
            y=ratio_values,
            marker_color=ratio_colors,
            marker_line_width=0,
            hovertemplate='고객: %{x}<br>이탈 위험 비율: %{y:.1f}배<extra></extra>'
        )])
        # 기준선 추가 (1.5배, 1.0배)
        fig_churn_ratio.add_hline(y=1.5, line_dash="dash", line_color="#e17055", annotation_text="위험 기준선 (1.5x)", annotation_position="top right")
        fig_churn_ratio.add_hline(y=1.0, line_dash="dash", line_color="#00b894", annotation_text="정상 기준선 (1.0x)", annotation_position="top right")
        fig_churn_ratio.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e4e6f0'),
            yaxis=dict(range=[0, max(ratio_values) + 0.5], title='이탈 위험 비율 (배)')
        )
        st.plotly_chart(fig_churn_ratio, use_container_width=True, config={'displayModeBar': False})

# ==================== SECTION: 지역 특성 ====================
st.subheader("🗺️ 7. 고객군별 지역 특성")

region_groups = ['신규 고객', '재이용 고객', '이탈 위험 고객']
region_colors = {'신규 고객': '#00b894', '재이용 고객': '#00cec9', '이탈 위험 고객': '#e17055'}

col_region_1, col_region_2, col_region_3 = st.columns(3)
for idx, group in enumerate(region_groups):
    with [col_region_1, col_region_2, col_region_3][idx]:
        group_region = region_df[region_df['고객군'] == group]
        main_region = group_region.loc[group_region['고객 수'].idxmax(), 'region'] if len(group_region) > 0 else '-'
        main_count = group_region['고객 수'].max() if len(group_region) > 0 else 0

        st.markdown(f"### {group} — 지역 분포")
        if len(group_region) > 0:
            st.dataframe(
                group_region[['region', '고객 수', '비율']].rename(columns={'region': '지역', '고객 수': '고객 수', '비율': '비율'}),
                use_container_width=True, hide_index=True
            )
            # 미니 차트
            fig_region = go.Figure(data=[go.Bar(
                x=group_region['region'],
                y=group_region['고객 수'],
                marker_color=region_colors[group],
                marker_line_width=0,
                hovertemplate='%{x}: %{y}명<extra></extra>'
            )])
            fig_region.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e4e6f0'),
                yaxis=dict(range=[0, max(group_region['고객 수']) + 1], tick0=0, dtick=1)
            )
            st.plotly_chart(fig_region, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info(f"{group} 지역 데이터가 없습니다.")

        st.markdown(f"<div style='text-align:center; color: #6c5ce7; font-weight: 600; margin-top: 8px; font-size: 0.85rem;'>🏷️ 주요 지역: {main_region} ({main_count}명)</div>", unsafe_allow_html=True)

# 지역 스택드 바
st.divider()
st.markdown("### 고객군별 지역 중첩 비교 (스택드 바)")
if len(region_df) > 0:
    all_regions = region_df['region'].unique()
    fig_region_stack = go.Figure()
    for group in region_groups:
        group_data = region_df[region_df['고객군'] == group]
        fig_region_stack.add_trace(go.Bar(
            name=group,
            x=all_regions,
            y=[group_data[group_data['region'] == r]['고객 수'].values[0] if len(group_data[group_data['region'] == r]) > 0 else 0 for r in all_regions],
            marker_color=region_colors[group],
            marker_line_width=0,
            hovertemplate='%{fullData.name}: %{y}명<extra></extra>'
        ))
    fig_region_stack.update_layout(
        barmode='stack',
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e6f0'),
        yaxis=dict(range=[0, total_customers + 1], tick0=0, dtick=1)
    )
    st.plotly_chart(fig_region_stack, use_container_width=True, config={'displayModeBar': False})

# ==================== SECTION: 업종 특성 ====================
st.subheader("🏭 8. 고객군별 업종 특성")

col_ind_1, col_ind_2, col_ind_3 = st.columns(3)
for idx, group in enumerate(region_groups):
    with [col_ind_1, col_ind_2, col_ind_3][idx]:
        group_industry = industry_df[industry_df['고객군'] == group]
        main_industry = group_industry.loc[group_industry['고객 수'].idxmax(), 'industry'] if len(group_industry) > 0 else '-'
        main_count = group_industry['고객 수'].max() if len(group_industry) > 0 else 0

        st.markdown(f"### {group} — 업종 분포")
        if len(group_industry) > 0:
            st.dataframe(
                group_industry[['industry', '고객 수', '비율']].rename(columns={'industry': '업종', '고객 수': '고객 수', '비율': '비율'}),
                use_container_width=True, hide_index=True
            )
            fig_industry = go.Figure(data=[go.Bar(
                x=group_industry['industry'],
                y=group_industry['고객 수'],
                marker_color=region_colors[group],
                marker_line_width=0,
                hovertemplate='%{x}: %{y}명<extra></extra>'
            )])
            fig_industry.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e4e6f0'),
                yaxis=dict(range=[0, max(group_industry['고객 수']) + 1], tick0=0, dtick=1)
            )
            st.plotly_chart(fig_industry, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info(f"{group} 업종 데이터가 없습니다.")

        st.markdown(f"<div style='text-align:center; color: #6c5ce7; font-weight: 600; margin-top: 8px; font-size: 0.85rem;'>🏷️ 주요 업종: {main_industry} ({main_count}명)</div>", unsafe_allow_html=True)

# 업종 스택드 바
st.divider()
st.markdown("### 고객군별 업종 중첩 비교 (스택드 바)")
if len(industry_df) > 0:
    all_industries = industry_df['industry'].unique()
    fig_industry_stack = go.Figure()
    for group in region_groups:
        group_data = industry_df[industry_df['고객군'] == group]
        fig_industry_stack.add_trace(go.Bar(
            name=group,
            x=all_industries,
            y=[group_data[group_data['industry'] == i]['고객 수'].values[0] if len(group_data[group_data['industry'] == i]) > 0 else 0 for i in all_industries],
            marker_color=region_colors[group],
            marker_line_width=0,
            hovertemplate='%{fullData.name}: %{y}명<extra></extra>'
        ))
    fig_industry_stack.update_layout(
        barmode='stack',
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e6f0'),
        yaxis=dict(range=[0, total_customers + 1], tick0=0, dtick=1)
    )
    st.plotly_chart(fig_industry_stack, use_container_width=True, config={'displayModeBar': False})

# ==================== SECTION: 품목 분석 ====================
st.subheader("📦 9. 고객군별 품목 주문 분석")
st.markdown("### 탭을 선택하여 고객군별 품목 현황을 확인하세요")

tab_new, tab_return, tab_churn = st.tabs(['신규 고객', '재이용 고객', '이탈 위험 고객'])

product_tabs = {
    '신규 고객': tab_new,
    '재이용 고객': tab_return,
    '이탈 위험 고객': tab_churn
}

for group_name, tab in product_tabs.items():
    with tab:
        group_product = product_df[product_df['고객군'] == group_name]
        if len(group_product) > 0:
            st.markdown(f"### {group_name} — 품목 주문 현황")
            st.dataframe(
                group_product[['item_name', '주문_건수', '주문_금액', '비율']].rename(
                    columns={'item_name': '품목', '주문_건수': '주문 건수', '주문_금액': '주문 금액', '비율': '비율'}
                ),
                use_container_width=True, hide_index=True,
                column_config={
                    '주문 금액': st.column_config.NumberColumn(format='₩%,.0f')
                }
            )

            # 상위 품목
            top_product = group_product.loc[group_product['주문_금액'].idxmax()]
            st.markdown(f"<div style='text-align:center; color: #6c5ce7; font-weight: 600; margin-top: 8px; font-size: 0.85rem;'>🏷️ 상위 품목: {top_product['item_name']} ({int(top_product['주문_금액']):,}원)</div>", unsafe_allow_html=True)

            st.divider()
            st.markdown("### 품목명별 주문 건수 & 금액")
            fig_product = go.Figure()
            fig_product.add_trace(go.Bar(
                name='주문 건수',
                x=group_product['item_name'],
                y=group_product['주문_건수'],
                marker_color=region_colors[group_name],
                marker_line_width=0,
                hovertemplate='%{x}: %{y}건<extra></extra>',
                yaxis='y'
            ))
            fig_product.add_trace(go.Scatter(
                name='주문 금액 (원)',
                x=group_product['item_name'],
                y=group_product['주문_금액'],
                mode='lines+markers',
                line=dict(color=region_colors[group_name], width=3),
                marker=dict(size=10, color=region_colors[group_name]),
                hovertemplate='%{x}: ₩%,.0f원<extra></extra>',
                yaxis='y1'
            ))
            fig_product.update_layout(
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e4e6f0'),
                yaxis=dict(title='주문 건수', range=[0, max(group_product['주문_건수']) + 1], tick0=0, dtick=1, side='left'),
                yaxis1=dict(title='주문 금액 (원)', overlaying='y', side='right', tickformat=',d', showgrid=False)
            )
            st.plotly_chart(fig_product, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info(f"{group_name} 품목 데이터가 없습니다.")

# ==================== SECTION: AI 분석 요약 ====================
st.subheader("🤖 10. AI 분석 요약")

if len(ai_summary) > 0:
    for idx, sentence in enumerate(ai_summary, 1):
        st.markdown(f"""
        <div style="
          background: linear-gradient(135deg, #1e1a3a, #1a1d2e);
          border: 1px solid #6c5ce7;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 12px;
          font-size: 0.9rem;
          line-height: 1.8;
        ">
          <span style="
            display: inline-block;
            width: 24px; height: 24px;
            background: #6c5ce7;
            color: #fff;
            border-radius: 50%;
            text-align: center;
            line-height: 24px;
            font-size: 0.7rem;
            font-weight: 700;
            margin-right: 8px;
          ">{idx}</span>
          {sentence}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("AI 분석 요약 데이터가 없습니다.")

# ==================== SECTION: 검증 결과 ====================
st.subheader("✅ 11. 분석 결과 검증 결과")

if len(validation_final_df) > 0:
    st.markdown("### 검증 항목별 결과")
    st.dataframe(
        validation_final_df.rename(columns={'항목': '검증 항목', '상태': '통과/실패', '원인': '원인'}),
        use_container_width=True, hide_index=True
    )

    # KPI
    pass_count = len(validation_final_df[validation_final_df['상태'] == '통과'])
    total_vf = len(validation_final_df)
    fail_count = total_vf - pass_count

    kpi_v1, kpi_v2, kpi_v3 = st.columns(3)
    with kpi_v1:
        st.markdown(f"""
        <div class="metric-card kpi-total">
          <div class="kpi-label">검증 항목 통과</div>
          <div class="kpi-value" style="color: #00b894;">{pass_count}/{total_vf}</div>
          <div class="progress-bar-container">
            <div class="progress-fill" style="width: {pass_count/total_vf*100}%; background-color: #00b894;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_v2:
        st.markdown(f"""
        <div class="metric-card kpi-new">
          <div class="kpi-label">검증 실패 항목</div>
          <div class="kpi-value" style="color: #e17055;">{fail_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_v3:
        st.markdown(f"""
        <div class="metric-card kpi-returning">
          <div class="kpi-label">데이터 무결성</div>
          <div class="kpi-value" style="color: #00b894;">{'ALL PASS ✅' if fail_count == 0 else 'CHECK NEEDED'}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("검증 결과 데이터를 찾을 수 없습니다.")

# ==================== 푸터 ====================
st.divider()
st.caption(f"""
📅 대시보드 갱신 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
💡 데이터가 갱신되려면 `customer-analysis-orchestrator` 를 실행해주세요.<br>
🔄 대시보드는 접속 시마다 최신 CSV 데이터를 자동으로 읽어옵니다 (캐시 TTL: 60초).
""", unsafe_allow_html=True)
