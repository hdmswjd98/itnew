"""
customer-classifier: 고객군 분류와 이탈 위험 등급을 최종 결정한다.
"""

import pandas as pd
from paths import INPUT_DIR, OUTPUT_DIR, ensure_data_dirs


def classify_groups():
    """고객군 분류 실행"""
    ensure_data_dirs()

    metrics = pd.read_csv(OUTPUT_DIR / "customer_metrics.csv", dtype=str)
    churn_scores = pd.read_csv(OUTPUT_DIR / "churn_scores.csv", dtype=str)
    merged = pd.read_csv(OUTPUT_DIR / "merged_data.csv", dtype=str)
    merged["order_date_parsed"] = pd.to_datetime(
        merged["order_date_parsed"], errors="coerce"
    )
    members = pd.read_csv(INPUT_DIR / "members.csv", dtype=str)
    end_date = merged["order_date_parsed"].max().normalize()
    start_date = end_date.replace(day=1)

    groups = []

    for _, mrow in metrics.iterrows():
        cid = mrow["customer_id"]
        if cid not in members["customer_id"].values:
            continue

        cust_all = merged[merged["customer_id"] == cid].sort_values("order_date_parsed")
        first_order = cust_all["order_date_parsed"].min()
        order_count = int(mrow["주문 횟수"])

        # churn score lookup
        csrow = churn_scores[churn_scores["customer_id"] == cid].iloc[0]
        churn_grade = csrow["이탈 위험 등급"]
        churn_reason = csrow["판단 근거"]
        churn_eligible = csrow["이탈 분석 대상 여부"]
        churn_ratio = csrow["평균 주기 대비 경과 비율"]
        avg_cycle_str = mrow["평균 이용 주기"]
        days_since = int(mrow["최종 주문 후 경과일"])

        # 1. 신규 고객 판정
        if first_order >= start_date:
            group = "신규 고객"
            group_reason = f"최초 주문일({first_order.strftime('%Y-%m-%d')})이 최신 분석 월({start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}) 내에 발생"
        # 2. 이탈 위험 고객 판정
        elif churn_grade in ["주의", "위험"]:
            group = "이탈 위험 고객"
            group_reason = churn_reason
        # 3. 재이용 고객 판정
        elif order_count >= 2 and first_order < start_date:
            group = "재이용 고객"
            group_reason = "주문 이력이 2회 이상인 기존 재이용 고객"
        else:
            group = "일반 고객"
            group_reason = "주문 이력이 1회인 기존 단발 이용 고객"

        groups.append({
            "customer_id": cid,
            "고객군": group,
            "전체 주문 횟수": order_count,
            "최근 주문일": mrow["최근 주문일"],
            "평균 이용 주기": avg_cycle_str,
            "최종 주문 후 경과일": days_since,
            "평균 주기 대비 경과 비율": churn_ratio,
            "이탈 분석 대상 여부": churn_eligible,
            "이탈 위험 등급": churn_grade,
            "판단 근거": churn_reason,
            "고객군 판단 근거": group_reason,
        })

    df = pd.DataFrame(groups)
    df.to_csv(OUTPUT_DIR / "customer_groups.csv", index=False, encoding="utf-8-sig")

    # 이탈 위험 고객 목록
    churn_df = df[df["고객군"] == "이탈 위험 고객"].copy()
    grade_order = pd.Categorical(churn_df["이탈 위험 등급"], categories=["위험", "주의"], ordered=True)
    churn_df = churn_df.assign(_등급순서=grade_order).sort_values(
        ["_등급순서", "최종 주문 후 경과일"], ascending=[True, False]
    ).drop(columns="_등급순서")
    churn_df.to_csv(OUTPUT_DIR / "churn_risk_customers.csv", index=False, encoding="utf-8-sig")

    print("📊 고객군 분류 완료")
    print(f"  총 분석 대상: {len(df)}명")
    for grp in ["신규 고객", "재이용 고객", "이탈 위험 고객", "일반 고객"]:
        cnt = (df["고객군"] == grp).sum()
        if cnt > 0:
            print(f"  {grp}: {cnt}명")
    print(f"  저장: customer_groups.csv, churn_risk_customers.csv")
    return df, churn_df


if __name__ == "__main__":
    classify_groups()
