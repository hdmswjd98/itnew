"""월간 운영보고서 작성·미리보기·다운로드 화면."""

from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboards.monthly.report_export import create_excel_report, create_pdf_report
from dashboards.monthly.repository import ReportStoreError, get_report_store


CUSTOMER_DATA = Path(__file__).resolve().parents[1] / "customer" / "data"
OUTPUT_DIR = CUSTOMER_DATA / "output"
INPUT_DIR = CUSTOMER_DATA / "input"


@st.cache_data(ttl=60)
def load_monthly_source():
    merged_path = OUTPUT_DIR / "merged_data.csv"
    members_path = INPUT_DIR / "members.csv"
    merged = pd.read_csv(merged_path) if merged_path.exists() else pd.DataFrame()
    members = pd.read_csv(members_path) if members_path.exists() else pd.DataFrame()
    if "order_date_parsed" in merged.columns:
        merged["order_date_parsed"] = pd.to_datetime(merged["order_date_parsed"], errors="coerce")
    if "signup_date" in members.columns:
        members["signup_date"] = pd.to_datetime(members["signup_date"], errors="coerce")
    return merged, members


def _change(current, previous):
    if not previous:
        return None
    return (current - previous) / previous * 100


def _change_text(value):
    if value is None:
        return "비교 불가"
    return f"{value:+.1f}%"


