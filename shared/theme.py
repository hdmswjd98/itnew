"""라이트·다크 테마 선택과 공통 스타일."""

import streamlit as st


def render_theme():
    """테마 토글과 CSS를 렌더링하고 현재 색상표를 반환한다."""
    _, toggle_column = st.columns([8, 2])
    with toggle_column:
        st.toggle("☀️ 라이트 모드", key="light_theme")

    light = st.session_state.get("light_theme", False)
    theme = {
        "bg": "#f5f7fb" if light else "#0f1117",
        "sidebar": "#ffffff" if light else "#151824",
        "card": "#ffffff" if light else "#1a1d2e",
        "border": "#dfe3ec" if light else "#2a2d3e",
        "text": "#1f2430" if light else "#e4e6f0",
        "muted": "#687086" if light else "#8b8fa8",
        "kpi_card": "#ffffff" if light else "#292d44",
        "kpi_value": "#171a27" if light else "#f7f8ff",
        "kpi_muted": "#73798a" if light else "#bcc1d5",
        "plotly_template": "plotly_white" if light else "plotly_dark",
    }

    css = """
    <style>
      :root {
        --app-bg: __BG__;
        --sidebar-bg: __SIDEBAR__;
        --card-bg: __CARD__;
        --border-color: __BORDER__;
        --text-color: __TEXT__;
        --muted-color: __MUTED__;
        --kpi-card-bg: __KPI_CARD__;
        --kpi-value-color: __KPI_VALUE__;
        --kpi-muted-color: __KPI_MUTED__;
      }
      .stApp, [data-testid="stAppViewContainer"] {
        background: var(--app-bg);
        color: var(--text-color);
      }
      [data-testid="stHeader"] { background: var(--app-bg); }
      [data-testid="stAppViewContainer"] h1,
      [data-testid="stAppViewContainer"] h2,
      [data-testid="stAppViewContainer"] h3,
      [data-testid="stAppViewContainer"] h4,
      [data-testid="stAppViewContainer"] p,
      [data-testid="stAppViewContainer"] label,
      [data-testid="stAppViewContainer"] li,
      [data-testid="stMarkdownContainer"],
      [data-testid="stCaptionContainer"],
      [data-testid="stMetricLabel"],
      [data-testid="stMetricValue"] {
        color: var(--text-color) !important;
      }
      [data-testid="stCaptionContainer"] p,
      [data-testid="stMetricDelta"] {
        color: var(--muted-color) !important;
      }
      [data-testid="stProgress"] p,
      [data-testid="stAlert"] p {
        color: var(--text-color) !important;
      }
      [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background: var(--sidebar-bg);
      }
      [data-testid="stSidebar"] * { color: var(--text-color); }
      [data-testid="stSidebar"] .stButton > button {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-color) !important;
      }
      [data-testid="stSidebar"] .stButton > button p {
        color: var(--text-color) !important;
        font-weight: 650 !important;
      }
      [data-testid="stSidebar"] .stButton > button[kind="primary"],
      [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        background: #ff4b4b !important;
        border-color: #ff4b4b !important;
      }
      [data-testid="stSidebar"] .stButton > button[kind="primary"] p,
      [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p {
        color: #ffffff !important;
      }
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: var(--muted-color) !important;
      }
      [data-testid="stMetric"], [data-testid="stDataFrame"] {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 10px;
      }
      [data-testid="stDataFrame"] > div,
      [data-testid="stDataFrame"] iframe {
        background: var(--card-bg) !important;
      }
      [data-baseweb="tab-list"] {
        gap: 6px;
        background: transparent;
      }
      [data-baseweb="tab"] {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 9px 9px 0 0;
        color: var(--text-color);
      }
      [data-baseweb="tab"] p { color: var(--text-color) !important; }
      [data-baseweb="tab"][aria-selected="true"] {
        background: #6c5ce7;
        color: #ffffff;
      }
      [data-baseweb="tab"][aria-selected="true"] p { color: #ffffff !important; }
      [data-testid="stToggle"] [data-baseweb="checkbox"] > div {
        border-color: var(--border-color) !important;
      }
      [data-testid="stToggle"] p { color: var(--text-color); }
      .kpi-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
      }
      .kpi-value { font-size: 2rem; font-weight: 700; margin: 6px 0; }
      .kpi-label { font-size: .75rem; color: var(--muted-color); }
      .kpi-sub { font-size: .8rem; color: var(--muted-color); margin-top: 4px; }
      .customer-kpi-group { margin: 0 0 40px; width: 100%; }
      .customer-kpi-group:last-child { margin-bottom: 0; }
      .customer-kpi-group-title {
        margin: 0 0 5px !important;
        font-size: 1.05rem !important;
        font-weight: 720 !important;
        color: var(--text-color) !important;
      }
      .customer-kpi-group-subtitle {
        margin: 0 0 16px !important;
        font-size: .76rem !important;
        line-height: 1.45 !important;
        color: var(--muted-color) !important;
      }
      .customer-kpi-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        column-gap: 16px;
        row-gap: 15px;
        align-items: stretch;
      }
      .customer-kpi-card {
        width: 100%;
        min-width: 0;
        min-height: 132px;
        box-sizing: border-box;
        padding: 18px 17px;
        border: 1px solid rgba(151, 142, 210, .30);
        border-radius: 15px;
        box-shadow: 0 9px 24px rgba(5, 8, 20, .16), inset 0 1px 0 rgba(255, 255, 255, .045);
        display: grid;
        grid-template-rows: 30px 35px 34px;
        align-content: center;
        align-items: start;
        position: relative;
        overflow: visible;
        z-index: 1;
      }
      .customer-kpi-card:hover,
      .customer-kpi-card:focus { z-index: 30; outline: none; }
      .customer-kpi-label {
        color: var(--kpi-muted-color) !important;
        font-size: .72rem !important;
        font-weight: 620;
        line-height: 1.25;
        margin: 0;
      }
      .customer-kpi-value {
        color: var(--kpi-value-color) !important;
        font-size: clamp(1.35rem, 2vw, 1.9rem) !important;
        font-weight: 820;
        letter-spacing: -.025em;
        line-height: 1.05;
        white-space: nowrap;
        text-shadow: 0 1px 8px rgba(0, 0, 0, .10);
      }
      .customer-kpi-basis {
        color: var(--kpi-muted-color) !important;
        font-size: .67rem !important;
        line-height: 1.3;
        margin: 7px 0 0;
      }
      .customer-kpi-card::after {
        content: attr(data-detail);
        position: absolute;
        left: 10px;
        right: 10px;
        bottom: calc(100% - 5px);
        padding: 9px 10px;
        border: 1px solid var(--border-color);
        border-radius: 9px;
        background: var(--sidebar-bg);
        color: var(--text-color);
        box-shadow: 0 10px 28px rgba(0, 0, 0, .28);
        font-size: .7rem;
        font-weight: 500;
        line-height: 1.45;
        opacity: 0;
        visibility: hidden;
        transform: translateY(5px);
        transition: opacity .16s ease, transform .16s ease, visibility .16s ease;
        pointer-events: none;
      }
      .customer-kpi-card:hover::after,
      .customer-kpi-card:focus::after {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
      }
      .analysis-note {
        position: relative;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        max-width: 100%;
        margin: 0 0 13px;
        color: var(--muted-color) !important;
        font-size: .76rem;
        line-height: 1.45;
        cursor: help;
        z-index: 2;
      }
      .analysis-note > span:first-child { color: var(--muted-color) !important; }
      .analysis-note-icon {
        color: var(--muted-color) !important;
        font-size: .78rem;
        opacity: .9;
      }
      .analysis-note:hover,
      .analysis-note:focus { z-index: 50; outline: none; }
      .analysis-note::after {
        content: attr(data-detail);
        position: absolute;
        left: 0;
        top: calc(100% + 7px);
        width: min(430px, 76vw);
        padding: 11px 12px;
        border: 1px solid var(--border-color);
        border-radius: 10px;
        background: var(--sidebar-bg);
        color: var(--text-color);
        box-shadow: 0 12px 30px rgba(0, 0, 0, .3);
        font-size: .72rem;
        font-weight: 500;
        line-height: 1.55;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-4px);
        transition: opacity .16s ease, transform .16s ease, visibility .16s ease;
        pointer-events: none;
      }
      .analysis-note:hover::after,
      .analysis-note:focus::after {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
      }
      .classification-criteria {
        margin: 10px 0 4px;
        padding: 13px 15px;
        border-left: 2px solid rgba(133, 117, 215, .55);
        border-radius: 0 9px 9px 0;
        background: rgba(112, 98, 180, .07);
        color: var(--kpi-muted-color) !important;
        font-size: .68rem;
        line-height: 1.62;
      }
      .classification-criteria div,
      .classification-criteria span {
        color: var(--kpi-muted-color) !important;
      }
      .classification-criteria b {
        color: var(--text-color) !important;
        font-weight: 680;
      }
      .classification-criteria-title,
      .classification-grade-title {
        color: var(--text-color) !important;
        font-weight: 700;
      }
      .classification-grade-title {
        margin-top: 7px;
        padding-top: 7px;
        border-top: 1px solid rgba(151, 142, 210, .18);
      }
      .classification-grade-title span {
        font-weight: 500;
        font-size: .64rem;
      }
      .gradient-blue-purple {
        background: linear-gradient(135deg, rgba(103, 92, 231, .27), rgba(91, 75, 180, .13)), var(--kpi-card-bg);
      }
      .gradient-navy-indigo {
        background: linear-gradient(135deg, rgba(58, 72, 145, .27), rgba(90, 78, 190, .13)), var(--kpi-card-bg);
      }
      .gradient-indigo-purple {
        background: linear-gradient(135deg, rgba(83, 73, 190, .27), rgba(122, 82, 190, .13)), var(--kpi-card-bg);
      }
      .gradient-teal-mint {
        background: linear-gradient(135deg, rgba(72, 86, 170, .25), rgba(112, 91, 196, .12)), var(--kpi-card-bg);
      }
      .gradient-cyan-blue {
        background: linear-gradient(135deg, rgba(66, 91, 175, .26), rgba(96, 83, 194, .12)), var(--kpi-card-bg);
      }
      .gradient-teal-green {
        background: linear-gradient(135deg, rgba(76, 88, 174, .25), rgba(116, 87, 194, .12)), var(--kpi-card-bg);
      }
      .gradient-blue-cyan {
        background: linear-gradient(135deg, rgba(69, 97, 184, .26), rgba(91, 82, 191, .12)), var(--kpi-card-bg);
      }
      .gradient-orange-red {
        background: linear-gradient(135deg, rgba(245, 137, 54, .29), rgba(218, 72, 86, .16)), var(--kpi-card-bg);
        border-color: rgba(235, 128, 91, .34);
      }
      .section-title { color: var(--text-color); font-size: 1.1rem; font-weight: 600; }
      .progress-track { background: var(--border-color); border-radius: 4px; height: 8px; }
      .progress-fill { height: 100%; border-radius: 4px; }
      iframe[title="streamlit_plotly_events.plotly_events"] {
        background: var(--app-bg) !important;
        border: 0 !important;
        border-radius: 12px !important;
        display: block !important;
        width: calc(100% + 4px) !important;
        max-width: none !important;
        margin: -2px !important;
        padding: 0 !important;
        color-scheme: dark;
      }
      [data-testid="stCustomComponentV1"]:has(iframe[title="streamlit_plotly_events.plotly_events"]),
      [data-testid="stCustomComponent"]:has(iframe[title="streamlit_plotly_events.plotly_events"]) {
        background: var(--app-bg) !important;
        border: 0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        padding: 0 !important;
        line-height: 0 !important;
      }
    </style>
    """
    replacements = {
        "__BG__": theme["bg"],
        "__SIDEBAR__": theme["sidebar"],
        "__CARD__": theme["card"],
        "__BORDER__": theme["border"],
        "__TEXT__": theme["text"],
        "__MUTED__": theme["muted"],
        "__KPI_CARD__": theme["kpi_card"],
        "__KPI_VALUE__": theme["kpi_value"],
        "__KPI_MUTED__": theme["kpi_muted"],
    }
    for placeholder, color in replacements.items():
        css = css.replace(placeholder, color)
    st.markdown(css, unsafe_allow_html=True)
    return theme
