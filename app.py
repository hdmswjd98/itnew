"""
고객 주문 분석 대시보드

실행
    streamlit run app.py

데이터
    1) 앱 화면에서 Excel 파일을 업로드하거나
    2) app.py와 같은 폴더에 data.xlsx 또는 data - 복사본.xlsx를 둔다.

분석 원칙
    - 배송 행: Excel 주문 시트의 한 행. 실제 배송 물량을 나타낸다.
    - 주문회차: 동일 고객 + 동일 주문 접수 시각을 하나의 주문으로 묶은 값.
      엑셀 일괄 접수에서 한 번에 여러 배송을 입력한 경우 재주문 횟수가 과대계산되는 것을 막는다.
    - 재주문 지표는 주문회차 기준으로 계산한다.
    - 외부 폰트/CDN/웹 API를 호출하지 않는다.
"""

from __future__ import annotations

import io
import math
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =============================================================================
# 페이지 설정 및 디자인
# =============================================================================

st.set_page_config(
    page_title="고객 주문 분석",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK = "#F4F6F8"
INK_SOFT = "#A0A6B0"
INK_FAINT = "#747B87"
ORANGE = "#82B5F2"
EMBER = "#5B8FD1"
KRAFT = "#252932"
SHELL = "#0E1117"
LINE = "#2A2D36"
SEA = "#86B9F4"
GREEN = "#6ED28F"
AMBER = "#E6B35C"
RED = "#E06A67"
PURPLE = "#9C8FD8"
BLUE = "#6EA6E8"

SERIES = [SEA, BLUE, PURPLE, GREEN, AMBER, RED, "#C1C7D0", "#7A8290"]
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
TIME_BANDS = ["00–05시", "06–08시", "09–11시", "12–14시", "15–17시", "18–23시"]

SANS = "'Malgun Gothic', 'Apple SD Gothic Neo', -apple-system, BlinkMacSystemFont, sans-serif"
MONO = "'Consolas', 'D2Coding', 'Menlo', ui-monospace, monospace"

st.markdown(
    f"""
<style>
  :root {{ color-scheme: dark; }}
  html, body, [class*="css"] {{ font-family: {SANS}; color: {INK}; }}
  .stApp {{ background: {SHELL}; color: {INK}; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  .block-container {{ max-width: 1540px; padding-top: 1.35rem; padding-bottom: 3rem; }}
  [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}

  h1, h2, h3, h4, h5, h6 {{ color: {INK}; letter-spacing: -.02em; }}
  p, label, span, div, li {{ color: inherit; }}
  [data-testid="stCaptionContainer"] p {{ color: {INK_SOFT} !important; }}

  .pl-subtitle {{
    color: {INK_SOFT};
    margin-top: -.55rem;
    margin-bottom: 1.1rem;
    font-size: .96rem;
  }}
  .pl-note {{
    border-left: 4px solid {INK_FAINT};
    padding: .82rem 1rem;
    background: rgba(128,128,128,.065);
    border-radius: 0 8px 8px 0;
    margin: .35rem 0 1.15rem;
    color: {INK_SOFT};
    font-size: .91rem;
    line-height: 1.55;
  }}
  .pl-note b {{ color: {INK}; }}

  .masthead {{
    background: transparent;
    border: 0;
    border-radius: 0;
    padding: 0;
    margin: 0 0 1rem;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
    box-shadow: none;
  }}
  .masthead h1 {{ margin: 0; font-size: 2rem; font-weight: 800; color: {INK}; }}
  .masthead small {{ display: block; font-family: {MONO}; font-size: .66rem; letter-spacing: .15em; color: {INK_FAINT}; margin-bottom: 7px; }}
  .stamp {{
    font-family: {MONO}; font-size: .72rem; color: {INK_SOFT};
    border: 1px solid rgba(128,128,128,.22);
    background: rgba(128,128,128,.035);
    border-radius: 10px; padding: 9px 12px; text-align: right; min-width: 182px;
  }}
  .stamp b {{ display: block; font-size: .92rem; color: {INK}; margin-top: 2px; }}

  .sec {{ display:flex; align-items:center; gap:10px; margin: 1.9rem 0 .75rem; }}
  .sec::before {{ content:""; width:3px; height:20px; border-radius:2px; background:{SEA}; }}
  .sec h3 {{ margin:0; font-size:1.14rem; font-weight:750; color:{INK}; }}
  .sec i {{ font-family:{MONO}; font-style:normal; color:{INK_FAINT}; font-size:.69rem; letter-spacing:.06em; }}
  .sec::after {{ content:""; flex:1; height:1px; background:rgba(128,128,128,.14); }}

  [data-testid="stMetric"] {{
    border: 1px solid rgba(128,128,128,.24);
    border-radius: 12px;
    padding: 14px 16px;
    min-height: 104px;
    background: rgba(128,128,128,.04);
    box-shadow: none;
  }}
  [data-testid="stMetricLabel"] p {{
    font-size:.79rem !important;
    color:{INK_SOFT} !important;
    letter-spacing:0;
  }}
  [data-testid="stMetricValue"] {{
    font-family:{MONO};
    font-variant-numeric:tabular-nums;
    font-size:1.48rem;
    font-weight:700;
    color:{INK};
  }}
  [data-testid="stMetricDelta"] {{ font-family:{MONO}; font-size:.73rem; }}

  .insight-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(245px,1fr)); gap:12px; margin: 8px 0 16px; }}
  .insight {{
    background: rgba(128,128,128,.035);
    border:1px solid rgba(128,128,128,.22);
    border-radius:12px;
    padding:15px 16px;
    min-height:112px;
  }}
  .insight b {{ display:block; font-size:.78rem; color:{INK_SOFT}; margin-bottom:7px; }}
  .insight strong {{ font-family:{MONO}; font-size:1.02rem; color:{INK}; }}
  .insight p {{ margin:6px 0 0; color:{INK_SOFT}; line-height:1.5; font-size:.84rem; }}

  .note {{
    background: rgba(128,128,128,.055);
    border:1px solid rgba(128,128,128,.18);
    border-left:4px solid {INK_FAINT};
    border-radius:0 8px 8px 0;
    padding:12px 14px;
    margin:8px 0 14px;
    color:{INK_SOFT};
    font-size:.87rem;
    line-height:1.55;
  }}
  .note b {{ color:{INK}; }}
  .danger-note {{ border-left-color:{RED}; }}
  .good-note {{ border-left-color:{GREEN}; }}

  .segment-row {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 14px; }}
  .segment-pill {{
    background: rgba(128,128,128,.035);
    border:1px solid rgba(128,128,128,.22);
    border-radius:999px;
    padding:7px 11px;
    font-size:.79rem;
    color:{INK_SOFT};
  }}
  .segment-pill b {{ font-family:{MONO}; color:{INK}; margin-left:5px; }}

  [data-testid="stVerticalBlockBorderWrapper"] {{
    background: rgba(128,128,128,.025);
    border-color: rgba(128,128,128,.18);
    border-radius:12px;
  }}
  [data-testid="stDataFrame"] {{ border:1px solid rgba(128,128,128,.18); border-radius:10px; }}

  .stTabs [data-baseweb="tab-list"] {{ gap:2px; border-bottom:1px solid rgba(128,128,128,.18); }}
  .stTabs [data-baseweb="tab"] {{
    font-weight:650;
    color:{INK_SOFT};
    padding:10px 15px;
    background:transparent;
  }}
  .stTabs [aria-selected="true"] {{ color:{INK}; background:transparent; }}
  .stTabs [data-baseweb="tab-highlight"] {{ background:{SEA}; height:2px; }}

  [data-testid="stSidebar"] {{ background:#26272F; border-right:1px solid rgba(128,128,128,.18); }}
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {{ color:{INK}; }}
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] span {{ color:{INK_SOFT}; }}
  [data-testid="stSidebar"] [data-baseweb="tag"] {{
    background: rgba(130,181,242,.16) !important;
    border:1px solid rgba(130,181,242,.22);
  }}

  div[data-baseweb="select"] > div,
  div[data-baseweb="input"] > div,
  .stDateInput input,
  .stTextInput input {{
    background:#11131A !important;
    color:{INK} !important;
    border:1px solid rgba(128,128,128,.22) !important;
    border-radius:8px !important;
  }}
  [data-baseweb="popover"] {{ color:{INK}; }}
  [role="listbox"] {{ background:#17191F !important; color:{INK} !important; }}

  .stButton > button, .stDownloadButton > button {{
    background:rgba(128,128,128,.05);
    color:{INK};
    border:1px solid rgba(128,128,128,.24);
    border-radius:8px;
    font-weight:650;
  }}
  .stButton > button:hover, .stDownloadButton > button:hover {{ border-color:{SEA}; color:{INK}; }}

  a {{ color:{SEA}; }}
  code {{ background:#17191F; color:{INK}; padding:2px 6px; border-radius:5px; }}
  :focus-visible {{ outline:2px solid {SEA}; outline-offset:2px; }}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# 데이터 정의
# =============================================================================

ORDER_SHEET_PREFERRED = "주문_2026년1-6월"
MEMBER_SHEET_PREFERRED = "회원_전체누적"

ORDER_REQUIRED = [
    "배송일",
    "접수형태",
    "고객(사)명",
    "송화인",
    "배송물품 품목명",
    "수량",
    "주문 접수 시간",
]
MEMBER_REQUIRED = ["회원명(가명)", "회원유형", "가입일시"]

ITEM_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("김치·반찬", ("김치", "포기", "총각", "겉절이", "깍두기", "열무", "묵은지", "얼갈이", "동지", "반찬", "국,", "국 ", "오이", "보리")),
    ("베이커리·디저트", ("케이크", "빵", "제과", "떡", "디저트", "쿠키")),
    ("신선·수산", ("수산", "생선", "옥돔", "자리돔", "회", "해산물", "망고", "과일", "야채", "딸기", "채소")),
    ("음료·주류", ("커피", "원두", "음료", "포카리", "나랑드", "탄산수", "주류", "생수", "주스")),
    ("건강·의료", ("한약", "의료", "치과", "보철", "약품", "영양", "건강")),
    ("포장·용기", ("포장박스", "아이스박스", "배달용기", "박스", "용기", "포장재")),
    ("의류·생활", ("의류", "옷", "생활용품", "세탁")),
    ("가공식품", ("이유식", "식품", "허브", "착즙", "프리", "라이트", "컬리", "맛")),
    ("반품·회수", ("반품", "회수", "교환")),
]

REQUEST_RULES: dict[str, tuple[str, ...]] = {
    "취급주의": ("조심", "깨지", "파손", "상하주의", "흔들", "방지턱"),
    "냉장·신선": ("냉장", "냉동", "아이스", "신선", "딸기", "식품"),
    "연락요청": ("전화", "연락", "문자", "메세지", "메시지", "도착전", "도착 전에", "오시기전"),
    "문앞·부재": ("문앞", "문 앞", "현관", "부재", "놓아", "놔주", "두고"),
    "시간요청": ("시까지", "오전", "오후", "시간", "빠른배송", "빨리", "당일"),
    "보관요청": ("그늘", "햇빛", "보관", "실온"),
}


@dataclass(frozen=True)
class DataBundle:
    orders: pd.DataFrame
    sessions: pd.DataFrame
    members: pd.DataFrame
    quality: pd.DataFrame
    source_name: str
    order_sheet: str
    member_sheet: str | None


# =============================================================================
# 공통 함수
# =============================================================================


def section(title: str, meta: str = "") -> None:
    st.markdown(
        f'<div class="sec"><h3>{title}</h3>'
        + (f"<i>{meta}</i>" if meta else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def fmt_int(value: float | int) -> str:
    return f"{int(round(float(value))):,}"


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def fmt_days(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "–"
    value = float(value)
    return f"{value:.1f}일" if value < 10 else f"{value:.0f}일"


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_headers(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out.columns = [normalize_text(c) for c in out.columns]
    return out


def coerce_excel_datetime(series: pd.Series) -> pd.Series:
    """Excel serial, pandas Timestamp, 문자열 날짜를 모두 안전하게 datetime으로 변환한다."""
    result = pd.to_datetime(series, errors="coerce")
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_mask = numeric.notna() & numeric.between(20_000, 80_000)
    if numeric_mask.any():
        result.loc[numeric_mask] = pd.to_datetime(
            numeric.loc[numeric_mask], unit="D", origin="1899-12-30", errors="coerce"
        )
    return result


def mode_or_blank(series: pd.Series) -> str:
    clean = series.dropna().astype(str)
    if clean.empty:
        return ""
    mode = clean.mode()
    return mode.iat[0] if not mode.empty else clean.iat[0]


def item_category(text: object) -> str:
    value = normalize_text(text).lower()
    if value in {"", ".", "-", "없음", "미입력"}:
        return "미입력"
    for category, keywords in ITEM_RULES:
        if any(keyword.lower() in value for keyword in keywords):
            return category
    return "기타"


def request_flags(text: object) -> list[str]:
    value = normalize_text(text).lower()
    if not value:
        return []
    return [label for label, keywords in REQUEST_RULES.items() if any(k.lower() in value for k in keywords)]


def time_band(hour: float | int | None) -> str:
    if hour is None or pd.isna(hour):
        return "미상"
    h = int(hour)
    if h <= 5:
        return "00–05시"
    if h <= 8:
        return "06–08시"
    if h <= 11:
        return "09–11시"
    if h <= 14:
        return "12–14시"
    if h <= 17:
        return "15–17시"
    return "18–23시"


def style_fig(fig: go.Figure, height: int = 350) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=52, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Malgun Gothic, sans-serif", size=12, color=INK),
        colorway=SERIES,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=INK_SOFT),
            title_text="",
        ),
        hoverlabel=dict(
            bgcolor="#17191F",
            bordercolor=LINE,
            font=dict(family="Consolas, monospace", size=12, color=INK),
        ),
        title=dict(font=dict(size=14, color=INK), x=0.01, xanchor="left"),
        separators=".,",
    )
    fig.update_xaxes(
        showgrid=False,
        showline=False,
        zeroline=False,
        title_text="",
        tickfont=dict(color=INK_SOFT),
    )
    fig.update_yaxes(
        gridcolor="rgba(128,128,128,.18)",
        showline=False,
        zeroline=False,
        title_text="",
        tickfont=dict(color=INK_SOFT),
    )
    return fig


def chart(fig: go.Figure, height: int = 350) -> None:
    style_fig(fig, height)
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": False},
    )


def insight_cards(cards: Iterable[tuple[str, str, str]]) -> None:
    html = '<div class="insight-grid">'
    for title, strong, description in cards:
        html += (
            '<div class="insight">'
            f"<b>{title}</b><strong>{strong}</strong><p>{description}</p>"
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def dataframe_download(frame: pd.DataFrame, filename: str, label: str) -> None:
    st.download_button(
        label,
        frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def find_default_file() -> Path | None:
    base = Path(__file__).resolve().parent
    candidates = [
        base / "data.xlsx",
        base / "data - 복사본.xlsx",
        base / "data" / "data.xlsx",
        base / "data" / "data - 복사본.xlsx",
    ]
    return next((path for path in candidates if path.exists()), None)


def find_sheet_name(excel: pd.ExcelFile, required: list[str], preferred: str | None = None) -> str | None:
    if preferred and preferred in excel.sheet_names:
        sample = normalize_headers(pd.read_excel(excel, sheet_name=preferred, nrows=3))
        if set(required).issubset(sample.columns):
            return preferred
    for sheet in excel.sheet_names:
        sample = normalize_headers(pd.read_excel(excel, sheet_name=sheet, nrows=3))
        if set(required).issubset(sample.columns):
            return sheet
    return None


# =============================================================================
# 데이터 적재 및 전처리
# =============================================================================


@st.cache_data(show_spinner="Excel 데이터를 읽고 주문회차를 재구성하는 중…")
def load_and_prepare(file_bytes: bytes, source_name: str) -> DataBundle:
    excel = pd.ExcelFile(io.BytesIO(file_bytes))
    order_sheet = find_sheet_name(excel, ORDER_REQUIRED, ORDER_SHEET_PREFERRED)
    member_sheet = find_sheet_name(excel, MEMBER_REQUIRED, MEMBER_SHEET_PREFERRED)

    if order_sheet is None:
        raise ValueError(
            "주문 시트를 찾지 못했습니다. 필요한 열: " + ", ".join(ORDER_REQUIRED)
        )

    raw_orders = normalize_headers(pd.read_excel(excel, sheet_name=order_sheet))
    raw_members = (
        normalize_headers(pd.read_excel(excel, sheet_name=member_sheet))
        if member_sheet is not None
        else pd.DataFrame(columns=MEMBER_REQUIRED)
    )

    missing_order_cols = [c for c in ORDER_REQUIRED if c not in raw_orders.columns]
    if missing_order_cols:
        raise ValueError("주문 데이터 필수 열 누락: " + ", ".join(missing_order_cols))

    orders = raw_orders.copy()
    orders["delivery_row_id"] = np.arange(1, len(orders) + 1)
    orders["customer_id"] = orders["고객(사)명"].map(normalize_text)
    orders["sender_id"] = orders["송화인"].map(normalize_text)
    orders["channel"] = orders["접수형태"].map(normalize_text)
    orders["item_name"] = orders["배송물품 품목명"].map(normalize_text)
    orders["request_text"] = (
        orders["요청사항"].map(normalize_text)
        if "요청사항" in orders.columns
        else ""
    )
    orders["pickup_address"] = (
        orders["수거지 주소"].map(normalize_text)
        if "수거지 주소" in orders.columns
        else ""
    )
    orders["delivery_address"] = (
        orders["배송지 주소"].map(normalize_text)
        if "배송지 주소" in orders.columns
        else ""
    )
    orders["quantity"] = pd.to_numeric(orders["수량"], errors="coerce").fillna(0)
    orders["delivery_date"] = coerce_excel_datetime(orders["배송일"]).dt.normalize()
    orders["order_datetime"] = coerce_excel_datetime(orders["주문 접수 시간"])

    members = raw_members.copy()
    if not members.empty:
        members["customer_id"] = members["회원명(가명)"].map(normalize_text)
        members["customer_type"] = members["회원유형"].map(normalize_text)
        members["join_datetime"] = coerce_excel_datetime(members["가입일시"])
        members = members.drop_duplicates("customer_id", keep="last")
        member_map = members.set_index("customer_id")["customer_type"]
        join_map = members.set_index("customer_id")["join_datetime"]
        orders["customer_type"] = orders["customer_id"].map(member_map)
        orders["join_datetime"] = orders["customer_id"].map(join_map)
    else:
        orders["customer_type"] = np.nan
        orders["join_datetime"] = pd.NaT

    inferred_type = np.where(
        orders["customer_id"].str.startswith("사업자"),
        "사업자",
        np.where(orders["customer_id"].str.startswith("개인"), "개인", "미상"),
    )
    orders["customer_type"] = orders["customer_type"].replace("", np.nan).fillna(
        pd.Series(inferred_type, index=orders.index)
    )

    # 날짜/고객이 없는 행은 분석에서 제외하되 품질표에는 남긴다.
    valid_mask = (
        orders["customer_id"].ne("")
        & orders["order_datetime"].notna()
        & orders["delivery_date"].notna()
    )
    orders["analysis_valid"] = valid_mask

    # 동일 고객 + 동일 접수시각을 하나의 주문회차로 정의한다.
    # 접수시각이 없는 행은 서로 합쳐지지 않도록 행 ID를 보조키로 사용한다.
    key_time = orders["order_datetime"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    fallback = "ROW-" + orders["delivery_row_id"].astype(str)
    key_time = key_time.where(orders["order_datetime"].notna(), fallback)
    orders["session_key"] = orders["customer_id"] + "|" + key_time
    session_codes, _ = pd.factorize(orders["session_key"], sort=False)
    orders["order_session_id"] = "ORD-" + pd.Series(session_codes + 1).astype(str).str.zfill(6)

    orders["item_category"] = orders["item_name"].map(item_category)
    flags = orders["request_text"].map(request_flags)
    for label in REQUEST_RULES:
        orders[f"request_{label}"] = flags.map(lambda values, x=label: x in values)

    orders["visible_fingerprint"] = (
        orders[[
            "delivery_date", "channel", "customer_id", "request_text",
            "sender_id", "item_name", "quantity", "order_datetime"
        ]]
        .astype(str)
        .agg("|".join, axis=1)
    )

    valid_orders = orders[orders["analysis_valid"]].copy()
    sessions = (
        valid_orders.groupby("order_session_id", as_index=False)
        .agg(
            customer_id=("customer_id", "first"),
            customer_type=("customer_type", "first"),
            order_datetime=("order_datetime", "min"),
            delivery_date=("delivery_date", "min"),
            delivery_date_count=("delivery_date", "nunique"),
            channel=("channel", mode_or_blank),
            delivery_count=("delivery_row_id", "size"),
            quantity=("quantity", "sum"),
            item_input_count=("item_name", lambda s: s.ne("").sum()),
            request_input_count=("request_text", lambda s: s.ne("").sum()),
        )
        .sort_values(["customer_id", "order_datetime", "order_session_id"])
        .reset_index(drop=True)
    )

    sessions["order_date"] = sessions["order_datetime"].dt.normalize()
    sessions["order_hour"] = sessions["order_datetime"].dt.hour.astype("Int64")
    sessions["order_month"] = sessions["order_datetime"].dt.to_period("M").astype(str)
    sessions["delivery_month"] = sessions["delivery_date"].dt.to_period("M").astype(str)
    sessions["order_weekday"] = pd.Categorical(
        sessions["order_datetime"].dt.day_name().map(
            {
                "Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일",
                "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일",
                "Sunday": "일요일",
            }
        ),
        categories=WEEKDAYS,
        ordered=True,
    )
    sessions["delivery_weekday"] = pd.Categorical(
        sessions["delivery_date"].dt.day_name().map(
            {
                "Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일",
                "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일",
                "Sunday": "일요일",
            }
        ),
        categories=WEEKDAYS,
        ordered=True,
    )
    sessions["time_band"] = pd.Categorical(
        sessions["order_hour"].map(time_band), categories=TIME_BANDS, ordered=True
    )
    sessions["lead_time_days"] = (
        sessions["delivery_date"] - sessions["order_date"]
    ).dt.days
    sessions["order_number"] = sessions.groupby("customer_id").cumcount() + 1
    sessions["previous_order_datetime"] = sessions.groupby("customer_id")["order_datetime"].shift(1)
    sessions["gap_days"] = (
        sessions["order_datetime"] - sessions["previous_order_datetime"]
    ).dt.total_seconds() / 86_400
    sessions["first_order_datetime"] = sessions.groupby("customer_id")["order_datetime"].transform("min")
    sessions["first_order_month"] = sessions["first_order_datetime"].dt.to_period("M").astype(str)
    sessions["is_repeat_order"] = sessions["order_number"].gt(1)
    sessions["is_multi_delivery"] = sessions["delivery_count"].gt(1)

    # 데이터 품질표
    quality_rows: list[dict[str, object]] = []
    for source_col, internal_col in [
        ("배송일", "delivery_date"),
        ("주문 접수 시간", "order_datetime"),
        ("고객(사)명", "customer_id"),
        ("배송물품 품목명", "item_name"),
        ("요청사항", "request_text"),
        ("수거지 주소", "pickup_address"),
        ("배송지 주소", "delivery_address"),
    ]:
        if internal_col not in orders.columns:
            continue
        if pd.api.types.is_datetime64_any_dtype(orders[internal_col]):
            missing = orders[internal_col].isna().sum()
        else:
            missing = orders[internal_col].fillna("").astype(str).str.strip().eq("").sum()
        quality_rows.append(
            {
                "항목": source_col,
                "전체 행": len(orders),
                "결측 행": int(missing),
                "결측률": safe_div(missing, len(orders)),
            }
        )

    quality = pd.DataFrame(quality_rows)
    return DataBundle(
        orders=orders,
        sessions=sessions,
        members=members,
        quality=quality,
        source_name=source_name,
        order_sheet=order_sheet,
        member_sheet=member_sheet,
    )


# =============================================================================
# 분석 계산 함수
# =============================================================================


def reference_series(frame: pd.DataFrame, reference: str) -> pd.Series:
    return frame["delivery_date"] if reference == "배송일" else frame["order_date"]


def build_customer_summary(
    history: pd.DataFrame,
    members: pd.DataFrame,
    period_end: pd.Timestamp,
) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame()

    history = history.sort_values(["customer_id", "order_datetime"]).copy()
    base = (
        history.groupby("customer_id", as_index=False)
        .agg(
            customer_type=("customer_type", mode_or_blank),
            first_order=("order_datetime", "min"),
            last_order=("order_datetime", "max"),
            order_sessions=("order_session_id", "nunique"),
            delivery_count=("delivery_count", "sum"),
            quantity=("quantity", "sum"),
            active_order_days=("order_date", "nunique"),
            active_delivery_days=("delivery_date", "nunique"),
            average_batch=("delivery_count", "mean"),
            preferred_weekday=("order_weekday", mode_or_blank),
            preferred_hour=("order_hour", mode_or_blank),
            primary_channel=("channel", mode_or_blank),
        )
    )

    gap = (
        history.dropna(subset=["gap_days"])
        .groupby("customer_id")["gap_days"]
        .agg(avg_gap_days="mean", median_gap_days="median", gap_std_days="std")
        .reset_index()
    )
    base = base.merge(gap, on="customer_id", how="left")
    base["recency_days"] = (
        period_end - base["last_order"]
    ).dt.total_seconds().div(86_400).clip(lower=0)
    base["customer_lifetime_days"] = (
        base["last_order"] - base["first_order"]
    ).dt.total_seconds().div(86_400)
    base["active_months"] = (
        (base["last_order"].dt.year - base["first_order"].dt.year) * 12
        + base["last_order"].dt.month
        - base["first_order"].dt.month
        + 1
    ).clip(lower=1)
    base["orders_per_active_month"] = base["order_sessions"] / base["active_months"]
    base["repeat_customer"] = base["order_sessions"].ge(2)
    base["expected_cycle_days"] = base["median_gap_days"].where(
        base["median_gap_days"].notna(), base["avg_gap_days"]
    )
    base["cycle_delay_ratio"] = base["recency_days"] / base["expected_cycle_days"].replace(0, np.nan)

    if not members.empty:
        member_cols = members[["customer_id", "customer_type", "join_datetime"]].copy()
        member_cols = member_cols.rename(columns={"customer_type": "member_type"})
        base = base.merge(member_cols, on="customer_id", how="left")
        base["customer_type"] = base["member_type"].fillna(base["customer_type"])
        base["days_to_first_order"] = (
            base["first_order"] - base["join_datetime"]
        ).dt.total_seconds().div(86_400)
    else:
        base["join_datetime"] = pd.NaT
        base["days_to_first_order"] = np.nan

    # 고객별 주문주기와 절대 무주문 기간을 동시에 사용한다.
    risk_threshold = np.maximum(30.0, base["expected_cycle_days"].fillna(30) * 3.0)
    care_threshold = np.maximum(14.0, base["expected_cycle_days"].fillna(14) * 2.0)
    base["alert_level"] = np.select(
        [
            base["repeat_customer"] & base["recency_days"].gt(risk_threshold),
            base["repeat_customer"] & base["recency_days"].gt(care_threshold),
        ],
        ["위험", "관심필요"],
        default="정상",
    )

    high_frequency_cut = max(5.0, float(base["order_sessions"].quantile(0.8)))
    base["segment"] = np.select(
        [
            base["order_sessions"].eq(1) & base["recency_days"].le(30),
            base["order_sessions"].eq(1) & base["recency_days"].gt(30),
            base["alert_level"].eq("위험"),
            base["alert_level"].eq("관심필요"),
            base["order_sessions"].ge(high_frequency_cut) & base["recency_days"].le(14),
            base["order_sessions"].ge(5),
            base["order_sessions"].ge(2),
        ],
        ["신규·첫주문", "일회성·미재주문", "이탈위험", "관심필요", "핵심고객", "충성고객", "재이용고객"],
        default="기타",
    )

    base["first_order_month"] = base["first_order"].dt.to_period("M").astype(str)
    base["last_order_date"] = base["last_order"].dt.date
    return base.sort_values(["alert_level", "order_sessions"], ascending=[True, False])


def repeat_conversion(history: pd.DataFrame, period_end: pd.Timestamp, horizons=(7, 14, 30, 60, 90)) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame(columns=["기간", "관찰가능 고객", "재주문 고객", "전환율"])
    ordered = history.sort_values(["customer_id", "order_datetime"])
    first_two = ordered.groupby("customer_id")["order_datetime"].agg(
        first_order="min",
        second_order=lambda x: x.iloc[1] if len(x) >= 2 else pd.NaT,
    ).reset_index()
    rows = []
    for horizon in horizons:
        eligible = first_two[(period_end - first_two["first_order"]).dt.total_seconds() / 86_400 >= horizon]
        converted = eligible[
            eligible["second_order"].notna()
            & ((eligible["second_order"] - eligible["first_order"]).dt.total_seconds() / 86_400 <= horizon)
        ]
        rows.append(
            {
                "기간": f"{horizon}일",
                "관찰가능 고객": len(eligible),
                "재주문 고객": len(converted),
                "전환율": safe_div(len(converted), len(eligible)),
            }
        )
    return pd.DataFrame(rows)


def conversion_curve(history: pd.DataFrame, period_end: pd.Timestamp, max_days: int = 90) -> pd.DataFrame:
    horizons = sorted(set(list(range(1, 15)) + list(range(15, max_days + 1, 5)) + [30, 60, 90]))
    return repeat_conversion(history, period_end, horizons).assign(
        days=lambda d: d["기간"].str.replace("일", "", regex=False).astype(int)
    )


def cohort_retention(history: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame()
    temp = history[["customer_id", "order_datetime"]].copy()
    temp["activity_month"] = temp["order_datetime"].dt.to_period("M")
    first = temp.groupby("customer_id")["activity_month"].min().rename("cohort_month")
    temp = temp.merge(first, on="customer_id", how="left")
    cohort_start = start_date.to_period("M")
    cohort_end = end_date.to_period("M")
    temp = temp[temp["cohort_month"].between(cohort_start, cohort_end)]
    if temp.empty:
        return pd.DataFrame()
    temp["month_index"] = (
        (temp["activity_month"].dt.year - temp["cohort_month"].dt.year) * 12
        + temp["activity_month"].dt.month
        - temp["cohort_month"].dt.month
    )
    active = temp.drop_duplicates(["customer_id", "activity_month"])
    counts = active.groupby(["cohort_month", "month_index"])["customer_id"].nunique()
    sizes = active[active["month_index"].eq(0)].groupby("cohort_month")["customer_id"].nunique()
    retention = counts.div(sizes, level="cohort_month").unstack(fill_value=0)
    retention.index = retention.index.astype(str)
    retention.columns = [f"M+{int(c)}" for c in retention.columns]
    return retention.sort_index()


def monthly_new_returning(history: pd.DataFrame) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame(columns=["월", "신규 고객", "재주문 고객", "활성 고객"])
    temp = history.copy()
    temp["월"] = temp["order_datetime"].dt.to_period("M").astype(str)
    first_month = temp.groupby("customer_id")["order_datetime"].min().dt.to_period("M").astype(str)
    temp["first_month"] = temp["customer_id"].map(first_month)
    unique = temp.drop_duplicates(["월", "customer_id"])
    result = (
        unique.assign(구분=np.where(unique["월"].eq(unique["first_month"]), "신규 고객", "재주문 고객"))
        .groupby(["월", "구분"])["customer_id"].nunique()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["신규 고객", "재주문 고객"]:
        if col not in result:
            result[col] = 0
    result["활성 고객"] = result["신규 고객"] + result["재주문 고객"]
    return result[["월", "신규 고객", "재주문 고객", "활성 고객"]]


def frequency_bands(customer_summary: pd.DataFrame) -> pd.DataFrame:
    if customer_summary.empty:
        return pd.DataFrame(columns=["주문회차 구간", "고객 수"])
    bins = [0, 1, 2, 5, 10, 20, np.inf]
    labels = ["1회", "2회", "3–5회", "6–10회", "11–20회", "21회 이상"]
    band = pd.cut(customer_summary["order_sessions"], bins=bins, labels=labels, include_lowest=True)
    return band.value_counts(sort=False).rename_axis("주문회차 구간").reset_index(name="고객 수")


def hhi_share(values: pd.Series) -> float:
    total = values.sum()
    if total <= 0:
        return 0.0
    shares = values / total
    return float((shares.pow(2).sum()) * 10_000)


def build_report(
    period_sessions: pd.DataFrame,
    period_orders: pd.DataFrame,
    history: pd.DataFrame,
    customer_summary: pd.DataFrame,
    members: pd.DataFrame,
    quality: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    reference: str,
    source_name: str,
) -> str:
    active_customers = period_sessions["customer_id"].nunique()
    repeat_active = customer_summary[
        customer_summary["customer_id"].isin(period_sessions["customer_id"].unique())
    ]["repeat_customer"].mean() if active_customers else 0
    repeat_session_share = period_sessions["is_repeat_order"].mean() if len(period_sessions) else 0
    same_day = period_sessions["lead_time_days"].eq(0).mean() if len(period_sessions) else 0
    multi = period_sessions["is_multi_delivery"].mean() if len(period_sessions) else 0

    hourly = period_sessions["order_hour"].value_counts()
    peak_hour = int(hourly.idxmax()) if not hourly.empty else 0
    joint_peak = period_sessions.groupby(["order_weekday", "order_hour"], observed=False).size()
    joint_peak = joint_peak[joint_peak.gt(0)]
    if not joint_peak.empty:
        peak_weekday, peak_hour = joint_peak.idxmax()
        peak_weekday = str(peak_weekday)
        peak_hour = int(peak_hour)
    else:
        peak_weekday = "–"
    monthly = period_sessions.groupby("delivery_month")["order_session_id"].nunique()
    peak_month = str(monthly.idxmax()) if not monthly.empty else "–"

    gaps = history["gap_days"].dropna()
    median_gap = gaps.median() if not gaps.empty else np.nan
    second = (
        history.sort_values(["customer_id", "order_datetime"])
        .groupby("customer_id")["order_datetime"]
        .apply(lambda x: (x.iloc[1] - x.iloc[0]).total_seconds() / 86_400 if len(x) >= 2 else np.nan)
        .dropna()
    )
    median_second = second.median() if not second.empty else np.nan
    conversions = repeat_conversion(history, end_date)
    conv_map = dict(zip(conversions["기간"], conversions["전환율"]))

    volume_by_customer = period_sessions.groupby("customer_id")["delivery_count"].sum().sort_values(ascending=False)
    top1 = safe_div(volume_by_customer.head(1).sum(), volume_by_customer.sum())
    top10 = safe_div(volume_by_customer.head(10).sum(), volume_by_customer.sum())

    risk = customer_summary[customer_summary["alert_level"].eq("위험")]
    care = customer_summary[customer_summary["alert_level"].eq("관심필요")]

    eligible_members = members[
        members["join_datetime"].notna() & members["join_datetime"].le(end_date)
    ] if not members.empty else pd.DataFrame()
    ordered_by_end = history["customer_id"].nunique()
    activation = safe_div(ordered_by_end, len(eligible_members)) if len(eligible_members) else 0

    address_missing = quality.loc[
        quality["항목"].isin(["수거지 주소", "배송지 주소"]), "결측률"
    ].max() if not quality.empty else 0

    report = f"""# 고객 주문·재주문 분석 보고서

- **분석 파일:** {source_name}
- **분석 기간:** {start_date.date()} ~ {end_date.date()} ({reference} 기준)
- **분석 단위:** 배송 행과 주문회차를 분리하여 산출

## 1. 데이터 개요

| 지표 | 결과 |
|---|---:|
| 배송 행 | {len(period_orders):,}건 |
| 주문회차 | {len(period_sessions):,}회 |
| 활성 고객 | {active_customers:,}곳 |
| 주문회차당 평균 배송 | {safe_div(len(period_orders), len(period_sessions)):.2f}건 |
| 다건 주문회차 비율 | {multi * 100:.1f}% |
| 당일 배송률 | {same_day * 100:.1f}% |

> **주문회차**는 동일 고객이 동일 접수시각에 등록한 배송 행을 하나로 묶은 값이다. 재주문 분석에 배송 행을 그대로 사용하면 엑셀 일괄 주문 고객의 빈도가 과대계산되므로 주문회차를 사용했다.

## 2. 핵심 결과

1. 주문 접수는 **{peak_weekday} {peak_hour:02d}시대**에 가장 많이 발생했다.
2. 배송월 기준 최대 주문회차는 **{peak_month}**에 발생했다.
3. 활성 고객 중 과거 주문을 포함해 2회 이상 주문한 고객 비율은 **{repeat_active * 100:.1f}%**이다.
4. 분석 기간 주문회차 중 첫 주문 이후 주문이 차지하는 비중은 **{repeat_session_share * 100:.1f}%**이다.
5. 고객 상위 1곳이 배송 물량의 **{top1 * 100:.1f}%**, 상위 10곳이 **{top10 * 100:.1f}%**를 차지한다.

## 3. 재주문 패턴

| 재주문 지표 | 결과 |
|---|---:|
| 전체 주문 간격 중앙값 | {fmt_days(median_gap)} |
| 첫 주문 → 두 번째 주문 중앙값 | {fmt_days(median_second)} |
| 7일 이내 재주문 전환율 | {conv_map.get('7일', 0) * 100:.1f}% |
| 30일 이내 재주문 전환율 | {conv_map.get('30일', 0) * 100:.1f}% |
| 60일 이내 재주문 전환율 | {conv_map.get('60일', 0) * 100:.1f}% |
| 90일 이내 재주문 전환율 | {conv_map.get('90일', 0) * 100:.1f}% |

재주문 전환율은 해당 기간만큼 관찰할 수 있는 고객만 분모에 포함했다. 예를 들어 90일 전환율에는 분석 종료일까지 첫 주문 후 90일 이상 관찰된 고객만 포함된다.

## 4. 고객 유지 및 위험 신호

- **위험 고객:** {len(risk):,}곳
- **관심필요 고객:** {len(care):,}곳
- **기준일 이전 가입회원 주문 활성화율:** {activation * 100:.1f}%

위험도는 단순히 마지막 주문일만 보지 않고 고객별 평소 주문 간격을 함께 사용했다. 재주문 고객의 무주문 기간이 `평소 중앙 주문주기의 3배`와 `30일` 중 큰 값을 넘으면 위험, `평소 주기의 2배`와 `14일` 중 큰 값을 넘으면 관심필요로 분류한다.

## 5. 운영 해석 및 권고

1. **인력 배치:** {peak_weekday}과 {peak_hour:02d}시 전후에 접수 검수·배차 인력을 집중한다.
2. **일괄 주문 분리 관리:** 다건 주문회차 비율이 {multi * 100:.1f}%이므로 고객 주문 수와 실제 배송 물량을 별도 KPI로 관리한다.
3. **재주문 유도:** 첫 주문 후 7일·30일 전환 구간을 기준으로 개인 고객과 저빈도 고객에게 후속 안내 시점을 설계한다.
4. **거래처 의존도 관리:** 상위 고객 물량 비중이 높으면 주요 거래처 감소 경보와 대체 고객 확보 목표를 함께 운영한다.
5. **위험 고객 우선순위:** 위험 고객 중 과거 주문회차와 배송량이 큰 고객부터 연락 순서를 정한다.

## 6. 데이터 품질 및 한계

- 주소 결측률 최고값은 **{address_missing * 100:.1f}%**다. 주소가 비식별화된 경우 지역·권역별 분석은 수행하지 않는다.
- 가격·청구액 열이 없어 매출과 고객가치 금액은 계산하지 않았다. 본 보고서의 고객가치는 주문회차·배송량·수량 기준이다.
- 화면상 완전히 동일한 행이 있더라도 주소가 제거된 다건 배송일 수 있으므로 자동 중복 삭제하지 않았다.
- 품목 카테고리는 품목명 키워드에 의한 운영용 추정 분류이며 회계상 상품 분류와 다를 수 있다.
"""
    return report


def build_download_zip(
    report_text: str,
    period_sessions: pd.DataFrame,
    customer_summary: pd.DataFrame,
    quality: pd.DataFrame,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("분석보고서.md", report_text.encode("utf-8-sig"))
        zf.writestr("주문회차_분석.csv", period_sessions.to_csv(index=False).encode("utf-8-sig"))
        zf.writestr("고객_분석.csv", customer_summary.to_csv(index=False).encode("utf-8-sig"))
        zf.writestr("데이터품질.csv", quality.to_csv(index=False).encode("utf-8-sig"))
    return buffer.getvalue()


# =============================================================================
# 화면 구성
# =============================================================================


def main() -> None:
    # ------------------------------------------------------------------ 파일
    st.sidebar.markdown("### DATA SOURCE")
    uploaded = st.sidebar.file_uploader("Excel 파일", type=["xlsx", "xls"], help="주문 시트와 회원 시트를 포함한 파일")
    default_file = find_default_file()

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        source_name = uploaded.name
    elif default_file is not None:
        file_bytes = default_file.read_bytes()
        source_name = default_file.name
        st.sidebar.caption(f"자동 불러오기: {default_file.name}")
    else:
        st.title("고객 주문 분석 대시보드")
        st.markdown(
            '<div class="pl-subtitle">주문회차·재주문·시간대 수요·고객 이탈 위험 통합 분석</div>',
            unsafe_allow_html=True,
        )
        st.info("사이드바에서 Excel 파일을 업로드하거나 app.py와 같은 폴더에 `data.xlsx`를 두세요.")
        st.stop()

    try:
        bundle = load_and_prepare(file_bytes, source_name)
    except Exception as exc:
        st.error(f"데이터를 읽지 못했습니다: {exc}")
        st.stop()

    sessions_all = bundle.sessions
    orders_all = bundle.orders[bundle.orders["analysis_valid"]].copy()
    members = bundle.members

    if sessions_all.empty:
        st.error("분석 가능한 주문회차가 없습니다. 날짜와 고객 열을 확인하세요.")
        st.stop()

    # ------------------------------------------------------------------ 필터
    st.sidebar.markdown("### ANALYSIS FILTER")
    reference = st.sidebar.radio(
        "기간 기준",
        ["배송일", "주문 접수일"],
        horizontal=True,
        help="운영 물량은 배송일, 고객 주문행동은 주문 접수일 기준이 적합합니다.",
    )
    ref_source = sessions_all["delivery_date"] if reference == "배송일" else sessions_all["order_date"]
    data_min = ref_source.min().date()
    data_max = ref_source.max().date()
    picked = st.sidebar.date_input(
        "분석 기간",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
        key=f"analysis_period_{reference}",
    )
    if isinstance(picked, tuple) and len(picked) == 2:
        start_d, end_d = picked
    else:
        start_d = end_d = picked if isinstance(picked, date) else data_max
    if start_d > end_d:
        start_d, end_d = end_d, start_d

    type_options = sorted(sessions_all["customer_type"].dropna().unique().tolist())
    selected_types = st.sidebar.multiselect("고객 유형", type_options, default=type_options)
    channel_options = sorted(sessions_all["channel"].dropna().unique().tolist())
    selected_channels = st.sidebar.multiselect("접수 형태", channel_options, default=channel_options)

    start_ts = pd.Timestamp(start_d)
    end_ts = pd.Timestamp.combine(end_d, time.max)

    base = sessions_all[
        sessions_all["customer_type"].isin(selected_types)
        & sessions_all["channel"].isin(selected_channels)
    ].copy()
    ref_col = "delivery_date" if reference == "배송일" else "order_date"
    history = base[base[ref_col].le(end_ts)].copy()
    period_sessions = history[history[ref_col].ge(start_ts)].copy()
    period_ids = set(period_sessions["order_session_id"])
    period_orders = orders_all[orders_all["order_session_id"].isin(period_ids)].copy()

    if period_sessions.empty:
        st.warning("선택한 조건에 해당하는 주문이 없습니다. 필터 범위를 넓혀 주세요.")
        st.stop()

    customer_summary = build_customer_summary(history, members, end_ts)
    active_ids = set(period_sessions["customer_id"])
    active_customer_summary = customer_summary[customer_summary["customer_id"].isin(active_ids)].copy()

    # ------------------------------------------------------------------ 헤더
    st.title("고객 주문 분석 대시보드")
    st.markdown(
        '<div class="pl-subtitle">'
        "주문회차·재주문·시간대 수요·고객 이탈 위험 통합 분석"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pl-note"><b>분석 기준</b><br>'
        f'{reference} · {start_d} ~ {end_d}<br>'
        f'파일: {bundle.source_name} · 주문 시트: {bundle.order_sheet} · '
        f'회원 시트: {bundle.member_sheet or "없음"}</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "경영 요약",
        "시간대·수요",
        "재주문·코호트",
        "고객·이탈위험",
        "품목·운영",
        "분석 보고서",
    ])

    # ================================================================== 1
    with tabs[0]:
        active_customers = period_sessions["customer_id"].nunique()
        repeat_customer_rate = active_customer_summary["repeat_customer"].mean()
        repeat_order_share = period_sessions["is_repeat_order"].mean()
        same_day_rate = period_sessions["lead_time_days"].eq(0).mean()
        avg_batch = period_sessions["delivery_count"].mean()
        multi_rate = period_sessions["is_multi_delivery"].mean()

        hourly = period_sessions["order_hour"].value_counts()
        peak_hour = int(hourly.idxmax()) if not hourly.empty else 0
        peak_hour_share = safe_div(hourly.max(), len(period_sessions)) if not hourly.empty else 0

        cols = st.columns(6)
        cols[0].metric("배송 행", f"{len(period_orders):,}건")
        cols[1].metric("주문회차", f"{len(period_sessions):,}회", help="동일 고객+동일 접수시각을 1회로 계산")
        cols[2].metric("활성 고객", f"{active_customers:,}곳")
        cols[3].metric("재주문 고객률", fmt_pct(repeat_customer_rate), help="선택 기간 활성 고객 중 기준일까지 누적 2회 이상 주문한 고객")
        cols[4].metric("재주문회차 비중", fmt_pct(repeat_order_share), help="선택 기간 주문회차 중 고객의 두 번째 이후 주문")
        cols[5].metric("당일 배송률", fmt_pct(same_day_rate))

        monthly = (
            period_sessions.groupby("delivery_month", as_index=False)
            .agg(
                주문회차=("order_session_id", "nunique"),
                배송행=("delivery_count", "sum"),
                활성고객=("customer_id", "nunique"),
                수량=("quantity", "sum"),
            )
        )
        peak_month_row = monthly.loc[monthly["주문회차"].idxmax()]
        joint_peak = period_sessions.groupby(["order_weekday", "order_hour"], observed=False).size()
        joint_peak = joint_peak[joint_peak.gt(0)]
        if not joint_peak.empty:
            peak_weekday, peak_hour_joint = joint_peak.idxmax()
            peak_weekday = str(peak_weekday)
            peak_hour_joint = int(peak_hour_joint)
        else:
            peak_weekday, peak_hour_joint = "–", peak_hour
        customer_volume = period_sessions.groupby("customer_id")["delivery_count"].sum().sort_values(ascending=False)
        top1_share = safe_div(customer_volume.head(1).sum(), customer_volume.sum())
        top10_share = safe_div(customer_volume.head(10).sum(), customer_volume.sum())

        insight_cards([
            (
                "최대 수요 월",
                f"{peak_month_row['delivery_month']} · {int(peak_month_row['주문회차']):,}회",
                f"배송 행은 {int(peak_month_row['배송행']):,}건, 활성 고객은 {int(peak_month_row['활성고객']):,}곳입니다.",
            ),
            (
                "주문 피크 시간",
                f"{peak_weekday} · {peak_hour_joint:02d}시",
                f"전체 시간 기준 최다 접수 시간은 {peak_hour:02d}시이며, 해당 시간 비중은 {peak_hour_share * 100:.1f}%입니다.",
            ),
            (
                "일괄 주문 구조",
                f"평균 {avg_batch:.2f}건/회",
                f"주문회차의 {multi_rate * 100:.1f}%가 2건 이상 배송을 포함합니다.",
            ),
            (
                "고객 의존도",
                f"상위 1곳 {top1_share * 100:.1f}%",
                f"상위 10곳이 전체 배송 행의 {top10_share * 100:.1f}%를 차지합니다.",
            ),
        ])

        a, b = st.columns([1.25, 1])
        with a:
            fig = go.Figure()
            fig.add_bar(x=monthly["delivery_month"], y=monthly["배송행"], name="배송 행", marker_color=SEA)
            fig.add_scatter(x=monthly["delivery_month"], y=monthly["주문회차"], name="주문회차", mode="lines+markers", line=dict(color=ORANGE, width=3), yaxis="y2")
            fig.update_layout(
                title="월별 배송 물량과 주문회차",
                yaxis2=dict(overlaying="y", side="right", showgrid=False),
                hovermode="x unified",
            )
            chart(fig, 390)
        with b:
            nr = monthly_new_returning(history)
            nr = nr[nr["월"].between(start_ts.to_period("M").strftime("%Y-%m"), end_ts.to_period("M").strftime("%Y-%m"))]
            fig = go.Figure()
            fig.add_bar(x=nr["월"], y=nr["신규 고객"], name="신규 고객", marker_color=ORANGE)
            fig.add_bar(x=nr["월"], y=nr["재주문 고객"], name="재주문 고객", marker_color=SEA)
            fig.update_layout(title="월별 신규·재주문 활성 고객", barmode="stack", hovermode="x unified")
            chart(fig, 390)

        a, b = st.columns(2)
        with a:
            daily = (
                period_sessions.groupby(ref_col, as_index=False)
                .agg(주문회차=("order_session_id", "nunique"), 배송행=("delivery_count", "sum"))
                .sort_values(ref_col)
            )
            daily["7일 이동평균"] = daily["배송행"].rolling(7, min_periods=1).mean()
            fig = go.Figure()
            fig.add_bar(x=daily[ref_col], y=daily["배송행"], name="배송 행", marker_color="rgba(99,179,255,.34)")
            fig.add_scatter(x=daily[ref_col], y=daily["7일 이동평균"], name="7일 이동평균", line=dict(color=SEA, width=2.5))
            fig.update_layout(title="일별 물량과 7일 이동평균", hovermode="x unified")
            chart(fig, 350)
        with b:
            pareto = customer_volume.reset_index(name="배송행").head(20)
            pareto["누적비중"] = pareto["배송행"].cumsum() / customer_volume.sum()
            fig = go.Figure()
            fig.add_bar(x=pareto["customer_id"], y=pareto["배송행"], name="배송 행", marker_color=SEA)
            fig.add_scatter(x=pareto["customer_id"], y=pareto["누적비중"], name="누적 비중", mode="lines+markers", line=dict(color=ORANGE), yaxis="y2")
            fig.update_layout(title="상위 20개 고객 물량 집중도", yaxis2=dict(overlaying="y", side="right", tickformat=".0%", range=[0, 1.05], showgrid=False))
            fig.update_xaxes(tickangle=-45)
            chart(fig, 350)

        st.markdown(
            '<div class="note"><b>지표 해석:</b> 배송 행은 실제 처리 물량, 주문회차는 고객의 주문 행동입니다. '
            'B2B 엑셀 일괄 주문은 한 번의 접수에 여러 배송 행이 포함되므로 두 지표를 함께 봐야 합니다.</div>',
            unsafe_allow_html=True,
        )

    # ================================================================== 2
    with tabs[1]:
        section("주문 접수 시간대", "주문회차 기준")
        hour_table = (
            period_sessions.groupby("order_hour", as_index=False)
            .agg(주문회차=("order_session_id", "nunique"), 배송행=("delivery_count", "sum"))
            .set_index("order_hour")
            .reindex(range(24), fill_value=0)
            .reset_index()
        )
        hour_table["주문회차 비중"] = hour_table["주문회차"] / hour_table["주문회차"].sum()
        hour_table["누적 접수 비중"] = hour_table["주문회차 비중"].cumsum()
        top_hours = hour_table.nlargest(3, "주문회차")
        before_noon = hour_table.loc[hour_table["order_hour"].le(11), "주문회차"].sum() / hour_table["주문회차"].sum()

        insight_cards([
            ("최대 접수 시간", f"{int(top_hours.iloc[0]['order_hour']):02d}시 · {int(top_hours.iloc[0]['주문회차']):,}회", "주문회차 기준 최대 한 시간 구간입니다."),
            ("오전 11시까지", fmt_pct(before_noon), "전체 주문회차 중 11:59 이전에 접수된 비중입니다."),
            ("2위 시간", f"{int(top_hours.iloc[1]['order_hour']):02d}시 · {int(top_hours.iloc[1]['주문회차']):,}회" if len(top_hours) > 1 else "–", "피크 한 시간만이 아니라 인접 시간대까지 인력을 배치합니다."),
        ])

        a, b = st.columns(2)
        with a:
            fig = go.Figure()
            fig.add_bar(x=hour_table["order_hour"], y=hour_table["주문회차"], name="주문회차", marker_color=SEA)
            fig.add_scatter(x=hour_table["order_hour"], y=hour_table["배송행"], name="배송 행", mode="lines+markers", line=dict(color=ORANGE, width=2), yaxis="y2")
            fig.update_layout(title="시간대별 주문회차와 배송 물량", yaxis2=dict(overlaying="y", side="right", showgrid=False), hovermode="x unified")
            fig.update_xaxes(dtick=1)
            chart(fig, 370)
        with b:
            fig = px.line(hour_table, x="order_hour", y="누적 접수 비중", markers=True, title="시간대별 누적 접수 비중")
            fig.update_traces(line_color=SEA, line_width=3)
            fig.update_yaxes(tickformat=".0%", range=[0, 1.03])
            fig.update_xaxes(dtick=1)
            fig.add_hline(y=0.8, line_dash="dash", line_color=AMBER, annotation_text="80%")
            chart(fig, 370)

        heat = (
            period_sessions.pivot_table(
                index="order_weekday", columns="order_hour", values="order_session_id", aggfunc="nunique", fill_value=0
            )
            .reindex(WEEKDAYS)
            .reindex(columns=range(24), fill_value=0)
        )
        fig = go.Figure(
            data=go.Heatmap(
                z=heat.values,
                x=[f"{h:02d}" for h in heat.columns],
                y=heat.index.astype(str),
                colorscale=[[0, "#0F172A"], [0.35, "#17314A"], [0.7, SEA], [1, PURPLE]],
                colorbar=dict(title="주문회차"),
                hovertemplate="%{y} %{x}시<br>주문회차 %{z:,}<extra></extra>",
            )
        )
        fig.update_layout(title="요일 × 시간대 주문 집중도")
        chart(fig, 400)

        a, b = st.columns(2)
        with a:
            channel_hour = period_sessions.groupby(["order_hour", "channel"]).size().reset_index(name="주문회차")
            fig = px.line(channel_hour, x="order_hour", y="주문회차", color="channel", markers=True, title="접수 형태별 시간대 패턴", color_discrete_sequence=SERIES)
            fig.update_xaxes(dtick=1)
            chart(fig, 350)
        with b:
            weekday_delivery = (
                period_sessions.groupby("delivery_weekday", observed=False)["delivery_count"].sum()
                .reindex(WEEKDAYS, fill_value=0)
                .reset_index(name="배송행")
            )
            fig = px.bar(weekday_delivery, x="delivery_weekday", y="배송행", title="배송 요일별 처리 물량")
            fig.update_traces(marker_color=INK_SOFT)
            chart(fig, 350)

        section("접수일부터 배송일까지", "주문회차 기준")
        lead = period_sessions["lead_time_days"].value_counts().sort_index().reset_index()
        lead.columns = ["리드타임", "주문회차"]
        lead["표시"] = lead["리드타임"].map(lambda x: "당일" if x == 0 else f"D+{int(x)}")
        a, b = st.columns([1.1, 1])
        with a:
            fig = px.bar(lead, x="표시", y="주문회차", title="주문 접수일 → 배송일 분포")
            fig.update_traces(marker_color=SEA)
            chart(fig, 330)
        with b:
            day_rank = (
                period_sessions.groupby(ref_col, as_index=False)
                .agg(주문회차=("order_session_id", "nunique"), 배송행=("delivery_count", "sum"), 활성고객=("customer_id", "nunique"))
                .sort_values("배송행", ascending=False)
                .head(15)
            )
            day_rank[ref_col] = pd.to_datetime(day_rank[ref_col]).dt.strftime("%Y-%m-%d")
            st.markdown("**물량 상위 15일**")
            st.dataframe(day_rank, hide_index=True, use_container_width=True, height=330)

    # ================================================================== 3
    with tabs[2]:
        conversions = repeat_conversion(history, end_ts)
        conversion_map = dict(zip(conversions["기간"], conversions["전환율"]))
        second_gaps = (
            history.sort_values(["customer_id", "order_datetime"])
            .groupby("customer_id")["order_datetime"]
            .apply(lambda x: (x.iloc[1] - x.iloc[0]).total_seconds() / 86_400 if len(x) >= 2 else np.nan)
            .dropna()
        )
        median_second = second_gaps.median() if not second_gaps.empty else np.nan
        all_gaps = history["gap_days"].dropna()

        cols = st.columns(6)
        cols[0].metric("재주문 고객률", fmt_pct(active_customer_summary["repeat_customer"].mean()))
        cols[1].metric("재주문회차 비중", fmt_pct(period_sessions["is_repeat_order"].mean()))
        cols[2].metric("두 번째 주문 중앙값", fmt_days(median_second))
        cols[3].metric("7일 재주문", fmt_pct(conversion_map.get("7일", 0)))
        cols[4].metric("30일 재주문", fmt_pct(conversion_map.get("30일", 0)))
        cols[5].metric("90일 재주문", fmt_pct(conversion_map.get("90일", 0)))

        st.markdown(
            '<div class="note"><b>재주문률 계산:</b> 고객+접수시각으로 만든 주문회차를 사용합니다. '
            '30일 재주문 전환율은 첫 주문 후 30일 이상 관찰 가능한 고객만 분모에 포함하므로 최근 신규 고객 때문에 비율이 낮아지는 문제를 줄였습니다.</div>',
            unsafe_allow_html=True,
        )

        a, b = st.columns([1.15, 1])
        with a:
            curve = conversion_curve(history, end_ts)
            fig = px.line(curve, x="days", y="전환율", markers=True, title="첫 주문 후 누적 재주문 전환 곡선")
            fig.update_traces(line_color=SEA, line_width=3)
            fig.update_yaxes(tickformat=".0%", range=[0, min(1, max(0.1, curve["전환율"].max() * 1.15))])
            fig.update_xaxes(tickmode="array", tickvals=[1, 7, 14, 30, 60, 90])
            chart(fig, 380)
        with b:
            st.markdown("**기간별 재주문 전환율**")
            conv_show = conversions.copy()
            conv_show["전환율"] = conv_show["전환율"].map(lambda x: f"{x * 100:.1f}%")
            st.dataframe(conv_show, hide_index=True, use_container_width=True, height=330)

        section("월별 코호트 유지율", "첫 주문 월=M+0")
        cohort = cohort_retention(history, start_ts, end_ts)
        if cohort.empty:
            st.info("코호트 분석에 충분한 데이터가 없습니다.")
        else:
            fig = go.Figure(
                data=go.Heatmap(
                    z=cohort.values,
                    x=cohort.columns,
                    y=cohort.index,
                    zmin=0,
                    zmax=1,
                    colorscale=[[0, "#0F172A"], [0.45, "#17314A"], [0.75, SEA], [1, PURPLE]],
                    text=np.vectorize(lambda x: f"{x * 100:.0f}%")(cohort.values),
                    texttemplate="%{text}",
                    hovertemplate="코호트 %{y}<br>%{x} 유지율 %{z:.1%}<extra></extra>",
                    colorbar=dict(tickformat=".0%", title="유지율"),
                )
            )
            fig.update_layout(title="첫 주문 월별 고객 유지율")
            chart(fig, max(310, 55 * len(cohort.index) + 100))

        a, b = st.columns(2)
        with a:
            nr = monthly_new_returning(history)
            fig = go.Figure()
            fig.add_bar(x=nr["월"], y=nr["신규 고객"], name="신규 고객", marker_color=ORANGE)
            fig.add_bar(x=nr["월"], y=nr["재주문 고객"], name="재주문 고객", marker_color=SEA)
            fig.update_layout(title="월별 신규 고객과 재주문 고객", barmode="stack")
            chart(fig, 360)
        with b:
            freq = frequency_bands(customer_summary)
            fig = px.bar(freq, x="주문회차 구간", y="고객 수", title="누적 주문회차별 고객 분포")
            fig.update_traces(marker_color=INK_SOFT)
            chart(fig, 360)

        a, b = st.columns(2)
        with a:
            gap_view = history.dropna(subset=["gap_days"]).copy()
            gap_view = gap_view[gap_view["gap_days"].between(0, 90)]
            fig = px.histogram(
                gap_view,
                x="gap_days",
                color="customer_type",
                nbins=45,
                barmode="overlay",
                opacity=0.65,
                title="주문 간격 분포 — 90일 이내",
                color_discrete_sequence=[SEA, ORANGE],
            )
            chart(fig, 360)
        with b:
            type_repeat = (
                customer_summary.groupby("customer_type", as_index=False)
                .agg(
                    고객수=("customer_id", "nunique"),
                    재주문고객=("repeat_customer", "sum"),
                    주문회차=("order_sessions", "sum"),
                    주문간격중앙값=("median_gap_days", "median"),
                )
            )
            type_repeat["재주문고객률"] = type_repeat["재주문고객"] / type_repeat["고객수"]
            fig = px.bar(type_repeat, x="customer_type", y="재주문고객률", text_auto=".1%", title="고객 유형별 재주문 고객률")
            fig.update_traces(marker_color=[SEA if x == "사업자" else ORANGE for x in type_repeat["customer_type"]])
            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            chart(fig, 360)

        top_repeat = customer_summary[customer_summary["repeat_customer"]].nlargest(30, "order_sessions").copy()
        top_repeat = top_repeat[[
            "customer_id", "customer_type", "order_sessions", "delivery_count", "median_gap_days",
            "recency_days", "preferred_weekday", "preferred_hour", "primary_channel", "segment"
        ]]
        top_repeat.columns = ["고객", "유형", "주문회차", "배송행", "주문간격 중앙값", "무주문일", "선호 요일", "선호 시간", "주 접수형태", "세그먼트"]
        st.markdown("**재주문 빈도 상위 고객**")
        st.dataframe(top_repeat, hide_index=True, use_container_width=True, height=430)

    # ================================================================== 4
    with tabs[3]:
        eligible_members = (
            members[
                members["join_datetime"].notna()
                & members["join_datetime"].le(end_ts)
                & members["customer_type"].isin(selected_types)
            ]
            if not members.empty
            else pd.DataFrame()
        )
        ordered_member_ids = set(history["customer_id"])
        activated = len(set(eligible_members["customer_id"]) & ordered_member_ids) if len(eligible_members) else 0
        inactive = max(0, len(eligible_members) - activated)
        risk_count = int(customer_summary["alert_level"].eq("위험").sum())
        care_count = int(customer_summary["alert_level"].eq("관심필요").sum())
        hhi = hhi_share(history.groupby("customer_id")["delivery_count"].sum())

        cols = st.columns(6)
        cols[0].metric("기준일 가입회원", f"{len(eligible_members):,}명")
        cols[1].metric("주문 경험 회원", f"{activated:,}명", f"활성화율 {safe_div(activated, len(eligible_members))*100:.1f}%" if len(eligible_members) else None)
        cols[2].metric("미주문 회원", f"{inactive:,}명")
        cols[3].metric("위험 고객", f"{risk_count:,}곳")
        cols[4].metric("관심필요", f"{care_count:,}곳")
        cols[5].metric("집중도 HHI", f"{hhi:,.0f}", help="배송 행 고객점유율 제곱합×10,000. 값이 높을수록 특정 고객 의존도가 큼")

        seg_order = ["핵심고객", "충성고객", "재이용고객", "신규·첫주문", "관심필요", "이탈위험", "일회성·미재주문", "기타"]
        seg = customer_summary["segment"].value_counts().reindex(seg_order).fillna(0).astype(int)
        pills = '<div class="segment-row">' + "".join(
            f'<span class="segment-pill">{name}<b>{count:,}</b></span>' for name, count in seg.items() if count
        ) + "</div>"
        st.markdown(pills, unsafe_allow_html=True)

        st.caption("위험·관심필요 고객 중 평소 주문주기 대비 지연이 큰 고객을 우선 표시합니다.")

        a, b = st.columns([1.15, 1])
        with a:
            attention = customer_summary[
                customer_summary["alert_level"].isin(["위험", "관심필요"])
            ].copy()
            attention["cycle_delay_ratio"] = attention["cycle_delay_ratio"].replace(
                [np.inf, -np.inf], np.nan
            )
            attention = attention.dropna(subset=["cycle_delay_ratio"])
            attention["_priority"] = attention["alert_level"].map(
                {"위험": 0, "관심필요": 1}
            )
            attention = (
                attention.sort_values(
                    ["_priority", "cycle_delay_ratio", "delivery_count"],
                    ascending=[True, False, False],
                )
                .head(15)
                .sort_values("cycle_delay_ratio", ascending=True)
            )

            if attention.empty:
                st.info("현재 우선 연락이 필요한 고객이 없습니다.")
            else:
                fig = px.bar(
                    attention,
                    x="cycle_delay_ratio",
                    y="customer_id",
                    color="alert_level",
                    orientation="h",
                    title="우선 연락 고객 — 주문주기 지연 상위 15곳",
                    labels={
                        "cycle_delay_ratio": "평소 주문주기 대비 지연배수",
                        "customer_id": "고객",
                        "alert_level": "경보",
                    },
                    hover_data={
                        "recency_days": ":.1f",
                        "median_gap_days": ":.1f",
                        "order_sessions": ":,",
                        "delivery_count": ":,",
                        "_priority": False,
                    },
                    color_discrete_map={"위험": RED, "관심필요": AMBER},
                )
                fig.add_vline(x=2, line_dash="dot", line_color=AMBER)
                fig.add_vline(x=3, line_dash="dash", line_color=RED)
                fig.update_layout(legend_title_text="", bargap=0.34)
                chart(fig, 430)
        with b:
            seg_df = seg[seg.gt(0)].rename_axis("세그먼트").reset_index(name="고객 수")
            seg_df = seg_df.sort_values("고객 수")
            fig = px.bar(
                seg_df,
                x="고객 수",
                y="세그먼트",
                orientation="h",
                title="고객 세그먼트 구성",
            )
            color_map = {
                "이탈위험": RED,
                "관심필요": AMBER,
                "핵심고객": GREEN,
                "충성고객": SEA,
                "재이용고객": BLUE,
            }
            fig.update_traces(
                marker_color=[color_map.get(x, "#7A8290") for x in seg_df["세그먼트"]]
            )
            chart(fig, 430)

        section("고객 경보 목록", "개인별 평소 주문주기 반영")
        alert_filter = st.radio("경보 등급", ["전체", "위험", "관심필요", "정상"], horizontal=True, index=0)
        alert_view = customer_summary.copy()
        if alert_filter != "전체":
            alert_view = alert_view[alert_view["alert_level"].eq(alert_filter)]
        alert_priority = {"위험": 0, "관심필요": 1, "정상": 2}
        alert_view["_alert_priority"] = alert_view["alert_level"].map(alert_priority).fillna(9)
        alert_view = alert_view.sort_values(
            ["_alert_priority", "delivery_count", "recency_days"],
            ascending=[True, False, False],
        )
        show_cols = [
            "customer_id", "customer_type", "alert_level", "segment", "order_sessions", "delivery_count",
            "median_gap_days", "recency_days", "cycle_delay_ratio", "last_order_date", "primary_channel"
        ]
        alert_show = alert_view[show_cols].copy()
        alert_show.columns = ["고객", "유형", "경보", "세그먼트", "주문회차", "배송행", "평소 주문주기", "무주문일", "주기 대비 지연배수", "마지막 주문일", "주 접수형태"]
        st.dataframe(
            alert_show,
            hide_index=True,
            use_container_width=True,
            height=430,
            column_config={
                "평소 주문주기": st.column_config.NumberColumn(format="%.1f일"),
                "무주문일": st.column_config.NumberColumn(format="%.1f일"),
                "주기 대비 지연배수": st.column_config.NumberColumn(format="%.1f배"),
                "배송행": st.column_config.ProgressColumn(min_value=0, max_value=max(1, int(alert_show["배송행"].max()))),
            },
        )

        section("고객 상세 조회")
        customer_options = customer_summary.sort_values("delivery_count", ascending=False)["customer_id"].tolist()
        selected_customer = st.selectbox("고객", customer_options, index=0)
        one = customer_summary[customer_summary["customer_id"].eq(selected_customer)].iloc[0]
        one_history = history[history["customer_id"].eq(selected_customer)].sort_values("order_datetime")
        c = st.columns(6)
        c[0].metric("누적 주문회차", f"{int(one['order_sessions']):,}회")
        c[1].metric("누적 배송행", f"{int(one['delivery_count']):,}건")
        c[2].metric("평소 주문주기", fmt_days(one["median_gap_days"]))
        c[3].metric("현재 무주문", fmt_days(one["recency_days"]))
        c[4].metric("선호 시간", f"{int(float(one['preferred_hour'])):02d}시" if str(one["preferred_hour"]) not in {"", "nan", "<NA>"} else "–")
        c[5].metric("경보", str(one["alert_level"]))

        a, b = st.columns([1.25, 1])
        with a:
            customer_month = (
                one_history.groupby(one_history["order_datetime"].dt.to_period("M").astype(str))
                .agg(주문회차=("order_session_id", "nunique"), 배송행=("delivery_count", "sum"))
                .reset_index(names="월")
            )
            fig = go.Figure()
            fig.add_bar(x=customer_month["월"], y=customer_month["배송행"], name="배송 행", marker_color=SEA)
            fig.add_scatter(x=customer_month["월"], y=customer_month["주문회차"], name="주문회차", mode="lines+markers", line=dict(color=ORANGE), yaxis="y2")
            fig.update_layout(title=f"{selected_customer} 월별 주문 이력", yaxis2=dict(overlaying="y", side="right", showgrid=False))
            chart(fig, 350)
        with b:
            detail = one_history[["order_datetime", "delivery_date", "channel", "delivery_count", "quantity", "gap_days", "order_number"]].copy().tail(30)
            detail.columns = ["접수시각", "배송일", "접수형태", "배송행", "수량", "이전 주문과 간격", "누적 주문번호"]
            st.dataframe(detail, hide_index=True, use_container_width=True, height=350)

    # ================================================================== 5
    with tabs[4]:
        section("접수 형태별 운영 구조")
        channel_ops = (
            period_sessions.groupby("channel", as_index=False)
            .agg(
                주문회차=("order_session_id", "nunique"),
                배송행=("delivery_count", "sum"),
                수량=("quantity", "sum"),
                활성고객=("customer_id", "nunique"),
                평균묶음=("delivery_count", "mean"),
                다건주문률=("is_multi_delivery", "mean"),
                당일배송률=("lead_time_days", lambda x: x.eq(0).mean()),
            )
        )
        channel_ops["다건주문률"] = channel_ops["다건주문률"] * 100
        channel_ops["당일배송률"] = channel_ops["당일배송률"] * 100
        st.dataframe(
            channel_ops,
            hide_index=True,
            use_container_width=True,
            column_config={
                "평균묶음": st.column_config.NumberColumn(format="%.2f건"),
                "다건주문률": st.column_config.NumberColumn(format="%.1f%%"),
                "당일배송률": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

        a, b = st.columns(2)
        with a:
            batch = period_sessions["delivery_count"].clip(upper=20)
            batch_label = np.where(period_sessions["delivery_count"].gt(20), "20건 초과", batch.astype(int).astype(str) + "건")
            batch_df = pd.Series(batch_label).value_counts().rename_axis("배송행/회").reset_index(name="주문회차")
            order_categories = [f"{i}건" for i in range(1, 21)] + ["20건 초과"]
            batch_df["배송행/회"] = pd.Categorical(batch_df["배송행/회"], categories=order_categories, ordered=True)
            batch_df = batch_df.sort_values("배송행/회")
            fig = px.bar(batch_df, x="배송행/회", y="주문회차", title="한 번의 주문에 포함된 배송 행 수")
            fig.update_traces(marker_color=SEA)
            fig.update_xaxes(tickangle=-45)
            chart(fig, 360)
        with b:
            qty = period_orders["quantity"].clip(upper=10)
            qty_label = np.where(period_orders["quantity"].gt(10), "10 초과", qty.round().astype(int).astype(str))
            qty_df = pd.Series(qty_label).value_counts().rename_axis("수량").reset_index(name="배송행")
            fig = px.bar(qty_df, x="수량", y="배송행", title="배송 행별 수량 분포")
            fig.update_traces(marker_color=INK_SOFT)
            chart(fig, 360)

        section("품목 분석", "키워드 기반 운영용 분류")
        a, b = st.columns([1, 1.2])
        with a:
            category = period_orders["item_category"].value_counts().reset_index()
            category.columns = ["품목 카테고리", "배송행"]
            fig = px.bar(category.sort_values("배송행"), x="배송행", y="품목 카테고리", orientation="h", title="품목 카테고리별 배송 행")
            fig.update_traces(marker_color=SEA)
            chart(fig, 390)
        with b:
            cat_month = (
                period_orders.assign(월=period_orders["delivery_date"].dt.to_period("M").astype(str))
                .groupby(["월", "item_category"]).size().reset_index(name="배송행")
            )
            keep = period_orders["item_category"].value_counts().head(7).index
            cat_month["카테고리"] = cat_month["item_category"].where(cat_month["item_category"].isin(keep), "그 외")
            cat_month = cat_month.groupby(["월", "카테고리"], as_index=False)["배송행"].sum()
            fig = px.line(cat_month, x="월", y="배송행", color="카테고리", markers=True, title="품목 카테고리 월간 추이", color_discrete_sequence=SERIES)
            chart(fig, 390)

        top_items = (
            period_orders[period_orders["item_name"].ne("") & ~period_orders["item_name"].isin([".", "-"])]
            ["item_name"].value_counts().head(30).reset_index()
        )
        top_items.columns = ["품목명 원문", "배송행"]
        st.markdown("**품목명 상위 30개**")
        st.dataframe(top_items, hide_index=True, use_container_width=True, height=430)

        section("배송 요청사항")
        request_summary = []
        for label in REQUEST_RULES:
            count = int(period_orders[f"request_{label}"].sum())
            request_summary.append({"요청 유형": label, "배송행": count, "비중": safe_div(count, len(period_orders))})
        req_df = pd.DataFrame(request_summary).sort_values("배송행", ascending=False)
        a, b = st.columns([1, 1.3])
        with a:
            fig = px.bar(req_df.sort_values("배송행"), x="배송행", y="요청 유형", orientation="h", title="요청사항 키워드 분류")
            fig.update_traces(marker_color=ORANGE)
            chart(fig, 330)
        with b:
            request_top = (
                period_orders[period_orders["request_text"].ne("")]["request_text"]
                .value_counts().head(20).reset_index()
            )
            request_top.columns = ["요청사항 원문", "배송행"]
            st.dataframe(request_top, hide_index=True, use_container_width=True, height=330)

        section("데이터 품질")
        quality = bundle.quality.copy()
        quality["결측률 표시"] = quality["결측률"].map(lambda x: f"{x * 100:.1f}%")
        st.dataframe(quality[["항목", "전체 행", "결측 행", "결측률 표시"]], hide_index=True, use_container_width=True)

        visible_duplicates = int(bundle.orders.duplicated("visible_fingerprint", keep=False).sum())
        address_missing = quality.loc[quality["항목"].isin(["수거지 주소", "배송지 주소"]), "결측률"].max()
        if address_missing >= 0.95:
            st.markdown(
                '<div class="note danger-note"><b>지역 분석 제외:</b> 수거지·배송지 주소가 대부분 또는 전부 비어 있습니다. '
                '현재 파일만으로 지역별 주문량을 표시하면 허위 분석이 되므로 화면에서 제외했습니다.</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="note"><b>표면상 중복 행:</b> 동일하게 보이는 행이 {visible_duplicates:,}건 있습니다. '
            '다만 주소가 비식별화되면 서로 다른 배송지가 같은 행처럼 보일 수 있어 자동 삭제하지 않습니다.</div>',
            unsafe_allow_html=True,
        )

    # ================================================================== 6
    with tabs[5]:
        report = build_report(
            period_sessions=period_sessions,
            period_orders=period_orders,
            history=history,
            customer_summary=customer_summary,
            members=members,
            quality=bundle.quality,
            start_date=start_ts,
            end_date=end_ts,
            reference=reference,
            source_name=bundle.source_name,
        )
        d1, d2, d3 = st.columns([1, 1, 2])
        with d1:
            st.download_button(
                "분석보고서 MD",
                report.encode("utf-8-sig"),
                file_name=f"고객주문_분석보고서_{start_d}_{end_d}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with d2:
            package = build_download_zip(report, period_sessions, customer_summary, bundle.quality)
            st.download_button(
                "분석자료 ZIP",
                package,
                file_name=f"고객주문_분석자료_{start_d}_{end_d}.zip",
                mime="application/zip",
                use_container_width=True,
            )
        with d3:
            st.caption("ZIP에는 분석보고서, 주문회차, 고객분석, 데이터품질 CSV가 포함됩니다.")

        with st.container(border=True):
            st.markdown(report)

        section("분석용 데이터 미리보기")
        preview_tabs = st.tabs(["주문회차", "고객 요약", "품질 점검"])
        with preview_tabs[0]:
            st.dataframe(period_sessions.tail(500), hide_index=True, use_container_width=True, height=420)
        with preview_tabs[1]:
            st.dataframe(customer_summary, hide_index=True, use_container_width=True, height=420)
        with preview_tabs[2]:
            st.dataframe(bundle.quality, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()