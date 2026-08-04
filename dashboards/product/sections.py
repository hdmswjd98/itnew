"""품목 자동분류 현황, 수기 검토, 기업 규칙 화면."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.product.classifier import classify_products
from services.product.rules import load_company_rules, save_exact_rules
from shared.paths import OUTPUT_DIR


@st.cache_data(ttl=60)
def load_classification():
    path = OUTPUT_DIR / "product_classification.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def _review_table(classification):
    review = classification[classification["대분류"].eq("기타")].copy()
    if review.empty:
        return review
    return (
        review.groupby("item_name", dropna=False)
        .agg(주문_건수=("order_id", "count"), 최근_주문일=("order_date", "max"))
        .reset_index()
        .sort_values(["주문_건수", "item_name"], ascending=[False, True])
        .rename(columns={"item_name": "품목명"})
    )


def _category_map(classification):
    pairs = classification.loc[
        ~classification["대분류"].eq("기타"), ["대분류", "중분류"]
    ].drop_duplicates()
    return {
        main: sorted(group["중분류"].loc[lambda values: values.ne("")].unique())
        for main, group in pairs.groupby("대분류", sort=True)
    }


def _render_status(classification):
    summary = (
        classification.groupby(["대분류", "중분류"], as_index=False)
        .agg(주문_건수=("order_id", "count"), 고유_품목수=("item_name", "nunique"))
        .sort_values("주문_건수", ascending=False)
    )
    main_summary = summary.groupby("대분류", as_index=False)["주문_건수"].sum()
    figure = px.bar(
        main_summary.sort_values("주문_건수"),
        x="주문_건수",
        y="대분류",
        orientation="h",
        title="대분류별 주문 품목 현황",
    )
    figure.update_layout(height=max(420, len(main_summary) * 35), yaxis_title=None)
    st.plotly_chart(figure, width="stretch")
    st.markdown("### 카테고리별 상세")
    st.dataframe(summary, width="stretch", hide_index=True)


def _render_review(classification):
    review_table = _review_table(classification)
    st.markdown("### ⚠️ 검토 필요 품목")
    st.caption("검색한 목록에서 품목을 체크한 뒤 같은 카테고리로 일괄 등록할 수 있습니다.")
    if review_table.empty:
        st.success("검토가 필요한 품목이 없습니다.")
        return

    search = st.text_input("검토 목록 검색", placeholder="예: 갈치, 김치, 포장박스")
    visible = review_table
    if search:
        visible = visible[visible["품목명"].str.contains(search, case=False, na=False)]

    visible = visible.reset_index(drop=True)
    selection_key = "product_review_selection"
    previous_search = st.session_state.get("product_review_previous_search")
    if previous_search != search:
        st.session_state[selection_key] = {"selection": {"rows": []}}
        st.session_state["product_review_previous_search"] = search

    selection_controls = st.columns([1, 1, 3])
    with selection_controls[0]:
        if st.button("검색 결과 전체 선택", width="stretch", disabled=visible.empty):
            st.session_state[selection_key] = {
                "selection": {"rows": list(range(len(visible)))}
            }
    with selection_controls[1]:
        if st.button("선택 해제", width="stretch", disabled=visible.empty):
            st.session_state[selection_key] = {"selection": {"rows": []}}

    selection_event = st.dataframe(
        visible,
        width="stretch",
        hide_index=True,
        column_config={
            "주문_건수": st.column_config.NumberColumn(format="%d건"),
            "최근_주문일": "최근 주문일",
        },
        key=selection_key,
        on_select="rerun",
        selection_mode="multi-row",
    )
    selected_rows = selection_event.selection.rows
    selected_items = visible.iloc[selected_rows]["품목명"].tolist() if selected_rows else []
    st.caption(f"검색 결과 {len(visible):,}개 · 선택 {len(selected_items):,}개")

    category_map = _category_map(classification)
    direct_option = "＋ 직접 입력"
    category_columns = st.columns(2)
    with category_columns[0]:
        main_choice = st.selectbox("대분류", [*category_map, direct_option])
        main_category = (
            st.text_input("새 대분류", placeholder="예: 건강식품")
            if main_choice == direct_option
            else main_choice
        )
    with category_columns[1]:
        sub_options = category_map.get(main_category, [])
        sub_choice = st.selectbox("중분류", [*sub_options, direct_option])
        subcategory = (
            st.text_input("새 중분류", placeholder="예: 영양제")
            if sub_choice == direct_option
            else sub_choice
        )

    if st.button(
        f"선택한 {len(selected_items):,}개 품목 일괄 등록",
        type="primary",
        disabled=not selected_items or not main_category or not subcategory,
        width="stretch",
    ):
        try:
            with st.spinner("수기 분류를 저장하고 전체 품목에 다시 적용하는 중입니다..."):
                save_exact_rules(selected_items, main_category, subcategory)
                result = classify_products()
                if not result.get("ok"):
                    st.error(result["message"])
                    return
                load_classification.clear()
                st.session_state["product_review_saved"] = (
                    f"선택한 {len(selected_items):,}개 품목을 "
                    f"{main_category} / {subcategory}(으)로 저장했습니다."
                )
                st.rerun()
        except Exception as error:
            st.error(f"분류를 저장하지 못했습니다: {error}")



def _render_rules():
    st.markdown("### 기업 우선 분류 규칙")
    st.caption("수기 검토에서 저장한 규칙은 기본 자동분류 규칙보다 먼저 적용됩니다.")
    rules = pd.DataFrame(load_company_rules())
    if rules.empty:
        st.info("등록된 기업 규칙이 없습니다.")
    else:
        st.dataframe(rules, width="stretch", hide_index=True)


def render_overview():
    classification = load_classification()
    if classification.empty or "대분류" not in classification.columns:
        st.info("분류 결과가 없습니다. 홈에서 데이터 새로고침을 실행해주세요.")
        return

    saved_message = st.session_state.pop("product_review_saved", None)
    if saved_message:
        st.success(saved_message)

    total = len(classification)
    review_count = int(classification["대분류"].eq("기타").sum())
    classified_count = total - review_count
    metric_columns = st.columns(4)
    metric_columns[0].metric("전체 주문 품목", f"{total:,}건")
    metric_columns[1].metric("고유 품목명", f"{classification['item_name'].nunique():,}개")
    metric_columns[2].metric("자동분류", f"{classified_count:,}건", f"{classified_count / total:.1%}")
    metric_columns[3].metric("검토 필요", f"{review_count:,}건", f"{review_count / total:.1%}", delta_color="inverse")

    requested_view = "검토 필요" if st.query_params.get("review") == "unclassified" else "분류 현황"
    if "product_view" not in st.session_state:
        st.session_state["product_view"] = requested_view
    view = st.radio(
        "품목분석 메뉴",
        ["분류 현황", "검토 필요", "기업 규칙"],
        horizontal=True,
        label_visibility="collapsed",
        key="product_view",
    )
    st.divider()
    if view == "분류 현황":
        _render_status(classification)
    elif view == "검토 필요":
        _render_review(classification)
    else:
        _render_rules()
