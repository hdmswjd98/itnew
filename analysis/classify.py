"""
customer-classifier: 고객군 분류와 이탈 위험 등급을 최종 결정한다.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 기준일 및 조회 기간 (실제 운영시 동적 설정 가능)
TODAY = datetime(2026, 7, 31)
END_DATE = TODAY
START_DATE = TODAY - pd.Timedelta(days=6)


def classify_groups():
    """고객군 분류 실행"""
    workspace = Path.cwd()

    metrics = pd.read_csv(workspace / "customer_metrics.csv", dtype=str)
    churn_scores = pd.read_csv(workspace / "churn_scores.csv", dtype=str)
    merged = pd.read_csv(workspace / "merged_data.csv", dtype=str, parse_dates=["order_date_parsed"])
    members = pd.read_csv(workspace / "members.csv", dtype=str)

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
        churn_grade = csrow["등급"]
        churn_reason = csrow["판정 근거"]
        avg_cycle_str = mrow["평균 이용 주기"]
        days_since = int(mrow["최종 주문 후 경과일"])

        # 1. 신규 고객 판정
        if first_order >= START_DATE:
            group = "신규 고객"
            churn_status = "적용 안 함"
            churn_grade_final = "—"
            reason = f"최초 주문일({first_order.strftime('%Y-%m-%d')})이 조회 기간({START_DATE.strftime('%Y-%m-%d')}~{END_DATE.strftime('%Y-%m-%d')}) 내에 발생"
        # 2. 이탈 위험 고객 판정
        elif churn_grade in ["주의", "위험"]:
            group = "이탈 위험 고객"
            churn_status = churn_grade
            churn_grade_final = churn_grade
            reason = churn_reason
        # 3. 재이용 고객 판정
        elif order_count >= 2 and first_order < START_DATE:
            group = "재이용 고객"
            churn_status = csrow["등급"]
            churn_grade_final = churn_grade
            reason = "조회 기간 이전 주문 이력 있고 조회 기간 재주문, 평균 이용 주기 내 재방문"
        else:
            group = "일반 고객"
            churn_status = csrow["등급"]
            churn_grade_final = churn_grade
            reason = "조회 기간 내 주문 이력 없음, 기존 고객"

        groups.append({
            "customer_id": cid,
            "고객군": group,
            "이탈 상태": churn_status,
            "이탈 등급": churn_grade_final,
            "판단 근거": reason,
            "평균 이용 주기": avg_cycle_str,
            "최종 주문 후 경과일": days_since,
        })

    df = pd.DataFrame(groups)
    df.to_csv(workspace / "customer_groups.csv", index=False, encoding="utf-8-sig")

    # 이탈 위험 고객 목록
    churn_df = df[df["고객군"] == "이탈 위험 고객"].copy()
    churn_df = churn_df.sort_values(["이탈 등급", "최종 주문 후 경과일"], ascending=[True, False])
    churn_df.to_csv(workspace / "churn_risk_customers.csv", index=False, encoding="utf-8-sig")

    print("📊 고객군 분류 완료")
    print(f"  총 분석 대상: {len(df)}명")
    for grp in ["신규 고객", "재이용 고객", "이탈 위험 고객", "일반 고객"]:
        cnt = (df["고객군"] == grp).sum()
        if cnt > 0:
            print(f"  {grp}: {cnt}명")
    for _, r in df.iterrows():
        print(f"  {r['customer_id']}: {r['고객군']} / 이탈={r['이탈 상태']} / 근거={r['판단 근거']}")

    print(f"  저장: customer_groups.csv, churn_risk_customers.csv")
    return df, churn_df


if __name__ == "__main__":
    classify_groups()
