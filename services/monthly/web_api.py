"""Next.js 월간리포트 화면용 JSON 표준출력 진입점."""

import json
from pathlib import Path

import pandas as pd

from .repository import get_report_store
from shared.paths import OUTPUT_DIR


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


def main():
    store = get_report_store()
    reports = [store.get(month) for month in store.list_months()]
    print(json.dumps({"reports": reports, "trends": _monthly_trends()}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
