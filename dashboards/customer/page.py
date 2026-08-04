"""고객분석 메인 및 고객군 상세 화면."""

from html import escape
from pathlib import Path
from math import cos, radians

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
from streamlit_plotly_events import plotly_events


OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "output"
GROUPS = ["신규 고객", "재이용 고객", "이탈 위험 고객", "일반 고객"]
COLORS = ["#00b894", "#00cec9", "#e17055", "#a29bfe"]
REGION_COORDINATES = {
    "애월읍": (33.462, 126.329), "한림읍": (33.410, 126.267),
    "조천읍": (33.542, 126.642), "구좌읍": (33.522, 126.853),
    "성산읍": (33.448, 126.910), "표선면": (33.326, 126.832),
    "남원읍": (33.279, 126.720), "대정읍": (33.226, 126.252),
    "안덕면": (33.257, 126.330), "한경면": (33.350, 126.185),
    "연동": (33.489, 126.497), "노형동": (33.483, 126.477),
    "중문동": (33.251, 126.413), "서귀동": (33.247, 126.561),
    "동홍동": (33.258, 126.568), "서홍동": (33.255, 126.551),
    "법환동": (33.237, 126.515), "보목동": (33.241, 126.601),
    "하효동": (33.254, 126.621), "외도일동": (33.493, 126.430),
    "이도이동": (33.496, 126.535), "아라일동": (33.476, 126.545),
}

# 제주 본섬의 간략 경계. 지도 격자를 섬 안쪽에만 표시하기 위해 사용한다.
JEJU_BOUNDARY = [
    (126.145, 33.305), (126.165, 33.365), (126.225, 33.425),
    (126.315, 33.475), (126.435, 33.515), (126.575, 33.545),
    (126.720, 33.555), (126.840, 33.530), (126.930, 33.480),
    (126.965, 33.415), (126.925, 33.335), (126.835, 33.265),
    (126.710, 33.225), (126.565, 33.215), (126.445, 33.225),
    (126.335, 33.205), (126.235, 33.225), (126.170, 33.260),
]
@st.cache_data(ttl=60)
def load_csv(filename, columns=None):
    try:
        return pd.read_csv(OUTPUT_DIR / filename)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=columns or [])


