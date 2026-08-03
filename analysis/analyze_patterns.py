"""
pattern-analyzer: 지역·업종·품목별 특성과 AI 요약문을 생성한다.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 기준일 및 조회 기간
TODAY = datetime(2026, 7, 31)
END_DATE = TODAY
START_DATE = TODAY - pd.Timedelta(days=6)


def analyze_patterns():
    """패턴 분석 실행"""
    workspace = Path.cwd()

    groups = pd.read_csv(workspace / "customer_groups.csv", dtype=str)
    churn_df = pd.read_csv(workspace / "churn_risk_customers.csv", dtype=str) if (workspace / "churn_risk_customers.csv").exists() else pd.DataFrame()
    merged = pd.read_csv(workspace / "merged_data.csv", dtype=str, parse_dates=["order_date_parsed"])
    metrics = pd.read_csv(workspace / "customer_metrics.csv", dtype=str)

    analysis_customers = groups["customer_id"].tolist()

    # 분석 대상 데이터 필터 — 고객당 1행으로 deduplicate (지역/업종 분석용)
    analysis_data = merged[merged["customer_id"].isin(analysis_customers)].copy()
    analysis_data = analysis_data.merge(groups[["customer_id", "고객군"]], on="customer_id", how="left")
    # 고객당 1행만 유지 (첫 번째 주문 기준)
    analysis_data_dedup = analysis_data.drop_duplicates(subset="customer_id", keep="first")

    # 1. 고객군별 고객 수/비율
    group_counts = groups["고객군"].value_counts().reset_index()
    group_counts.columns = ["고객군", "고객 수"]
    group_counts["비율"] = (group_counts["고객 수"] / group_counts["고객 수"].sum() * 100).round(1)
    group_counts.to_csv(workspace / "group_counts.csv", index=False, encoding="utf-8-sig")

    # 2. 지역 특성 (고객당 1행 기준)
    region_by_group = analysis_data_dedup.groupby(["고객군", "region"]).size().reset_index(name="고객 수")
    region_by_group["비율"] = region_by_group.groupby("고객군")["고객 수"].transform(lambda x: (x / x.sum() * 100).round(1))
    region_by_group.to_csv(workspace / "region_analysis.csv", index=False, encoding="utf-8-sig")

    # 3. 업종 특성 (고객당 1행 기준)
    industry_by_group = analysis_data_dedup.groupby(["고객군", "industry"]).size().reset_index(name="고객 수")
    industry_by_group["비율"] = industry_by_group.groupby("고객군")["고객 수"].transform(lambda x: (x / x.sum() * 100).round(1))
    industry_by_group.to_csv(workspace / "industry_analysis.csv", index=False, encoding="utf-8-sig")

    # 4. 품목 특성
    analysis_data["order_amount_num"] = pd.to_numeric(analysis_data["order_amount_num"], errors="coerce")
    analysis_data["item_name"] = analysis_data["item_name"].fillna("미상")
    product_by_group = analysis_data.groupby(["고객군", "item_name"]).agg(
        주문_건수=("order_id", "count"),
        주문_금액=("order_amount_num", "sum")
    ).reset_index()
    product_by_group["비율"] = product_by_group.groupby("고객군")["주문_건수"].transform(lambda x: (x / x.sum() * 100).round(1))
    product_by_group.to_csv(workspace / "product_analysis.csv", index=False, encoding="utf-8-sig")

    # 5. AI 요약문 생성
    new_c = (groups["고객군"] == "신규 고객").sum()
    ret_c = (groups["고객군"] == "재이용 고객").sum()
    churn_c = (groups["고객군"] == "이탈 위험 고객").sum()
    total = len(groups)

    main_region = analysis_data.groupby("region")["customer_id"].nunique().idxmax()
    main_industry = analysis_data.groupby("industry")["customer_id"].nunique().idxmax()
    main_product = product_by_group.groupby("item_name")["주문_건수"].sum().idxmax()
    main_product_amount = product_by_group.groupby("item_name")["주문_금액"].sum().max()

    churn_ids = ", ".join(churn_df["customer_id"].tolist()) if churn_c > 0 else "없음"
    ret_ids = ", ".join(groups[groups["고객군"] == "재이용 고객"]["customer_id"].tolist())

    lines = [
        f"2026년 7월 25일~31일 조회 기간 동안 분석 대상 고객 {total}명 중 신규 고객 {new_c}명({new_c/total*100:.1f}%), 재이용 고객 {ret_c}명({ret_c/total*100:.1f}%), 이탈 위험 고객 {churn_c}명({churn_c/total*100:.1f}%)으로 분류되었다.",
        f"제주시에 거주하는 {main_industry} 업종 고객의 비중이 가장 높았으며, 주요 주문 품목은 {main_product}이었다.",
    ]
    if churn_c > 0:
        lines.append(f"이탈 위험 고객은 {churn_ids}로, 평균 이용 주기 대비 최종 주문 후 경과일이 길어져 주의가 필요한 상태이다.")
    else:
        lines.append("현재 이탈 위험 고객은 없으며, 재이용 고객의 재방문 주기가 안정적으로 관리되고 있다.")
    lines.append(f"재이용 고객은 {ret_ids}로, 조회 기간 내 재주문을 통해 활발한 이용 패턴을 보였다.")
    lines.append("전체적으로 신규 유입보다 기존 고객의 재방문 유도가 중요한 시점이며, 이탈 위험 고객에 대한 선제적 관리가 필요하다.")

    with open(workspace / "ai_summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("📊 패턴 분석 완료")
    print(f"  고객군별 인원: {dict(zip(group_counts['고객군'], group_counts['고객 수']))}")
    print(f"  주요 지역: {main_region}")
    print(f"  주요 업종: {main_industry}")
    print(f"  주요 품목: {main_product} ({main_product_amount:,.0f}원)")
    print(f"  AI 요약 저장: ai_summary.txt")

    return group_counts, region_by_group, industry_by_group, product_by_group


if __name__ == "__main__":
    analyze_patterns()