def _one_column_table(title, text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return pd.DataFrame({title: lines or ["입력 내용 없음"]})


def build_report(month, merged, members, current_revenue, previous_revenue, issues, next_plan, requests):
    start = month.start_time
    end = month.end_time
    previous_month = month - 1
    current = merged[merged["order_date_parsed"].between(start, end)].copy()
    previous = merged[merged["order_date_parsed"].between(previous_month.start_time, previous_month.end_time)].copy()

    current_quantity = pd.to_numeric(current.get("order_quantity_num"), errors="coerce").sum()
    previous_quantity = pd.to_numeric(previous.get("order_quantity_num"), errors="coerce").sum()
    current_orders = len(current)
    previous_orders = len(previous)
    current_customers = current["customer_id"].nunique() if "customer_id" in current else 0
    previous_customers = previous["customer_id"].nunique() if "customer_id" in previous else 0
    unique_receipts = current.drop_duplicates(["customer_id", "order_date_parsed"]).shape[0] if len(current) else 0

    if len(members):
        total_members = members["customer_id"].nunique() if "customer_id" in members else len(members)
        new_members = members[members["signup_date"].between(start, end)]["customer_id"].nunique() if "signup_date" in members else 0
        if "member_type" in members:
            member_table = members["member_type"].fillna("미상").value_counts().rename_axis("회원 유형").reset_index(name="회원 수")
        else:
            member_table = pd.DataFrame({"회원 유형": ["전체 회원"], "회원 수": [total_members]})
    else:
        total_members, new_members = 0, 0
        member_table = pd.DataFrame({"회원 유형": ["회원 데이터 없음"], "회원 수": [0]})
    member_table = pd.concat([
        pd.DataFrame({"회원 유형": ["전체 회원", "당월 신규 회원", "당월 주문 고객"], "회원 수": [total_members, new_members, current_customers]}),
        member_table,
    ], ignore_index=True)

    if len(current) and "item_name" in current:
        product_table = current.assign(
            배송_수량=pd.to_numeric(current.get("order_quantity_num"), errors="coerce").fillna(0)
        ).groupby("item_name", as_index=False).agg(
            배송_건수=("order_id", "count"), 배송_수량=("배송_수량", "sum")
        ).sort_values(["배송_수량", "배송_건수"], ascending=False)
        product_table = product_table.rename(columns={"item_name": "품목명"})
    else:
        product_table = pd.DataFrame(columns=["품목명", "배송_건수", "배송_수량"])

    revenue_change = _change(current_revenue, previous_revenue)
    kpi_table = pd.DataFrame([
        ["당월 매출", f"{current_revenue:,.0f}원", "직접 입력"],
        ["전월 매출", f"{previous_revenue:,.0f}원", "직접 입력"],
        ["전월 대비 매출", _change_text(revenue_change), "(당월-전월)÷전월"],
        ["주문량", f"{current_quantity:,.0f}개", f"전월 대비 {_change_text(_change(current_quantity, previous_quantity))}"],
        ["주문건수", f"{current_orders:,}건", f"전월 대비 {_change_text(_change(current_orders, previous_orders))}"],
        ["고유 주문 접수", f"{unique_receipts:,}건", "동일 고객·동일 접수시각 중복 제거"],
        ["당월 주문 고객", f"{current_customers:,}명", f"전월 대비 {_change_text(_change(current_customers, previous_customers))}"],
        ["전체 회원", f"{total_members:,}명", f"당월 신규 {new_members:,}명"],
    ], columns=["지표", "당월 실적", "비교·산정 기준"])

    issue_table = issues.copy()
    issue_table = issue_table.fillna("")
    issue_table = issue_table[issue_table.astype(str).apply(lambda row: row.str.strip().ne("").any(), axis=1)]
    if issue_table.empty:
        issue_table = pd.DataFrame([["입력 내용 없음", "-", "-"]], columns=["당월 주요 이슈", "조치 내역", "결과"])

    top_product = product_table.iloc[0] if len(product_table) else None
    summary_lines = [
        f"당월 주문량은 {current_quantity:,.0f}개로 전월 대비 {_change_text(_change(current_quantity, previous_quantity))}입니다.",
        f"당월 주문건수는 {current_orders:,}건이며, 실제 주문 접수 단위로는 {unique_receipts:,}건입니다.",
        f"당월 주문 고객은 {current_customers:,}명이고 전체 회원은 {total_members:,}명입니다.",
        f"전월 대비 매출은 {_change_text(revenue_change)}입니다." if previous_revenue else "전월 매출을 입력하면 매출 증감률이 자동 계산됩니다.",
        f"배송 수량이 가장 많은 품목은 {top_product['품목명']}({top_product['배송_수량']:,.0f}개)입니다." if top_product is not None else "당월 품목 데이터가 없습니다.",
    ]

    return {
        "month_label": f"{month.year}년 {month.month}월",
        "period_label": f"{start:%Y-%m-%d} ~ {end:%Y-%m-%d}",
        "kpi_table": kpi_table,
        "issue_table": issue_table,
        "next_plan_table": _one_column_table("익월 계획", next_plan),
        "partner_request_table": _one_column_table("협력사 요청 사항", requests),
        "member_table": member_table,
        "product_table": product_table,
        "summary_lines": summary_lines,
        "current": current,
    }


def _monthly_styles():
    st.markdown("""
    <style>
      .monthly-hero { margin: 8px 0 38px; }
      .monthly-eyebrow {
        color: #8f7cf4 !important; font-size: 13px; font-weight: 600;
        letter-spacing: .08em; text-transform: uppercase; margin-bottom: 9px;
      }
      .monthly-title {
        color: var(--text-color) !important; font-size: clamp(34px, 4vw, 38px);
        font-weight: 550; line-height: 1.15; letter-spacing: -.035em; margin: 0 0 10px;
      }
      .monthly-description { color: var(--muted-color) !important; font-size: 15px; margin: 0; }
      .monthly-report-meta {
        display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        color: var(--muted-color); font-size: 13px; margin-top: 12px;
      }
      .monthly-status {
        display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px;
        border: 1px solid rgba(83, 194, 139, .28); border-radius: 999px;
        background: rgba(46, 160, 103, .10); color: #71d6a4 !important; font-weight: 500;
      }
      .monthly-kpi-grid {
        display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px; margin: 0 0 44px;
      }
      .monthly-kpi-card {
        min-height: 142px; padding: 24px; box-sizing: border-box;
        border: 1px solid #31374d; border-radius: 14px;
        background: linear-gradient(145deg, rgba(108, 92, 231, .08), rgba(24, 27, 36, 0)), #181b24;
        box-shadow: 0 12px 32px rgba(0, 0, 0, .14);
      }
      .monthly-kpi-head { display: flex; justify-content: space-between; align-items: center; }
      .monthly-kpi-label { color: #989fb3 !important; font-size: 13px; font-weight: 500; }
      .monthly-kpi-icon {
        width: 32px; height: 32px; display: grid; place-items: center;
        border-radius: 9px; color: #aa9df7; background: rgba(108, 92, 231, .13);
      }
      .monthly-kpi-value {
        color: #f5f7ff !important; font-size: 27px; font-weight: 600;
        letter-spacing: -.025em; margin: 20px 0 8px;
      }
      .monthly-kpi-change { color: #8f96aa !important; font-size: 12px; }
      .monthly-positive { color: #62d49c !important; }
      .monthly-negative { color: #ff858f !important; }
      .monthly-section-title {
        color: var(--text-color) !important; font-size: 24px; font-weight: 500;
        letter-spacing: -.02em; margin: 0 0 7px;
      }
      .monthly-section-caption { color: var(--muted-color) !important; font-size: 13px; margin: 0; }
      [class*="st-key-monthly_card"], [class*="st-key-monthly_form"] {
        background: #181b24 !important; border: 1px solid #31374d !important;
        border-radius: 16px !important; padding: 28px !important;
        box-shadow: 0 14px 36px rgba(0, 0, 0, .13); margin-bottom: 24px;
      }
      [class*="st-key-monthly_form"] [data-baseweb="input"],
      [class*="st-key-monthly_form"] [data-baseweb="base-input"],
      [class*="st-key-monthly_form"] [data-baseweb="textarea"],
      [class*="st-key-monthly_form"] input,
      [class*="st-key-monthly_form"] textarea {
        background: #222638 !important; color: #f2f4fb !important;
        -webkit-text-fill-color: #f2f4fb !important; border-color: #31374d !important;
      }
      [class*="st-key-monthly_form"] input:focus,
      [class*="st-key-monthly_form"] textarea:focus {
        border-color: #7c6ee6 !important; box-shadow: 0 0 0 3px rgba(108, 92, 231, .16) !important;
      }
      .monthly-ops-table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 20px; }
      .monthly-ops-table th {
        background: #222638; color: #aeb4c6; font-size: 13px; font-weight: 500;
        padding: 14px 16px; text-align: left; border-top: 1px solid #31374d;
        border-bottom: 1px solid #31374d;
      }
      .monthly-ops-table th:first-child { border-left: 1px solid #31374d; border-radius: 10px 0 0 0; }
      .monthly-ops-table th:last-child { border-right: 1px solid #31374d; border-radius: 0 10px 0 0; }
      .monthly-ops-table td {
        color: #e9ebf3; font-size: 14px; line-height: 1.55; padding: 16px;
        background: #1b1e28; border-bottom: 1px solid #2b3041;
      }
      .monthly-ops-table tr:hover td { background: #202431; }
      .monthly-plan {
        white-space: pre-wrap; color: #e9ebf3 !important; font-size: 15px; line-height: 1.75;
        margin-top: 18px; padding: 20px; border: 1px solid #31374d;
        border-radius: 12px; background: #1b1e28;
      }
      [class*="st-key-monthly_primary"] button {
        background: #6c5ce7 !important; border-color: #7668ea !important;
        color: white !important; font-weight: 500 !important;
      }
      [class*="st-key-monthly_secondary"] button {
        background: transparent !important; border-color: #3b4258 !important;
        color: var(--text-color) !important;
      }
      [class*="st-key-monthly_primary"] button:hover,
      [class*="st-key-monthly_secondary"] button:hover { transform: translateY(-1px); }
      @media (max-width: 900px) {
        .monthly-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
      @media (max-width: 560px) {
        .monthly-kpi-grid { grid-template-columns: 1fr; }
        [class*="st-key-monthly_card"], [class*="st-key-monthly_form"] { padding: 20px !important; }
      }
    </style>
    """, unsafe_allow_html=True)


def _issues_from_record(record):
    issues = record.get("issues", []) if record else []
    actions = record.get("actions", []) if record else []
    results = record.get("results", []) if record else []
    size = max(len(issues), len(actions), len(results), 1)
    return pd.DataFrame([
        [issues[index] if index < len(issues) else "", actions[index] if index < len(actions) else "", results[index] if index < len(results) else ""]
        for index in range(size)
    ], columns=["당월 주요 이슈", "조치 내역", "결과"])


def _editor_prefix(month_key):
    return f"monthly_editor_{month_key}"


def _clear_editor(month_key):
    prefix = _editor_prefix(month_key)
    for key in list(st.session_state):
        if key.startswith(prefix):
            del st.session_state[key]


def _initialize_editor(month_key, record):
    prefix = _editor_prefix(month_key)
    if f"{prefix}_initialized" in st.session_state:
        return
    rows = _issues_from_record(record)
    st.session_state[f"{prefix}_current_sales"] = int(record.get("current_sales", 0)) if record else 0
    st.session_state[f"{prefix}_previous_sales"] = int(record.get("previous_sales", 0)) if record else 0
    st.session_state[f"{prefix}_next_plan"] = record.get("next_month_plan", "") if record else ""
    st.session_state[f"{prefix}_partner_requests"] = record.get("partner_requests", "") if record else ""
    st.session_state[f"{prefix}_issue_count"] = max(len(rows), 3)
    for index, row in rows.iterrows():
        st.session_state[f"{prefix}_issue_{index}"] = row["당월 주요 이슈"]
        st.session_state[f"{prefix}_action_{index}"] = row["조치 내역"]
        st.session_state[f"{prefix}_result_{index}"] = row["결과"]
    st.session_state[f"{prefix}_initialized"] = True


def _render_section_heading(title, caption):
    st.markdown(
        f'<div><h2 class="monthly-section-title">{escape(title)}</h2>'
        f'<p class="monthly-section-caption">{escape(caption)}</p></div>',
        unsafe_allow_html=True,
    )


def _render_editor(month, record, store, merged, members):
    month_key = str(month)
    prefix = _editor_prefix(month_key)
    _initialize_editor(month_key, record)
    is_new = record is None
    st.markdown(
        f'<div class="monthly-hero"><div class="monthly-eyebrow">{("New report" if is_new else "Edit report")}</div>'
        f'<h1 class="monthly-title">{month.year}년 {month.month}월 운영보고서 {("작성" if is_new else "수정")}</h1>'
        '<p class="monthly-description">운영 내용을 작성하고 저장하면 완성된 보고서 화면으로 전환됩니다.</p></div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True, key="monthly_form_basic"):
        _render_section_heading("보고서 기본정보", "보고서는 선택한 월별로 독립 저장됩니다.")
        st.text_input("보고서 대상 월", value=f"{month.year}년 {month.month}월", disabled=True)

    with st.container(border=True, key="monthly_form_sales"):
        _render_section_heading("매출정보", "원본 데이터에 매출 정보가 없어 당월·전월 매출을 직접 입력합니다.")
        sales_columns = st.columns(2, gap="large")
        sales_columns[0].number_input("당월 매출(원)", min_value=0, step=100_000, key=f"{prefix}_current_sales")
        sales_columns[1].number_input("전월 매출(원)", min_value=0, step=100_000, key=f"{prefix}_previous_sales")

    with st.container(border=True, key="monthly_form_operations"):
        _render_section_heading("운영내용", "주요 이슈별 조치 내역과 처리 결과를 같은 행에 작성합니다.")
        headers = st.columns([1.1, 1.5, 1.1], gap="medium")
        for column, label in zip(headers, ["주요 이슈", "조치 내역", "결과"]):
            column.markdown(f"**{label}**")
        issue_count = st.session_state[f"{prefix}_issue_count"]
        for index in range(issue_count):
            columns = st.columns([1.1, 1.5, 1.1], gap="medium")
            columns[0].text_input("주요 이슈", placeholder="주요 이슈", label_visibility="collapsed", key=f"{prefix}_issue_{index}")
            columns[1].text_input("조치 내역", placeholder="조치 내역", label_visibility="collapsed", key=f"{prefix}_action_{index}")
            columns[2].text_input("결과", placeholder="처리 결과", label_visibility="collapsed", key=f"{prefix}_result_{index}")
        if st.button("＋ 이슈 행 추가", key=f"{prefix}_add"):
            st.session_state[f"{prefix}_issue_count"] = min(issue_count + 1, 10)
            st.rerun()

    with st.container(border=True, key="monthly_form_plan"):
        _render_section_heading("익월 계획", "다음 달에 추진할 계획과 우선순위를 작성합니다.")
        st.text_area("익월 계획", height=150, placeholder="익월 추진 계획을 입력해주세요.", key=f"{prefix}_next_plan")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        _render_section_heading("협력사 요청 사항", "협력사에서 전달받은 요청이나 협조 요청을 작성합니다.")
        st.text_area("협력사 요청 사항", height=120, placeholder="협력사에서 요청한 사항을 입력해주세요.", key=f"{prefix}_partner_requests")

    button_columns = st.columns([1, 1, 3])
    save_label = "보고서 저장 및 생성" if is_new else "변경사항 저장"
    with button_columns[0]:
        save_clicked = st.button(save_label, type="primary", width="stretch", key="monthly_primary_save")
    with button_columns[1]:
        cancel_clicked = st.button("취소", width="stretch", key="monthly_secondary_cancel", disabled=is_new)
    if cancel_clicked:
        _clear_editor(month_key)
        st.session_state[f"monthly_edit_mode_{month_key}"] = False
        st.rerun()
    if save_clicked:
        issue_rows = []
        for index in range(st.session_state[f"{prefix}_issue_count"]):
            row = [
                st.session_state.get(f"{prefix}_issue_{index}", "").strip(),
                st.session_state.get(f"{prefix}_action_{index}", "").strip(),
                st.session_state.get(f"{prefix}_result_{index}", "").strip(),
            ]
            if any(row):
                issue_rows.append(row)
        payload = {
            "report_month": month_key,
            "current_sales": int(st.session_state[f"{prefix}_current_sales"]),
            "previous_sales": int(st.session_state[f"{prefix}_previous_sales"]),
            "issues": [row[0] for row in issue_rows],
            "actions": [row[1] for row in issue_rows],
            "results": [row[2] for row in issue_rows],
            "next_month_plan": st.session_state[f"{prefix}_next_plan"].strip(),
            "partner_requests": st.session_state[f"{prefix}_partner_requests"].strip(),
        }
        try:
            store.save(payload)
            _clear_editor(month_key)
            st.session_state[f"monthly_edit_mode_{month_key}"] = False
            st.toast("월간 운영보고서를 저장했습니다.", icon="✅")
            st.rerun()
        except ReportStoreError as error:
            st.error(str(error))


def _render_kpi_cards(current_sales, previous_sales):
    difference = current_sales - previous_sales
    rate = _change(current_sales, previous_sales)
    rate_text = _change_text(rate)
    change_class = "monthly-positive" if difference >= 0 else "monthly-negative"
    cards = [
        ("당월 매출", f"{current_sales:,.0f}원", "이번 달 입력 매출", "₩", ""),
        ("전월 매출", f"{previous_sales:,.0f}원", "비교 기준 매출", "◷", ""),
        ("증감액", f"{difference:+,.0f}원", "당월 매출 - 전월 매출", "↕", change_class),
        ("증감률", rate_text, "(당월-전월) ÷ 전월 × 100", "%", change_class if rate is not None else ""),
    ]
    html = '<div class="monthly-kpi-grid">'
    for label, value, note, icon, css_class in cards:
        html += (
            f'<div class="monthly-kpi-card"><div class="monthly-kpi-head">'
            f'<span class="monthly-kpi-label">{label}</span><span class="monthly-kpi-icon">{icon}</span></div>'
            f'<div class="monthly-kpi-value {css_class}">{value}</div>'
            f'<div class="monthly-kpi-change">{note}</div></div>'
        )
    st.markdown(html + "</div>", unsafe_allow_html=True)


def _render_report_view(month, record, store, merged, members, theme):
    current_sales = int(record.get("current_sales", 0))
    previous_sales = int(record.get("previous_sales", 0))
    issues = _issues_from_record(record)
    report = build_report(
        month, merged, members, current_sales, previous_sales, issues,
        record.get("next_month_plan", ""), record.get("partner_requests", ""),
    )
    created_at = str(record.get("created_at", "-")).replace("T", " ")[:16]
    st.markdown(
        f'<div class="monthly-hero"><div class="monthly-eyebrow">Operations report</div>'
        f'<h1 class="monthly-title">월간 운영보고서</h1>'
        f'<p class="monthly-description">{month.year}년 {month.month}월 운영 현황과 주요 업무 결과입니다.</p>'
        f'<div class="monthly-report-meta"><span class="monthly-status">● 저장됨</span>'
        f'<span>보고서 대상 월&nbsp; {month.year}.{month.month:02d}</span><span>작성일&nbsp; {escape(created_at)}</span></div></div>',
        unsafe_allow_html=True,
    )
    _render_kpi_cards(current_sales, previous_sales)

    with st.container(border=True, key="monthly_card_operations"):
        _render_section_heading("운영 내용", "당월 주요 이슈별 조치 내역과 결과")
        rows = ""
        for _, row in issues.iterrows():
            rows += (
                f"<tr><td>{escape(str(row['당월 주요 이슈']) or '-')}</td>"
                f"<td>{escape(str(row['조치 내역']) or '-')}</td>"
                f"<td>{escape(str(row['결과']) or '-')}</td></tr>"
            )
        st.markdown(
            '<table class="monthly-ops-table"><thead><tr><th>주요 이슈</th><th>조치 내역</th><th>결과</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True,
        )

    with st.container(border=True, key="monthly_card_plan"):
        _render_section_heading("익월 계획", "다음 달 주요 추진 계획")
        st.markdown(f'<div class="monthly-plan">{escape(record.get("next_month_plan", "") or "등록된 계획이 없습니다.")}</div>', unsafe_allow_html=True)

    with st.container(border=True, key="monthly_card_partner"):
        _render_section_heading("협력사 요청 사항", "협력사에서 전달받은 요청 및 협조 사항")
        st.markdown(f'<div class="monthly-plan">{escape(record.get("partner_requests", "") or "등록된 요청 사항이 없습니다.")}</div>', unsafe_allow_html=True)

    with st.container(border=True, key="monthly_card_metrics"):
        _render_section_heading("월간 운영 지표", "실제 주문 데이터에서 자동 집계한 주문량·주문건수·회원 현황")
        st.dataframe(report["kpi_table"].iloc[3:], width="stretch", hide_index=True)

    with st.container(border=True, key="monthly_card_product"):
        _render_section_heading("품목 현황", "선택 월의 배송 수량 상위 품목")
        if len(report["product_table"]):
            figure = px.bar(report["product_table"].head(12), x="품목명", y="배송_수량")
            figure.update_xaxes(categoryorder="total descending")
            figure.update_layout(
                template=theme["plotly_template"], paper_bgcolor="#181b24", plot_bgcolor="#181b24",
                font_color="#e9ebf3", font_family="Pretendard, sans-serif",
                margin=dict(l=10, r=10, t=20, b=20), height=380,
            )
            st.plotly_chart(figure, width="stretch")
        else:
            st.info("선택 월의 품목 데이터가 없습니다.")

    filename = f"잇뉴_{month.year}-{month.month:02d}_월간보고서"
    action_columns = st.columns([1, 1, 1, 2])
    with action_columns[0]:
        if st.button("수정하기", width="stretch", key="monthly_primary_edit"):
            _clear_editor(str(month))
            st.session_state[f"monthly_edit_mode_{month}"] = True
            st.rerun()
    action_columns[1].download_button(
        "Excel 다운로드", create_excel_report(report), f"{filename}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch",
    )
    action_columns[2].download_button(
        "PDF 다운로드", create_pdf_report(report), f"{filename}.pdf", "application/pdf", width="stretch",
    )


def render(theme):
    _monthly_styles()
    merged, members = load_monthly_source()
    if merged.empty or "order_date_parsed" not in merged:
        st.warning("고객 분석 파이프라인을 먼저 실행해주세요: python3 dashboards/customer/analysis/run_pipeline.py")
        return
    try:
        store = get_report_store()
        stored_months = store.list_months()
    except ReportStoreError as error:
        st.error(str(error))
        return
    data_months = [str(value) for value in pd.period_range(merged["order_date_parsed"].min(), merged["order_date_parsed"].max(), freq="M")]
    current_month = str(pd.Timestamp.now().to_period("M"))
    month_options = sorted(set(data_months + stored_months + [current_month]), reverse=True)
    selected_month = st.selectbox(
        "보고서 대상 월", month_options, format_func=lambda value: f"{value[:4]}년 {int(value[5:])}월",
        key="monthly_selected_month",
    )
    month = pd.Period(selected_month, freq="M")
    try:
        record = store.get(selected_month)
    except ReportStoreError as error:
        st.error(str(error))
        return
    report_exists = record is not None
    st.session_state["monthly_report_exists"] = report_exists
    edit_key = f"monthly_edit_mode_{selected_month}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = not report_exists
    if not report_exists:
        st.session_state[edit_key] = True
    if st.session_state[edit_key]:
        _render_editor(month, record, store, merged, members)
    else:
        _render_report_view(month, record, store, merged, members, theme)