@st.cache_data(ttl=60)
def load_text(filename):
    try:
        return [line.strip() for line in (OUTPUT_DIR / filename).read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError:
        return []


def load_data():
    metrics = load_csv("customer_metrics.csv", ["customer_id", "주문 횟수", "누적 배송 수량"])
    if "누적 배송 수량" in metrics.columns:
        metrics["누적 배송 수량"] = pd.to_numeric(metrics["누적 배송 수량"], errors="coerce").fillna(0)
    groups = load_csv(
        "customer_groups.csv",
        ["customer_id", "고객군", "이탈 분석 대상 여부", "이탈 위험 등급"],
    )
    return {
        "metrics": metrics,
        "groups": groups,
        "validation": load_csv("validation_results.csv"),
        "invalid": load_csv("invalid_records.csv"),
        "ai_summary": load_text("ai_summary.txt"),
        "merged": load_csv("merged_data.csv"),
        "churn": load_csv("churn_scores.csv"),
        "region": load_csv("region_analysis.csv"),
        "industry": load_csv("industry_analysis.csv"),
        "product": load_csv("product_analysis.csv"),
    }


def build_period_data(data, start_date, end_date):
    """선택 기간의 활동 고객을 종료일 기준으로 다시 분류한다."""
    scoped = dict(data)
    merged = data["merged"].copy()
    if merged.empty or "order_date_parsed" not in merged.columns:
        return scoped

    merged["order_date_parsed"] = pd.to_datetime(merged["order_date_parsed"], errors="coerce")
    start = pd.Timestamp(start_date).normalize()
    end_exclusive = pd.Timestamp(end_date).normalize() + pd.Timedelta(days=1)
    period_rows = merged[merged["order_date_parsed"].between(start, end_exclusive, inclusive="left")].copy()
    history = merged[merged["order_date_parsed"] < end_exclusive].copy()
    valid_customers = set(data["groups"].get("customer_id", pd.Series(dtype=str)).astype(str))
    active_ids = set(period_rows.get("customer_id", pd.Series(dtype=str)).astype(str)) & valid_customers

    metric_rows = []
    group_rows = []
    for customer_id in sorted(active_ids):
        customer_history = history[history["customer_id"].astype(str) == customer_id].copy()
        events = pd.Series(customer_history["order_date_parsed"].dropna().unique()).sort_values().reset_index(drop=True)
        if events.empty:
            continue
        order_count = len(events)
        first_order = events.iloc[0]
        recent_order = events.iloc[-1]
        days_since = max((pd.Timestamp(end_date).normalize() - recent_order.normalize()).days, 0)
        avg_cycle = None
        if order_count >= 3:
            avg_cycle = round((events.diff().dropna().dt.total_seconds() / 86_400).mean(), 1)

        if order_count == 1:
            eligible, grade, ratio = "아니오", "판정 제외", None
        elif order_count == 2 or not avg_cycle or avg_cycle <= 0:
            eligible, grade, ratio = "아니오", "판정 보류", None
        else:
            eligible = "예"
            ratio = days_since / avg_cycle
            grade = "정상" if ratio <= 1 else ("주의" if ratio <= 1.5 else "위험")

        ratio_text = f"{ratio:.2f}배" if ratio is not None else "계산 불가"
        cycle_text = f"{avg_cycle:.1f}일" if avg_cycle is not None else "계산 불가"
        reason = (
            f"주문 {order_count}회, 평균 이용 주기 {cycle_text}, 최종 주문 후 {days_since}일 경과, "
            f"평균 주기 대비 {ratio_text}"
        )
        if first_order >= start:
            group = "신규 고객"
        elif grade in ["주의", "위험"]:
            group = "이탈 위험 고객"
        elif order_count >= 2:
            group = "재이용 고객"
        else:
            group = "일반 고객"

        period_customer_rows = period_rows[period_rows["customer_id"].astype(str) == customer_id]
        total_quantity = pd.to_numeric(period_customer_rows.get("order_quantity_num"), errors="coerce").sum()
        metric_rows.append({
            "customer_id": customer_id,
            "최근 주문일": recent_order.strftime("%Y-%m-%d"),
            "주문 횟수": order_count,
            "평균 이용 주기": cycle_text,
            "_avg_cycle_raw": avg_cycle,
            "최종 주문 후 경과일": days_since,
            "누적 배송 수량": total_quantity,
        })
        group_rows.append({
            "customer_id": customer_id,
            "고객군": group,
            "전체 주문 횟수": order_count,
            "최근 주문일": recent_order.strftime("%Y-%m-%d"),
            "평균 이용 주기": cycle_text,
            "최종 주문 후 경과일": days_since,
            "평균 주기 대비 경과 비율": ratio_text,
            "이탈 분석 대상 여부": eligible,
            "이탈 위험 등급": grade,
            "판단 근거": reason,
        })

    groups = pd.DataFrame(group_rows, columns=[
        "customer_id", "고객군", "전체 주문 횟수", "최근 주문일", "평균 이용 주기",
        "최종 주문 후 경과일", "평균 주기 대비 경과 비율", "이탈 분석 대상 여부",
        "이탈 위험 등급", "판단 근거",
    ])
    metrics = pd.DataFrame(metric_rows, columns=[
        "customer_id", "최근 주문일", "주문 횟수", "평균 이용 주기", "_avg_cycle_raw",
        "최종 주문 후 경과일", "누적 배송 수량",
    ])
    period_rows = period_rows[period_rows["customer_id"].astype(str).isin(active_ids)].copy()
    if not period_rows.empty and not groups.empty:
        product = period_rows.merge(groups[["customer_id", "고객군"]], on="customer_id", how="left")
        product = product.groupby(["고객군", "item_name"], as_index=False).agg(
            주문_건수=("order_id", "count"),
            배송_수량=("order_quantity_num", lambda values: pd.to_numeric(values, errors="coerce").sum()),
        )
        product["비율"] = product.groupby("고객군")["주문_건수"].transform(lambda values: (values / values.sum() * 100).round(1))
    else:
        product = pd.DataFrame(columns=["고객군", "item_name", "주문_건수", "배송_수량", "비율"])

    scoped.update({"merged": period_rows, "metrics": metrics, "groups": groups, "churn": groups.copy(), "product": product})
    return scoped


def render_period_filter(merged):
    """홈 대시보드의 전체·월·주·직접설정 조회기간 선택기."""
    dates = pd.to_datetime(merged.get("order_date_parsed"), errors="coerce").dropna()
    if dates.empty:
        return None, None
    minimum, maximum = dates.min().normalize(), dates.max().normalize()
    mode = st.radio("조회 단위", ["전체", "월간", "주간", "직접 설정"], horizontal=True, key="home_period_mode")

    if mode == "월간":
        months = list(pd.period_range(minimum, maximum, freq="M"))[::-1]
        selected = st.selectbox("조회 월", months, format_func=lambda value: f"{value.year}년 {value.month}월")
        start, end = selected.start_time.normalize(), min(selected.end_time.normalize(), maximum)
    elif mode == "주간":
        first_monday = minimum - pd.Timedelta(days=minimum.weekday())
        weeks = list(pd.date_range(first_monday, maximum, freq="7D"))[::-1]
        selected = st.selectbox(
            "조회 주",
            weeks,
            format_func=lambda value: f"{value:%Y.%m.%d} ~ {min(value + pd.Timedelta(days=6), maximum):%Y.%m.%d}",
        )
        start, end = max(selected, minimum), min(selected + pd.Timedelta(days=6), maximum)
    elif mode == "직접 설정":
        selected = st.date_input(
            "조회 기간",
            value=(minimum.date(), maximum.date()),
            min_value=minimum.date(),
            max_value=maximum.date(),
        )
        if not isinstance(selected, (tuple, list)) or len(selected) != 2:
            st.info("시작일과 종료일을 모두 선택해주세요.")
            return minimum, maximum
        start, end = pd.Timestamp(selected[0]), pd.Timestamp(selected[1])
    else:
        start, end = minimum, maximum

    st.caption(f"조회 기간: {start:%Y-%m-%d} ~ {end:%Y-%m-%d} · 이 기간에 활동한 고객을 {end:%Y-%m-%d} 기준으로 분석합니다.")
    return start, end


def style_chart(fig, theme):
    fig.update_layout(
        template=theme["plotly_template"],
        paper_bgcolor=theme["bg"],
        plot_bgcolor=theme["card"],
        font_color=theme["text"],
    )
    return fig


def show_dataframe(dataframe, theme):
    """Streamlit 기본 테마와 무관하게 표를 현재 앱 테마로 표시한다."""
    styled = dataframe.style.set_properties(**{
        "background-color": theme["card"],
        "color": theme["text"],
        "border-color": theme["border"],
    }).set_table_styles([
        {"selector": "th", "props": [
            ("background-color", theme["sidebar"]),
            ("color", theme["text"]),
            ("border-color", theme["border"]),
        ]},
    ])
    st.dataframe(styled, width="stretch", hide_index=True)


def render_kpi_group(title, subtitle, cards):
    """동일 크기의 2×2 KPI 카드를 의미별 그룹으로 표시한다."""
    card_html = "".join(
        f"""
        <div class="customer-kpi-card {color_class}" data-detail="{escape(detail, quote=True)}" tabindex="0">
          <div class="customer-kpi-label">{label}</div>
          <div class="customer-kpi-value">{value}</div>
          <div class="customer-kpi-basis">{basis}</div>
        </div>
        """
        for label, value, color_class, basis, detail in cards
    )
    st.markdown(
        f"""
        <section class="customer-kpi-group">
          <h4 class="customer-kpi-group-title">{title}</h4>
          <p class="customer-kpi-group-subtitle">{subtitle}</p>
          <div class="customer-kpi-grid">{card_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_note(summary, detail):
    """분석 기준 요약과 마우스 오버 상세 설명을 표시한다."""
    st.markdown(
        f"""
        <div class="analysis-note" tabindex="0" data-detail="{escape(detail, quote=True)}">
          <span>{summary}</span><span class="analysis-note-icon">ⓘ</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _is_inside_jeju(longitude, latitude):
    """점이 제주 경계 다각형 안에 있는지 확인한다."""
    inside = False
    previous = JEJU_BOUNDARY[-1]
    for current in JEJU_BOUNDARY:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > latitude) != (y2 > latitude):
            crossing = (x2 - x1) * (latitude - y1) / (y2 - y1) + x1
            if longitude < crossing:
                inside = not inside
        previous = current
    return inside


def _grid_color(count, maximum, dark_mode):
    if count == 0:
        return [62, 67, 83, 70] if dark_mode else [224, 229, 238, 115]
    # 한두 건의 차이도 보이도록 제곱근 비율을 사용한 단일 보라색 계열 그라데이션.
    ratio = (count / max(maximum, 1)) ** 0.5
    light_color = (221, 210, 255)
    dark_color = (91, 33, 182)
    red = round(light_color[0] + (dark_color[0] - light_color[0]) * ratio)
    green = round(light_color[1] + (dark_color[1] - light_color[1]) * ratio)
    blue = round(light_color[2] + (dark_color[2] - light_color[2]) * ratio)
    alpha = round(155 + 95 * ratio)
    return [red, green, blue, alpha]


def render_shipping_grid(shipment_data, theme, location_type):
    """제주 본섬을 작은 동일 크기 격자로 채우고 배송 건수를 표시한다."""
    prefix = "origin" if location_type in ["발송지", "수거주소"] else "destination"
    latitude_column = f"{prefix}_latitude"
    longitude_column = f"{prefix}_longitude"
    region_column = f"{prefix}_region"
    if latitude_column in shipment_data.columns and longitude_column in shipment_data.columns:
        map_data = shipment_data[[latitude_column, longitude_column]].copy()
    elif region_column in shipment_data.columns:
        map_data = shipment_data[[region_column]].copy()
        coordinates = map_data[region_column].map(REGION_COORDINATES)
        map_data[latitude_column] = coordinates.map(lambda value: value[0] if isinstance(value, tuple) else None)
        map_data[longitude_column] = coordinates.map(lambda value: value[1] if isinstance(value, tuple) else None)
        coverage = map_data[latitude_column].notna().mean() * 100
        st.caption(f"주소에서 읍·면·동을 확인할 수 있는 {coverage:.1f}%의 배송만 지도에 포함됩니다.")
    else:
        st.info("수거·배송 주소 지역 데이터가 없습니다.")
        return
    map_data[latitude_column] = pd.to_numeric(map_data[latitude_column], errors="coerce")
    map_data[longitude_column] = pd.to_numeric(map_data[longitude_column], errors="coerce")
    map_data = map_data.dropna()
    if map_data.empty:
        st.info(f"지도에 표시할 {location_type} 데이터가 없습니다.")
        return

    cell_km = 1.5
    latitude_step = cell_km / 111.0
    longitude_step = cell_km / (111.0 * cos(radians(33.38)))
    min_longitude = min(point[0] for point in JEJU_BOUNDARY)
    max_longitude = max(point[0] for point in JEJU_BOUNDARY)
    min_latitude = min(point[1] for point in JEJU_BOUNDARY)
    max_latitude = max(point[1] for point in JEJU_BOUNDARY)

    counts = {}
    for row in map_data[[latitude_column, longitude_column]].itertuples(index=False, name=None):
        latitude, longitude = row
        column = int((longitude - min_longitude) / longitude_step)
        line = int((latitude - min_latitude) / latitude_step)
        counts[(column, line)] = counts.get((column, line), 0) + 1

    grid = []
    column_count = int((max_longitude - min_longitude) / longitude_step) + 1
    line_count = int((max_latitude - min_latitude) / latitude_step) + 1
    for column in range(column_count):
        west = min_longitude + column * longitude_step
        east = west + longitude_step
        for line in range(line_count):
            south = min_latitude + line * latitude_step
            north = south + latitude_step
            if not _is_inside_jeju((west + east) / 2, (south + north) / 2):
                continue
            grid.append({
                "polygon": [[west, south], [east, south], [east, north], [west, north]],
                "count": counts.get((column, line), 0),
            })

    maximum = max((cell["count"] for cell in grid), default=0)
    dark_mode = theme["plotly_template"] != "plotly_white"
    for cell in grid:
        cell["fill_color"] = _grid_color(cell["count"], maximum, dark_mode)

    layer = pdk.Layer(
        "PolygonLayer",
        data=grid,
        get_polygon="polygon",
        get_fill_color="fill_color",
        get_line_color=[105, 112, 135, 150] if dark_mode else [255, 255, 255, 210],
        line_width_min_pixels=0.45,
        stroked=True,
        filled=True,
        pickable=True,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=33.38, longitude=126.55, zoom=8.7, pitch=0),
        map_style="light" if theme["plotly_template"] == "plotly_white" else "dark",
        tooltip={"html": f"<b>{location_type} 격자</b><br/>배송 건수: {{count}}건"},
    )
    st.pydeck_chart(deck, width="stretch", height=460)


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
    detail_shipments = filter_customers(data["merged"])
    detail_product = filter_group(data["product"])
    if "주문_건수" in detail_product.columns:
        detail_product = detail_product.sort_values("주문_건수", ascending=False)

    destination_summary = pd.DataFrame()
    channel_summary = pd.DataFrame()
    if len(detail_shipments):
        shipment_analysis = detail_shipments.copy()
        shipment_analysis["배송 수량"] = pd.to_numeric(
            shipment_analysis.get("order_quantity_num"), errors="coerce"
        ).fillna(0)

        if "destination_region" in shipment_analysis.columns:
            known_destination = shipment_analysis[
                shipment_analysis["destination_region"].notna()
                & (shipment_analysis["destination_region"] != "미상")
            ]
            if len(known_destination):
                destination_summary = (
                    known_destination.groupby("destination_region", as_index=False)
                    .agg(
                        배송_건수=("order_id", "count"),
                        고객_수=("customer_id", "nunique"),
                        배송_수량=("배송 수량", "sum"),
                    )
                    .sort_values("배송_건수", ascending=False)
                )

        if "order_channel" in shipment_analysis.columns:
            channel_data = shipment_analysis.copy()
            channel_data["order_channel"] = channel_data["order_channel"].fillna("미상")
            channel_summary = (
                channel_data.groupby("order_channel", as_index=False)
                .agg(
                    배송_건수=("order_id", "count"),
                    고객_수=("customer_id", "nunique"),
                    배송_수량=("배송 수량", "sum"),
                )
                .sort_values("배송_건수", ascending=False)
            )

    st.title(f"📋 {group_name} 상세 분석")
    st.caption("선택한 고객군의 배송 지역·접수형태·품목 특성과 고객별 지표를 보여줍니다.")
    st.divider()

    risk_count = len(detail[detail["이탈 위험 등급"].isin(["주의", "위험"])]) if "이탈 위험 등급" in detail.columns else 0
    avg_orders = pd.to_numeric(detail_metrics.get("주문 횟수"), errors="coerce").mean() if len(detail_metrics) else 0
    avg_quantity = pd.to_numeric(detail_metrics.get("누적 배송 수량"), errors="coerce").mean() if len(detail_metrics) else 0
    cols = st.columns(4)
    cols[0].metric("고객 수", f"{len(detail)}명")
    cols[1].metric("이탈 주의·위험", f"{risk_count}명")
    cols[2].metric("평균 주문 횟수", f"{avg_orders:.1f}회")
    cols[3].metric("평균 누적 배송 수량", f"{avg_quantity:,.1f}개")

    analysis_tab, churn_tab, profile_tab = st.tabs([
        "📊 고객군 분석", "⚠️ 이탈 위험", "👥 고객 프로필"
    ])
    with analysis_tab:
        render_analysis_note(
            "선택한 고객군의 지역·접수형태·배송 위치·품목 특성을 분석합니다.",
            "지역, B2B·B2C 접수형태, 품목은 실제 배송 행을 기준으로 배송 건수와 수량을 집계합니다. 고객 주문 횟수와 재이용 주기는 같은 접수 시간의 대량 배송을 한 번의 주문으로 계산합니다.",
        )

        region_col, channel_col = st.columns(2, gap="large")
        with region_col:
            st.markdown("#### 배송 목적지 지역")
            render_analysis_note(
                "주소가 확인된 배송 건수를 목적지 읍·면·동별로 비교합니다.",
                "고객 거주지가 아니라 배송 목적지 주소에서 제주 읍·면·동을 추출한 결과입니다. 지역을 확인할 수 없는 배송은 이 순위에서 제외하며, 막대는 배송 건수가 많은 순서로 표시합니다.",
            )
            if len(destination_summary):
                fig = px.bar(
                    destination_summary,
                    x="destination_region",
                    y="배송_건수",
                    title=f"{group_name} 배송 목적지 분포",
                )
                fig.update_xaxes(categoryorder="total descending", title="배송 목적지")
                st.plotly_chart(style_chart(fig, theme), width="stretch")
                show_dataframe(destination_summary, theme)
            else:
                st.info("확인 가능한 배송 목적지 지역 데이터가 없습니다.")

        with channel_col:
            st.markdown("#### B2B·B2C 접수형태")
            render_analysis_note(
                "접수형태별 실제 배송 건수를 비교합니다.",
                "B2B 엑셀일괄과 B2C 직접접수를 실제 배송 행으로 구분합니다. 한 번의 B2B 접수에서 여러 배송지가 생성되면 각 배송을 배송 건수에 포함합니다.",
            )
            if len(channel_summary):
                fig = px.bar(
                    channel_summary,
                    x="order_channel",
                    y="배송_건수",
                    title=f"{group_name} B2B·B2C 배송 비중",
                )
                fig.update_xaxes(categoryorder="total descending", title="접수형태")
                st.plotly_chart(style_chart(fig, theme), width="stretch")
                show_dataframe(channel_summary, theme)
            else:
                st.info("접수형태 데이터가 없습니다.")

        st.markdown("#### 수거지·배송지 격자 밀도")
        if len(detail_shipments):
            location_type = st.radio(
                "주소 기준",
                options=["배송주소", "수거주소"],
                horizontal=True,
                key=f"shipping_location_{group_name}",
            )
            render_analysis_note(
                "제주도를 동일 면적 격자로 나눠 배송 밀도를 비교합니다.",
                "배송주소는 물품을 받는 주소, 수거주소는 물류 수거·출발 주소를 사용합니다. 약 1.5km × 1.5km 격자에서 선택 고객군의 배송 건수가 많을수록 보라색이 진해집니다.",
            )
            render_shipping_grid(detail_shipments, theme, location_type)
        else:
            st.info("배송 위치 데이터가 없습니다.")

        st.markdown("#### 품목명 분석")
        if len(detail_product):
            render_analysis_note(
                "품목별 배송 건수와 배송 수량을 많은 순서로 비교합니다.",
                "선택 고객군의 실제 배송 행을 품목명으로 묶습니다. 그래프는 가독성을 위해 배송 건수 상위 15개 품목을 보여주며, 아래 표에서 전체 품목 집계를 확인할 수 있습니다.",
            )
            chart_data = detail_product.sort_values("주문_건수", ascending=False).head(15)
            fig = px.bar(
                chart_data,
                x="item_name",
                y="주문_건수",
                title=f"{group_name} 배송 건수 상위 품목",
            )
            fig.update_xaxes(categoryorder="total descending", title="품목명")
            st.plotly_chart(style_chart(fig, theme), width="stretch")
            show_dataframe(detail_product, theme)
        else:
            st.info("품목 분석 데이터가 없습니다.")

    with churn_tab:
        render_analysis_note(
            "전체 주문 3회 이상인 고객만 이탈 위험을 분석합니다.",
            "여기서 주문 횟수는 배송 행 수가 아니라 고객별 고유 주문 접수 시간 수입니다. 주문 1회는 판정 제외, 2회는 판정 보류이며, 3회 이상은 최종 주문 후 경과일÷평균 이용 주기로 정상·주의·위험을 판정합니다.",
        )
        if len(detail_churn):
            churn_columns = [
                "customer_id", "전체 주문 횟수", "최근 주문일", "평균 이용 주기",
                "최종 주문 후 경과일", "평균 주기 대비 경과 비율",
                "이탈 위험 등급", "판단 근거",
            ]
            churn_table = detail_churn[[column for column in churn_columns if column in detail_churn.columns]].copy()
            churn_table = churn_table.rename(columns={"customer_id": "고객 ID"})
            show_dataframe(churn_table, theme)
        else:
            st.info("이 고객군에는 이탈 분석 데이터가 없습니다.")
    with profile_tab:
        render_analysis_note(
            "선택한 고객군의 분류 결과와 누적 이용 지표입니다.",
            "배송 건수와 배송 수량은 실제 배송 행을 모두 집계합니다. 고객 주문 횟수와 재이용 주기는 고객별 고유 주문 접수 시간을 기준으로 계산하며, 한 고객에게는 하나의 고객군만 부여합니다.",
        )
        show_dataframe(detail, theme)
        if len(detail_metrics):
            st.markdown("#### 고객별 이용 지표")
            show_dataframe(detail_metrics, theme)


