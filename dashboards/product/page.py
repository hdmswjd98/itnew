"""품목 자동분류 및 분석 화면."""

import streamlit as st


def render(_theme):
    st.title("📦 품목 자동분류 및 분석")
    st.info("품목 자동분류와 수요 분석 대시보드입니다. 현재 준비 중입니다.")
    st.markdown("""
    앞으로 제공할 기능:

    - 품목명 자동 카테고리 분류
    - 품목별 주문량·매출 분석
    - 인기 품목과 수요 추이 확인
    """)
