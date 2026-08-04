"""
pattern-analyzer: 지역·업종·품목별 특성과 AI 요약문을 생성한다.
"""

import pandas as pd
from paths import OUTPUT_DIR, ensure_data_dirs


def analyze_patterns():
    """패턴 분석 실행"""
    ensure_data_dirs()

    groups = pd.read_csv(OUTPUT_DIR / "customer_groups.csv", dtype=str)
    churn_df = pd.read_csv(OUTPUT_DIR / "churn_risk_customers.csv", dtype=str) if (OUTPUT_DIR / "churn_risk_customers.csv").exists() else pd.DataFrame()
    merged = pd.read_csv(OUTPUT_DIR / "merged_data.csv", dtype=str)
    merged["order_date_parsed"] = pd.to_datetime(
        merged["order_date_parsed"], errors="coerce", format="mixed"
    )
    metrics = pd.read_csv(OUTPUT_DIR / "customer_metrics.csv", dtype=str)

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
    group_counts.to_csv(OUTPUT_DIR / "group_counts.csv", index=False, encoding="utf-8-sig")

    # 2. 지역 특성 (고객당 1행 기준)
    region_by_group = analysis_data_dedup.groupby(["고객군", "destination_region"]).size().reset_index(name="고객 수")
    region_by_group = region_by_group.rename(columns={"destination_region": "region"})
    region_by_group["비율"] = region_by_group.groupby("고객군")["고객 수"].transform(lambda x: (x / x.sum() * 100).round(1))
    region_by_group = region_by_group.sort_values(["고객군", "고객 수"], ascending=[True, False])
    region_by_group.to_csv(OUTPUT_DIR / "region_analysis.csv", index=False, encoding="utf-8-sig")

    analysis_data["order_quantity_num"] = pd.to_numeric(analysis_data["order_quantity_num"], errors="coerce")

    # 3. 업종 특성 (고객 수 + 주문량 기준)
    industry_by_group = analysis_data.groupby(["고객군", "member_type"]).agg(
        고객_수=("customer_id", "nunique"),
        주문_건수=("order_id", "count"),
        배송_수량=("order_quantity_num", "sum"),
    ).reset_index().rename(columns={"고객_수": "고객 수", "member_type": "industry"})
    industry_by_group["비율"] = industry_by_group.groupby("고객군")["고객 수"].transform(lambda x: (x / x.sum() * 100).round(1))
    industry_by_group = industry_by_group.sort_values(["고객군", "주문_건수"], ascending=[True, False])
    industry_by_group.to_csv(OUTPUT_DIR / "industry_analysis.csv", index=False, encoding="utf-8-sig")

    # 4. 품목 특성
    analysis_data["item_name"] = analysis_data["item_name"].fillna("미상")
    product_by_group = analysis_data.groupby(["고객군", "item_name"]).agg(
        주문_건수=("order_id", "count"),
        배송_수량=("order_quantity_num", "sum")
    ).reset_index()
    product_by_group["비율"] = product_by_group.groupby("고객군")["주문_건수"].transform(lambda x: (x / x.sum() * 100).round(1))
    product_by_group = product_by_group.sort_values(["고객군", "주문_건수"], ascending=[True, False])
    product_by_group.to_csv(OUTPUT_DIR / "product_analysis.csv", index=False, encoding="utf-8-sig")

    # 5. AI 요약문 생성
    new_c = (groups["고객군"] == "신규 고객").sum()
    ret_c = (groups["고객군"] == "재이용 고객").sum()
    churn_c = (groups["고객군"] == "이탈 위험 고객").sum()
    eligible_c = (groups["이탈 분석 대상 여부"] == "예").sum()
    danger_c = (groups["이탈 위험 등급"] == "위험").sum()
    churn_rate = danger_c / eligible_c * 100 if eligible_c else 0
    total = len(groups)

    known_regions = analysis_data[analysis_data["destination_region"] != "미상"]
    main_region = known_regions.groupby("destination_region")["customer_id"].nunique().idxmax() if len(known_regions) else "확인 불가"
    main_industry = analysis_data.groupby("member_type")["customer_id"].nunique().idxmax()
    known_products = product_by_group[product_by_group["item_name"] != "미상"]
    main_product = known_products.groupby("item_name")["주문_건수"].sum().idxmax() if len(known_products) else "확인 불가"
    main_product_quantity = known_products.groupby("item_name")["배송_수량"].sum().max() if len(known_products) else 0
    order_dates = pd.to_datetime(analysis_data["order_date_parsed"], errors="coerce", format="mixed")
    end_date = order_dates.max()
    start_date = order_dates.min()

    churn_ids = ", ".join(churn_df["customer_id"].tolist()) if churn_c > 0 else "없음"
    ret_ids = ", ".join(groups[groups["고객군"] == "재이용 고객"]["customer_id"].tolist())

    lines = [
        f"{start_date:%Y년 %m월 %d일}~{end_date:%Y년 %m월 %d일} 실제 배송 주문 기준 고객 {total}명 중 신규 고객 {new_c}명({new_c/total*100:.1f}%), 재이용 고객 {ret_c}명({ret_c/total*100:.1f}%), 이탈 위험 고객 {churn_c}명({churn_c/total*100:.1f}%)으로 분류되었다.",
        f"전체 주문 3회 이상인 이탈 분석 대상은 {eligible_c}명이며, 위험 등급은 {danger_c}명으로 분석 대상 기준 위험률은 {churn_rate:.1f}%이다.",
        f"목적지는 {main_region}, 회원유형은 {main_industry}의 비중이 높았으며 주요 배송 품목은 {main_product}이었다.",
    ]
    if churn_c > 0:
        lines.append(f"이탈 위험 고객은 {churn_ids}로, 평균 이용 주기 대비 최종 주문 후 경과일이 길어져 주의가 필요한 상태이다.")
    else:
        lines.append("현재 이탈 위험 고객은 없으며, 재이용 고객의 재방문 주기가 안정적으로 관리되고 있다.")
    lines.append(f"재이용 고객은 {ret_ids}로, 조회 기간 내 재주문을 통해 활발한 이용 패턴을 보였다.")

    with open(OUTPUT_DIR / "ai_summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("📊 패턴 분석 완료")
    print(f"  고객군별 인원: {dict(zip(group_counts['고객군'], group_counts['고객 수']))}")
    print(f"  주요 지역: {main_region}")
    print(f"  주요 업종: {main_industry}")
    print(f"  주요 품목: {main_product} ({main_product_quantity:,.0f}개)")
    print(f"  AI 요약 저장: ai_summary.txt")

    return group_counts, region_by_group, industry_by_group, product_by_group


if __name__ == "__main__":
    analyze_patterns()
