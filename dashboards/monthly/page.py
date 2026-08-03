"""월간리포트 화면."""

import streamlit as st


def render(_theme):
    st.title("📅 월간리포트")
    st.info("월간 분석 결과를 자동으로 정리하는 대시보드입니다. 현재 준비 중입니다.")
    st.markdown("""
    앞으로 제공할 기능:

    - 월별 고객·매출 핵심 지표
    - 전월 대비 증감 분석
    - 월간 리포트 미리보기 및 다운로드
    """)
