"""
metrics-calculator: 고객별 5대 이용 지표를 계산한다.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(".")
TODAY = datetime(2026, 7, 31)
END_DATE = TODAY

def calc_metrics():
    merged = pd.read_csv(WORKSPACE / "merged_data.csv", dtype=str, parse_dates=["order_date_parsed"])
    members = pd.read_csv(WORKSPACE / "members.csv", dtype=str)

    metrics = []

    for cid in sorted(merged["customer_id"].unique()):
        cust_data = merged[merged["customer_id"] == cid].sort_values("order_date_parsed")

        if len(cust_data) == 0:
            continue

        recent_order = cust_data["order_date_parsed"].max()
        order_count = len(cust_data)
        total_amount = pd.to_numeric(cust_data["order_amount_num"], errors="coerce").sum()

        # 평균 이용 주기
        if order_count >= 2:
            days_diff = cust_data["order_date_parsed"].diff().dropna().dt.days
            avg_cycle = round(days_diff.mean())
        else:
            avg_cycle = None

        # 최종 주문 후 경과일
        days_since = (END_DATE - recent_order).days
        if days_since < 0:
            days_since = 0

        # 회원 여부
        is_member = "회원" if cid in members["customer_id"].values else "비회원"

        metrics.append({
            "customer_id": cid,
            "최근 주문일": recent_order.strftime("%Y-%m-%d"),
            "주문 횟수": order_count,
            "평균 이용 주기": f"{avg_cycle}일" if avg_cycle is not None else "계산 불가",
            "_avg_cycle_raw": avg_cycle,
            "최종 주문 후 경과일": days_since,
            "_days_since_raw": days_since,
            "누적 이용 금액": f"{total_amount:,.0f}원",
            "_total_amount_raw": total_amount,
            "회원 여부": is_member,
        })

    df = pd.DataFrame(metrics)

    # 분석 대상 고객: 조회 기간 내 주문 이력이 있는 고객
    # (merged_data 의 order_date_parsed 기준)
    period_start = END_DATE - pd.Timedelta(days=6)
    analysis_customers = merged[merged["order_date_parsed"] >= period_start]["customer_id"].unique()
    # 회원 데이터에 있는 고객만 분석 대상으로
    analysis_customers = [c for c in analysis_customers if c in members["customer_id"].values]
    analysis_order_count = len(merged[merged["customer_id"].isin(analysis_customers)])

    print(f"📊 고객별 이용 지표 계산 완료")
    print(f"  분석 대상 고객: {len(analysis_customers)}명")
    print(f"  분석 대상 주문: {analysis_order_count}건")
    for _, r in df.iterrows():
        print(f"  {r['customer_id']}: 최근주문={r['최근 주문일']}, 횟수={r['주문 횟수']}, "
              f"평균주기={r['평균 이용 주기']}, 경과일={r['최종 주문 후 경과일']}일, "
              f"누적금액={r['누적 이용 금액']}, 회원={r['회원 여부']}")

    df.to_csv(WORKSPACE / "customer_metrics.csv", index=False, encoding="utf-8-sig")
    print(f"  저장: customer_metrics.csv")

    return df, analysis_customers, analysis_order_count

if __name__ == "__main__":
    calc_metrics()
