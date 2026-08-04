"""잇뉴 통합 분석 플랫폼의 Streamlit 진입점."""

import streamlit as st

from dashboards.customer.page import render as render_customer
from dashboards.monthly.page import render as render_monthly
from dashboards.product.page import render as render_product
from shared.navigation import render_sidebar
from shared.theme import render_theme


st.set_page_config(
    page_title="잇뉴 통합 분석 플랫폼",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

dashboard = render_sidebar()
theme = render_theme()

pages = {
    "customer": render_customer,
    "monthly": render_monthly,
    "product": render_product,
}
pages[dashboard](theme)
