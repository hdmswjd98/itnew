"""세 대시보드가 공통으로 사용하는 UI 조각."""

from html import escape

import streamlit as st


def section_heading(title, description=None):
    """일관된 섹션 제목과 설명을 표시한다."""
    st.markdown(f"## {escape(title)}")
    if description:
        st.caption(description)


def empty_state(message):
    """데이터가 없을 때 공통 안내를 표시한다."""
    st.info(message)
