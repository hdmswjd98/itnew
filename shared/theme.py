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
      }
      .stApp, [data-testid="stAppViewContainer"] {
        background: var(--app-bg);
        color: var(--text-color);
      }
      [data-testid="stHeader"] { background: var(--app-bg); }
      [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background: var(--sidebar-bg);
      }
      [data-testid="stSidebar"] * { color: var(--text-color); }
      [data-testid="stMetric"], [data-testid="stDataFrame"] {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 10px;
      }
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
      .section-title { color: var(--text-color); font-size: 1.1rem; font-weight: 600; }
      .progress-track { background: var(--border-color); border-radius: 4px; height: 8px; }
      .progress-fill { height: 100%; border-radius: 4px; }
      iframe[title="streamlit_plotly_events.plotly_events"] {
        background: var(--app-bg) !important;
        border: 0 !important;
        border-radius: 12px;
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
    }
    for placeholder, color in replacements.items():
        css = css.replace(placeholder, color)
    st.markdown(css, unsafe_allow_html=True)
    return theme
