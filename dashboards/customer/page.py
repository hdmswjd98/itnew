"""고객분석 메인 및 고객군 상세 화면."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events


OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "output"
GROUPS = ["신규 고객", "재이용 고객", "이탈 위험 고객", "일반 고객"]
COLORS = ["#00b894", "#00cec9", "#e17055", "#a29bfe"]


@st.cache_data(ttl=60)
def load_csv(filename, columns=None):
    try:
        return pd.read_csv(OUTPUT_DIR / filename)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=columns or [])


def load_data():
    metrics = load_csv("customer_metrics.csv", ["customer_id", "주문 횟수", "누적 이용 금액"])
    if "누적 이용 금액" in metrics.columns:
        metrics["누적 이용 금액(원)"] = pd.to_numeric(
            metrics["누적 이용 금액"].astype(str).str.replace(",", "").str.replace("원", ""),
            errors="coerce",
        ).fillna(0)
    groups = load_csv("customer_groups.csv", ["customer_id", "고객군", "이탈 상태"])
    return {
        "metrics": metrics,
        "groups": groups,
        "validation": load_csv("validation_results.csv"),
        "churn": load_csv("churn_risk_customers.csv"),
        "region": load_csv("region_analysis.csv"),
        "industry": load_csv("industry_analysis.csv"),
        "product": load_csv("product_analysis.csv"),
    }


def style_chart(fig, theme):
    fig.update_layout(
        template=theme["plotly_template"],
        paper_bgcolor=theme["bg"],
        plot_bgcolor=theme["card"],
        font_color=theme["text"],
    )
    return fig


def render_detail(group_name, data, theme):
    if st.button("← 전체 현황으로 돌아가기"):
        st.query_params.pop("group", None)
        st.rerun()

    groups = data["groups"]
    metrics = data["metrics"]
    detail = groups[groups["고객군"] == group_name].copy()
    customer_ids = detail["customer_id"] if "customer_id" in detail.columns else []
    detail_metrics = metrics[metrics["customer_id"].isin(customer_ids)].copy()

    def filter_customers(frame):
        if len(frame) == 0 or "customer_id" not in frame.columns:
            return pd.DataFrame()
        return frame[frame["customer_id"].isin(customer_ids)].copy()

    def filter_group(frame):
        if len(frame) == 0 or "고객군" not in frame.columns:
            return pd.DataFrame()
        return frame[frame["고객군"] == group_name].copy()

    detail_churn = filter_customers(data["churn"])
    detail_region = filter_group(data["region"])
    detail_industry = filter_group(data["industry"])
    detail_product = filter_group(data["product"])

    st.title(f"📋 {group_name} 상세 분석")
    st.caption("선택한 고객군의 지표와 지역·업종·품목 특성을 보여줍니다.")
    st.divider()

    risk_count = len(detail[detail["이탈 상태"].isin(["주의", "위험"])]) if "이탈 상태" in detail.columns else 0
    avg_orders = pd.to_numeric(detail_metrics.get("주문 횟수"), errors="coerce").mean() if len(detail_metrics) else 0
    avg_revenue = pd.to_numeric(detail_metrics.get("누적 이용 금액(원)"), errors="coerce").mean() if len(detail_metrics) else 0
    cols = st.columns(4)
    cols[0].metric("고객 수", f"{len(detail)}명")
    cols[1].metric("이탈 주의·위험", f"{risk_count}명")
    cols[2].metric("평균 주문 횟수", f"{avg_orders:.1f}회")
    cols[3].metric("평균 누적 금액", f"{avg_revenue:,.0f}원")

    profile_tab, churn_tab, region_tab, industry_tab, product_tab = st.tabs([
        "📊 고객 프로필", "⚠️ 이탈 위험", "🗺️ 지역", "🏭 업종", "📦 품목"
    ])
    with profile_tab:
        st.dataframe(detail, width="stretch", hide_index=True)
        if len(detail_metrics):
            st.markdown("#### 고객별 이용 지표")
            st.dataframe(detail_metrics, width="stretch", hide_index=True)
    with churn_tab:
        if len(detail_churn):
            st.dataframe(detail_churn, width="stretch", hide_index=True)
        else:
            st.success("이 고객군에는 이탈 위험 고객이 없습니다.")
    with region_tab:
        if len(detail_region):
            fig = px.bar(detail_region, x="region", y="고객 수", title=f"{group_name} 지역 분포")
            st.plotly_chart(style_chart(fig, theme), width="stretch")
            st.dataframe(detail_region, width="stretch", hide_index=True)
        else:
            st.info("지역 분석 데이터가 없습니다.")
    with industry_tab:
        if len(detail_industry):
            fig = px.bar(detail_industry, x="industry", y="고객 수", title=f"{group_name} 업종 분포")
            st.plotly_chart(style_chart(fig, theme), width="stretch")
            st.dataframe(detail_industry, width="stretch", hide_index=True)
        else:
            st.info("업종 분석 데이터가 없습니다.")
    with product_tab:
        if len(detail_product):
            chart_data = detail_product.copy()
            chart_data["주문_금액"] = pd.to_numeric(chart_data["주문_금액"], errors="coerce")
            fig = px.bar(chart_data, x="item_name", y="주문_금액", title=f"{group_name} 품목별 주문 금액")
            st.plotly_chart(style_chart(fig, theme), width="stretch")
            st.dataframe(detail_product, width="stretch", hide_index=True)
        else:
            st.info("품목 분석 데이터가 없습니다.")


def render_main(data, theme):
    groups = data["groups"]
    metrics = data["metrics"]
    validation = data["validation"]
    counts = [(groups["고객군"] == group).sum() for group in GROUPS]
    total_customers = len(groups)
    total_revenue = metrics["누적 이용 금액(원)"].sum() if "누적 이용 금액(원)" in metrics.columns else 0
    avg_orders = pd.to_numeric(metrics.get("주문 횟수"), errors="coerce").mean() if len(metrics) else 0
    passed = (validation["상태"] == "통과").sum() if "상태" in validation.columns else 0

    st.title("🏢 잇뉴 고객 분석 대시보드")
    st.caption("고객군별 현황과 기업 핵심 목표를 한눈에 확인합니다.")
    st.divider()

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<p class="section-title">👥 고객군 분포</p>', unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=GROUPS,
            values=counts,
            hole=.56,
            marker_colors=COLORS,
            textinfo="label+value+percent",
            hovertemplate="%{label}<br>%{value}명 (%{percent})<extra></extra>",
        ))
        fig.update_traces(marker_line_width=2, marker_line_color=theme["bg"])
        fig.update_layout(
            template=theme["plotly_template"],
            paper_bgcolor=theme["bg"],
            plot_bgcolor=theme["bg"],
            font_color=theme["text"],
            height=410,
            margin=dict(l=15, r=15, t=15, b=70),
            legend=dict(orientation="h", y=-.1, x=.5, xanchor="center"),
            annotations=[dict(text=f"{total_customers}명", showarrow=False, font_size=22)],
        )
        points = plotly_events(fig, click_event=True, select_event=False, hover_event=False, override_height=430, key="customer_group_chart")
        if points:
            point_number = points[0].get("pointNumber")
            if isinstance(point_number, int) and 0 <= point_number < len(GROUPS):
                st.query_params["group"] = GROUPS[point_number]
                st.rerun()
        st.caption("💡 원 그래프 조각을 클릭하면 고객군 상세 화면으로 이동합니다.")

    with right:
        st.markdown('<p class="section-title">🎯 기업 달성 목표 (KPI)</p>', unsafe_allow_html=True)
        kpi_columns = st.columns(2)
        kpis = [
            ("전체 고객", f"{total_customers}명", "#6c5ce7"),
            ("총 매출", f"{total_revenue:,.0f}원", "#00b894"),
            ("평균 주문", f"{avg_orders:.1f}회", "#00cec9"),
            ("데이터 검증", f"{passed}/{len(validation)}", "#fdcb6e"),
        ]
        for index, (label, value, color) in enumerate(kpis):
            kpi_columns[index % 2].markdown(
                f'<div class="kpi-card" style="border-top:3px solid {color};margin-bottom:12px">'
                f'<div class="kpi-label">{label}</div><div class="kpi-value" style="color:{color}">{value}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("#### MAU 100만 달성")
        mau = total_customers
        mau_target = 1_000_000
        st.progress(min(mau / mau_target, 1.0), text=f"{mau:,} / {mau_target:,}명")

    st.divider()
    if len(validation):
        st.markdown("### 🔍 데이터 검증 결과")
        st.dataframe(validation, width="stretch", hide_index=True)


def render(theme):
    data = load_data()
    selected_group = st.query_params.get("group")
    if selected_group in GROUPS:
        render_detail(selected_group, data, theme)
    else:
        render_main(data, theme)
