"""Next.js 월간리포트 화면용 JSON 표준출력 진입점."""

import json
import base64
import sys
from pathlib import Path

import pandas as pd

from .repository import get_report_store
from .export import create_excel_report, create_pdf_report
from shared.paths import INPUT_DIR, OUTPUT_DIR


def _total_members():
    members_path = INPUT_DIR / "members.csv"
    if not members_path.exists():
        return 0
    return int(pd.read_csv(members_path, dtype=str)["customer_id"].nunique())


def _monthly_trends():
    merged_path = OUTPUT_DIR / "merged_data.csv"
    if not merged_path.exists():
        return []
    data = pd.read_csv(merged_path, dtype=str)
    dates = pd.to_datetime(data.get("order_date_parsed", data.get("order_date")), errors="coerce")
    data = data.assign(month=dates.dt.to_period("M").astype(str))
    data = data[data["month"].ne("NaT")]
    data["quantity"] = pd.to_numeric(data.get("order_quantity_num", data.get("order_quantity")), errors="coerce").fillna(0)
    summary = data.groupby("month", as_index=False).agg(
        orders=("order_id", "count"),
        customers=("customer_id", "nunique"),
        quantity=("quantity", "sum"),
    )
    return summary.tail(12).to_dict("records")


def _export_payload(month, record):
    merged = pd.read_csv(OUTPUT_DIR / "merged_data.csv")
    classifications = pd.read_csv(OUTPUT_DIR / "product_classification.csv", dtype=str)
    classifications["자동분류_품목명"] = classifications["중분류"].where(
        classifications["중분류"].fillna("").str.strip().ne("기타"),
        classifications["대분류"].where(classifications["대분류"].fillna("").str.strip().ne("기타"), "미상"),
    )
    merged = merged.merge(classifications[["order_id", "자동분류_품목명"]], on="order_id", how="left")
    merged["자동분류_품목명"] = merged["자동분류_품목명"].fillna("미상")
    members = pd.read_csv(INPUT_DIR / "members.csv")
    dates = pd.to_datetime(merged.get("order_date_parsed", merged.get("order_date")), errors="coerce")
    current = merged[dates.dt.to_period("M").astype(str).eq(month)].copy()
    previous_month = str(pd.Period(month, freq="M") - 1)
    previous = merged[dates.dt.to_period("M").astype(str).eq(previous_month)].copy()
    quantity = pd.to_numeric(current.get("order_quantity_num", current.get("order_quantity")), errors="coerce").fillna(0)
    previous_quantity = pd.to_numeric(previous.get("order_quantity_num", previous.get("order_quantity")), errors="coerce").fillna(0)
    def change(value, prior): return f"{(value-prior)/prior*100:+.1f}%" if prior else "비교 불가"
    current_sales, previous_sales = int(record.get("current_sales", 0)), int(record.get("previous_sales", 0))
    kpis = pd.DataFrame([
        ["당월 매출", f"{current_sales:,}원" if current_sales else "금액 데이터 없음", "직접 입력"],
        ["전월 대비 매출", change(current_sales, previous_sales), "직접 입력 매출 기준"],
        ["주문량", f"{quantity.sum():,.0f}개", f"전월 대비 {change(quantity.sum(), previous_quantity.sum())}"],
        ["주문건수", f"{len(current):,}건", f"전월 대비 {change(len(current), len(previous))}"],
        ["주문 고객", f"{current['customer_id'].nunique():,}명", f"전월 대비 {change(current['customer_id'].nunique(), previous['customer_id'].nunique())}"],
        ["전체 회원", f"{members['customer_id'].nunique():,}명", "회원 전체 누적"],
    ], columns=["지표", "당월 실적", "비교·산정 기준"])
    issues, actions, results = record.get("issues", []), record.get("actions", []), record.get("results", [])
    size = max(len(issues), len(actions), len(results), 1)
    issue_table = pd.DataFrame([[issues[i] if i<len(issues) else "", actions[i] if i<len(actions) else "", results[i] if i<len(results) else ""] for i in range(size)], columns=["당월 주요 이슈","조치 내역","결과"])
    product_table = current.assign(배송_수량=quantity).groupby("자동분류_품목명",as_index=False).agg(배송_건수=("order_id","count"),배송_수량=("배송_수량","sum")).rename(columns={"자동분류_품목명":"품목명"}).sort_values("배송_건수",ascending=False)
    member_table = pd.DataFrame([["전체 회원",members['customer_id'].nunique()],["당월 주문 고객",current['customer_id'].nunique()]],columns=["회원 유형","회원 수"])
    return {"month_label":f"{month[:4]}년 {int(month[5:])}월","period_label":f"{month}-01 ~ {pd.Period(month).end_time:%Y-%m-%d}","kpi_table":kpis,"issue_table":issue_table,"next_plan_table":pd.DataFrame({"익월 계획":[record.get('next_month_plan') or '입력 내용 없음']}),"partner_request_table":pd.DataFrame({"협력사 요청 사항":[record.get('partner_requests') or '입력 내용 없음']}),"member_table":member_table,"product_table":product_table,"summary_lines":[f"당월 주문은 {len(current):,}건, 주문량은 {quantity.sum():,.0f}개입니다.",f"당월 주문 고객은 {current['customer_id'].nunique():,}명입니다.",f"전월 대비 주문건수는 {change(len(current),len(previous))}입니다."]}


def main():
    store = get_report_store()
    raw = sys.stdin.read().strip()
    if raw:
        request = json.loads(raw)
        if request.get("action") == "save":
            print(json.dumps({"ok": True, "data": store.save(request["report"])}, ensure_ascii=False, default=str)); return
        if request.get("action") == "export":
            record = store.get(request["month"]) or request.get("report") or {"report_month": request["month"]}
            report = _export_payload(request["month"], record)
            kind = request.get("format", "xlsx")
            content = create_pdf_report(report) if kind == "pdf" else create_excel_report(report)
            print(json.dumps({"ok":True,"data":{"content":base64.b64encode(content).decode(),"filename":f"itnew_{request['month']}_monthly_report.{kind}"}},ensure_ascii=False)); return
    reports = [store.get(month) for month in store.list_months()]
    print(json.dumps({"reports": reports, "trends": _monthly_trends(), "total_members": _total_members()}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
