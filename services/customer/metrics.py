"""
metrics-calculator: 고객별 5대 이용 지표를 계산한다.
"""

import pandas as pd
from .paths import INPUT_DIR, OUTPUT_DIR, ensure_data_dirs


def calc_metrics():
    """고객별 이용 지표 계산"""
    ensure_data_dirs()

    merged = pd.read_csv(OUTPUT_DIR / "merged_data.csv", dtype=str)
    merged["order_date_parsed"] = pd.to_datetime(
        merged["order_date_parsed"], errors="coerce"
    )
    end_date = merged["order_date_parsed"].max().normalize()
    members = pd.read_csv(INPUT_DIR / "members.csv", dtype=str)

    metrics = []

    for cid in sorted(merged["customer_id"].unique()):
        cust_data = merged[merged["customer_id"] == cid].sort_values("order_date_parsed")

        if len(cust_data) == 0:
            continue

        order_events = pd.Series(cust_data["order_date_parsed"].dropna().unique()).sort_values()
        recent_order = order_events.max()
        order_count = len(order_events)
        total_quantity = pd.to_numeric(cust_data["order_quantity_num"], errors="coerce").sum()

        # 평균 이용 주기는 주문 간격이 2개 이상 확보되는 3회 주문부터 계산한다.
        if order_count >= 3:
            days_diff = order_events.diff().dropna().dt.total_seconds() / 86_400
            avg_cycle = round(days_diff.mean(), 1)
        else:
            avg_cycle = None

        # 최종 주문 후 경과일
        days_since = (end_date - recent_order).days
        if days_since < 0:
            days_since = 0

        # 회원 여부
        is_member = "회원" if cid in members["customer_id"].values else "비회원"

        metrics.append({
            "customer_id": cid,
            "최근 주문일": recent_order.strftime("%Y-%m-%d"),
            "주문 횟수": order_count,
            "평균 이용 주기": f"{avg_cycle:.1f}일" if avg_cycle is not None else "계산 불가",
            "_avg_cycle_raw": avg_cycle,
            "최종 주문 후 경과일": days_since,
            "_days_since_raw": days_since,
            "누적 배송 수량": int(total_quantity),
            "_total_quantity_raw": total_quantity,
            "회원 여부": is_member,
        })

    df = pd.DataFrame(metrics)

    # 분석 대상 고객: 조회 기간 내 주문 이력이 있는 고객
    period_start = end_date.replace(day=1)
    analysis_customers = merged[merged["order_date_parsed"] >= period_start]["customer_id"].unique()
    analysis_customers = [c for c in analysis_customers if c in members["customer_id"].values]
    analysis_order_count = len(merged[merged["customer_id"].isin(analysis_customers)])

    print(f"📊 고객별 이용 지표 계산 완료")
    print(f"  최신 월 활성 고객(MAU): {len(analysis_customers)}명")
    print(f"  최신 월 활성 고객의 누적 배송 행: {analysis_order_count}건")
    print(f"  전체 지표 산출 고객: {len(df):,}명")

    df.to_csv(OUTPUT_DIR / "customer_metrics.csv", index=False, encoding="utf-8-sig")
    print(f"  저장: customer_metrics.csv")

    return df, analysis_customers, analysis_order_count


if __name__ == "__main__":
    calc_metrics()