def render_main(data, theme):
    st.title("🏢 잇뉴 고객 분석 대시보드")
    st.caption("고객군별 현황과 기업 핵심 목표를 한눈에 확인합니다.")
    start_date, end_date = render_period_filter(data["merged"])
    if start_date is not None and end_date is not None:
        st.query_params["start"] = pd.Timestamp(start_date).strftime("%Y-%m-%d")
        st.query_params["end"] = pd.Timestamp(end_date).strftime("%Y-%m-%d")
        source_dates = pd.to_datetime(data["merged"].get("order_date_parsed"), errors="coerce").dropna()
        is_full_range = (
            not source_dates.empty
            and pd.Timestamp(start_date).normalize() == source_dates.min().normalize()
            and pd.Timestamp(end_date).normalize() == source_dates.max().normalize()
        )
        if not is_full_range:
            data = build_period_data(data, start_date, end_date)
    st.divider()

    groups = data["groups"]
    metrics = data["metrics"]
    validation = data["validation"]
    merged = data["merged"]
    counts = [(groups["고객군"] == group).sum() for group in GROUPS]
    total_customers = len(groups)
    total_deliveries = len(merged)
    total_quantity = pd.to_numeric(merged.get("order_quantity_num"), errors="coerce").sum() if len(merged) else 0
    avg_orders = pd.to_numeric(metrics.get("주문 횟수"), errors="coerce").mean() if len(metrics) else 0
    avg_customer_deliveries = total_deliveries / total_customers if total_customers else 0
    new_count = counts[0]
    returning_rate = counts[1] / total_customers * 100 if total_customers else 0
    eligible_count = (groups.get("이탈 분석 대상 여부") == "예").sum() if "이탈 분석 대상 여부" in groups.columns else 0
    normal_count = (groups.get("이탈 위험 등급") == "정상").sum() if "이탈 위험 등급" in groups.columns else 0
    caution_count = (groups.get("이탈 위험 등급") == "주의").sum() if "이탈 위험 등급" in groups.columns else 0
    danger_count = (groups.get("이탈 위험 등급") == "위험").sum() if "이탈 위험 등급" in groups.columns else 0
    churn_rate = danger_count / eligible_count * 100 if eligible_count else 0
    cycle_values = pd.to_numeric(metrics.get("_avg_cycle_raw"), errors="coerce").dropna() if len(metrics) else pd.Series(dtype=float)
    avg_cycle = cycle_values.mean() if len(cycle_values) else 0

    analysis_date = pd.to_datetime(merged.get("order_date_parsed"), errors="coerce").max() if len(merged) else pd.NaT
    if len(merged) and "order_date_parsed" in merged.columns:
        order_dates = pd.to_datetime(merged["order_date_parsed"], errors="coerce")
        monthly_mask = order_dates.between(analysis_date.replace(day=1), analysis_date)
        monthly_data = merged[monthly_mask].copy()
        mau = monthly_data["customer_id"].nunique()
        monthly_deliveries = len(monthly_data)
    else:
        mau = 0
        monthly_deliveries = 0

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<p class="section-title">👥 고객군 분포</p>', unsafe_allow_html=True)
        render_analysis_note(
            "최초 주문일·주문 횟수·이탈 등급으로 고객군을 구분합니다.",
            "신규 고객은 조회 기간 내 첫 주문 고객, 재이용 고객은 주문 2회 이상인 기존 고객입니다. 주문 3회 이상 분석 대상 중 주의·위험 등급은 이탈 위험 고객으로 우선 분류하고, 나머지 기존 단발 고객은 일반 고객으로 분류합니다.",
        )
        fig = go.Figure(go.Pie(
            labels=GROUPS,
            values=counts,
            hole=0,
            marker_colors=COLORS,
            textinfo="none",
            texttemplate=(
                "<span style='font-size:18px'><b>%{percent}</b></span>"
                "<br><b>%{label}</b><br><span style='font-size:11px'>(%{value}명)</span>"
            ),
            textposition="inside",
            insidetextfont=dict(color="#ffffff", size=13),
            outsidetextfont=dict(color="#ffffff", size=13),
            hovertemplate="%{label}<br>%{value}명 (%{percent})<extra></extra>",
        ))
        fig.update_traces(
            marker_line_width=2,
            marker_line_color=theme["bg"],
            domain=dict(x=[0.02, 0.98], y=[0.16, 0.98]),
        )
        fig.update_layout(
            template=theme["plotly_template"],
            paper_bgcolor=theme["bg"],
            plot_bgcolor=theme["bg"],
            font_color=theme["text"],
            height=620,
            autosize=True,
            margin=dict(l=0, r=0, t=0, b=8),
            legend=dict(
                orientation="h", y=0.01, x=.5, xanchor="center", yanchor="bottom",
                bgcolor="rgba(0,0,0,0)",
            ),
            uniformtext_minsize=11,
            uniformtext_mode="hide",
        )
        points = plotly_events(fig, click_event=True, select_event=False, hover_event=False, override_height=620, key="customer_group_chart")
        if points:
            point_number = points[0].get("pointNumber")
            if isinstance(point_number, int) and 0 <= point_number < len(GROUPS):
                st.query_params["group"] = GROUPS[point_number]
                st.rerun()
        st.caption("💡 원 그래프 조각을 클릭하면 고객군 상세 화면으로 이동합니다.")
        st.markdown(
            """
            <div class="classification-criteria">
              <div class="classification-criteria-title">고객군 분류 기준</div>
              <div><b>신규</b> 최신 분석 월에 최초 주문 · <b>일반</b> 기존 고객 중 고유 주문 접수 1회</div>
              <div><b>재이용</b> 기존 고객 중 고유 주문 접수 2회 이상 · <b>이탈 위험</b> 이탈 등급이 주의 또는 위험</div>
              <div class="classification-grade-title">이탈 등급 기준 <span>※ 고유 주문 접수 3회 이상 고객만 분석</span></div>
              <div><b>정상</b> 경과일 ≤ 평균 주기 · <b>주의</b> 평균 주기 &lt; 경과일 ≤ 평균 주기 × 1.5</div>
              <div><b>위험</b> 경과일 &gt; 평균 주기 × 1.5 · <b>판정 제외</b> 고유 접수 1회</div>
              <div><b>판정 보류</b> 고유 접수 2회 또는 평균 이용 주기 계산 불가</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        render_kpi_group(
            "📊 고객 규모",
            "현재 고객 규모와 매출 현황을 보여주는 핵심 지표입니다.",
            [
                ("🚚 총 배송 건수", f"{total_deliveries:,}건", "gradient-blue-purple", "실제 배송 주문 행 기준", "2026년 1~6월 실제 배송 주문 데이터의 전체 행 수입니다."),
                ("👥 전체 고객", f"{total_customers:,}명", "gradient-navy-indigo", "고유 고객 ID 기준", "고객 분류 결과에 포함된 중복 없는 customer_id 수입니다."),
                ("📦 총 배송 수량", f"{total_quantity:,.0f}개", "gradient-indigo-purple", "배송물품 수량 합계", "실제 주문 데이터의 수량 컬럼을 모두 합산한 값입니다."),
                ("✨ 신규 고객", f"{new_count:,}명", "gradient-teal-mint", "조회 기간 내 최초 주문", "고객의 전체 주문 이력 중 최초 주문일이 사용자가 선택한 조회 기간 안에 있는 고객 수입니다."),
            ],
        )
        render_kpi_group(
            "📈 고객 이용 패턴",
            "고객의 재이용 패턴과 이탈 위험을 보여주는 분석 지표입니다.",
            [
                ("🔄 고객당 평균 배송", f"{avg_customer_deliveries:.1f}건", "gradient-cyan-blue", "총 배송 건수 ÷ 주문 고객", "전체 실제 배송 건수를 배송 주문 이력이 있는 고유 고객 수로 나눈 값입니다."),
                ("📈 재이용 고객 비율", f"{returning_rate:.1f}%", "gradient-teal-green", "재이용 고객 ÷ 전체 고객", "재이용 고객군 고객 수를 전체 분류 고객 수로 나누고 100을 곱한 비율입니다."),
                ("⏱ 평균 재이용 주기", f"{avg_cycle:.1f}일", "gradient-blue-cyan", "고유 접수 3회 이상 기준", "같은 접수 시간의 B2B 배송 행은 한 번으로 묶고, 고객별 고유 주문 접수 시간 사이의 평균 간격을 계산한 값입니다."),
                ("⚠️ 이탈 위험 고객 비율", f"{churn_rate:.1f}%", "gradient-orange-red", "위험 고객 ÷ 이탈 분석 대상", "위험 등급 고객 수를 주문 3회 이상인 이탈 분석 대상 고객 수로 나누고 100을 곱한 비율입니다."),
            ],
        )
        render_analysis_note(
            "배송량과 재이용 분석은 서로 다른 집계 단위를 사용합니다.",
            "B2B 엑셀일괄 접수는 같은 주문 접수 시간에 배송 행이 수백 건 생성될 수 있습니다. 따라서 배송 KPI·품목 분석은 13,152개 실제 배송 행을 모두 집계하고, 고객 주문 횟수·평균 재이용 주기·이탈 분석은 고객별 고유 주문 접수 시간만 한 번씩 집계합니다. 이를 통해 일괄 배송을 수백 번의 재주문으로 잘못 계산하는 것을 방지합니다.",
        )

    st.divider()
    st.markdown("## ⚠️ 이탈 위험 분석 현황")
    st.caption("전체 주문이 3회 이상인 고객만 이탈 위험 분석 대상으로 계산합니다.")
    render_analysis_note(
        "평균 이용 주기와 최종 주문 후 경과일을 비교한 결과입니다.",
        "평균 이용 주기는 고객별 고유 주문 접수 시간을 시간순으로 정렬한 뒤 인접 접수 간격을 평균한 값입니다. B2B 일괄접수의 같은 시간 배송 행은 한 번으로 계산합니다. 경과일이 평균 주기 이하면 정상, 1~1.5배는 주의, 1.5배 초과는 위험이며 위험률은 위험 고객÷분석 대상 고객×100입니다.",
    )
    churn_columns = st.columns(5)
    churn_columns[0].metric("분석 대상 고객", f"{eligible_count:,}명")
    churn_columns[1].metric("정상 고객", f"{normal_count:,}명")
    churn_columns[2].metric("주의 고객", f"{caution_count:,}명")
    churn_columns[3].metric("위험 고객", f"{danger_count:,}명")
    churn_columns[4].metric("분석 대상 중 위험률", f"{churn_rate:.1f}%")
    st.caption(
        f"위험률 계산: 위험 고객 {danger_count:,}명 ÷ 분석 대상 고객 "
        f"{eligible_count:,}명 × 100 = {churn_rate:.1f}%"
    )

    st.divider()
    st.markdown("## 🎯 기업 목표 KPI")
    st.caption("현재 성과를 기업 목표와 비교하는 관리 지표입니다.")
    render_analysis_note(
        "현재 실적을 사전에 설정한 기업 목표와 비교합니다.",
        "MAU는 최신 분석 월인 2026년 6월 배송 주문 고유 고객 수이며, 월 배송 건수는 같은 달의 실제 주문 행 수입니다. 목표값은 MAU 1,000명, 재이용률 50%, 위험률 10% 이하, 월 배송 3,000건으로 설정되어 있습니다.",
    )
    mau_target = 1_000
    returning_target = 50
    churn_target = 10
    delivery_target = 3_000
    goal_left, goal_right = st.columns(2)
    with goal_left:
        st.markdown("#### 👥 월간 활성 고객 (MAU)")
        st.progress(min(mau / mau_target, 1.0), text=f"{mau:,} / {mau_target:,}명")
        st.markdown("#### 🔄 재이용 고객 비율")
        st.progress(min(returning_rate / returning_target, 1.0), text=f"{returning_rate:.1f}% / 목표 {returning_target}%")
    with goal_right:
        st.markdown("#### ⚠️ 분석 대상 중 위험 고객 비율")
        st.progress(min(churn_rate / churn_target, 1.0), text=f"{churn_rate:.1f}% / 목표 {churn_target}% 이하")
        if churn_rate > churn_target:
            st.warning(f"목표보다 {churn_rate - churn_target:.1f}%p 높습니다.")
        st.markdown("#### 🚚 월 배송 건수")
        st.progress(min(monthly_deliveries / delivery_target, 1.0), text=f"{monthly_deliveries:,}건 / 목표 {delivery_target:,}건")

    st.divider()
    st.markdown("## 🔍 분석 상세 결과")
    render_analysis_note(
        "원본 데이터 품질과 분석 산출물의 정합성을 확인합니다.",
        "데이터 검증은 필수 컬럼·결측·중복·날짜·금액·연결 오류를 확인합니다. 제외 데이터에는 분석에서 제외된 행과 사유를, AI 분석 요약에는 계산 결과에 근거한 핵심 특징을 표시합니다.",
    )
    summary_tab, validation_tab, invalid_tab = st.tabs(["AI 분석 요약", "데이터 검증", "제외 데이터"])
    with summary_tab:
        if data["ai_summary"]:
            for line in data["ai_summary"]:
                st.markdown(f"- {line}")
        else:
            st.info("AI 분석 요약이 없습니다.")
    with validation_tab:
        if len(validation):
            show_dataframe(validation, theme)
        else:
            st.info("데이터 검증 결과가 없습니다.")
    with invalid_tab:
        if len(data["invalid"]):
            show_dataframe(data["invalid"], theme)
        else:
            st.success("제외된 데이터가 없습니다.")


def render(theme):
    data = load_data()
    validation = data["validation"]
    passed = (validation["상태"] == "통과").sum() if "상태" in validation.columns else 0
    result_file = OUTPUT_DIR / "validation_final.csv"
    last_analysis = pd.Timestamp(result_file.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M") if result_file.exists() else "분석 전"
    with st.sidebar:
        st.divider()
        st.markdown("### 🛠 시스템 상태")
        st.caption(f"✅ 데이터 검증 {passed} / {len(validation)}")
        st.caption(f"✅ 마지막 분석: {last_analysis}")
    selected_group = st.query_params.get("group")
    if selected_group in GROUPS:
        try:
            period_start = pd.Timestamp(st.query_params.get("start"))
            period_end = pd.Timestamp(st.query_params.get("end"))
            source_dates = pd.to_datetime(data["merged"].get("order_date_parsed"), errors="coerce").dropna()
            is_full_range = (
                not source_dates.empty
                and period_start.normalize() == source_dates.min().normalize()
                and period_end.normalize() == source_dates.max().normalize()
            )
            if pd.notna(period_start) and pd.notna(period_end) and not is_full_range:
                data = build_period_data(data, period_start, period_end)
        except (TypeError, ValueError):
            pass
        render_detail(selected_group, data, theme)
    else:
        render_main(data, theme)
