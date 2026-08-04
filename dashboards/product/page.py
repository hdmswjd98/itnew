"""품목 자동분류 및 분석 화면."""

import streamlit as st

from dashboards.product.sections import render_overview


def render(_theme):
    st.title("📦 품목 자동분류 및 분석")
    render_overview()
