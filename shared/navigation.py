"""전체 대시보드에서 사용하는 사이드바 내비게이션."""

import streamlit as st


DASHBOARDS = {
    "customer": "👥 고객분석",
    "monthly": "📅 월간리포트",
    "product": "📦 품목 자동분류 및 분석",
}


def _go_to(dashboard):
    st.query_params.clear()
    if dashboard != "customer":
        st.query_params["dashboard"] = dashboard
    st.session_state["selected_group"] = "전체"
    st.rerun()


def render_sidebar():
    """사이드바를 그리고 현재 선택된 대시보드 키를 반환한다."""
    current = st.query_params.get("dashboard", "customer")
    if current not in DASHBOARDS:
        current = "customer"

    with st.sidebar:
        st.title("🏢 잇뉴")
        st.caption("통합 분석 플랫폼")
        st.divider()

        if st.button("🏠 홈으로 돌아가기", width="stretch"):
            _go_to("customer")

        st.caption("대시보드")
        for key, label in DASHBOARDS.items():
            selected = key == current
            if st.button(
                label,
                key=f"nav_{key}",
                type="primary" if selected else "secondary",
                width="stretch",
            ) and not selected:
                _go_to(key)

    return current
