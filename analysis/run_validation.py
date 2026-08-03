"""
validation-suite: 분석 결과의 정합성을 검증한다.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 기준일 및 조회 기간
TODAY = datetime(2026, 7, 31)
END_DATE = TODAY
START_DATE = TODAY - pd.Timedelta(days=6)


def run_validation():
    """최종 검증 실행"""
    workspace = Path.cwd()

    results = []

    # 데이터 로드
    try:
        metrics = pd.read_csv(workspace / "customer_metrics.csv", dtype=str)
        groups = pd.read_csv(workspace / "customer_groups.csv", dtype=str)
        merged = pd.read_csv(workspace / "merged_data.csv", dtype=str, parse_dates=["order_date_parsed"])
        members = pd.read_csv(workspace / "members.csv", dtype=str)
        region = pd.read_csv(workspace / "region_analysis.csv", dtype=str)
        industry = pd.read_csv(workspace / "industry_analysis.csv", dtype=str)
        product = pd.read_csv(workspace / "product_analysis.csv", dtype=str)
        orders = pd.read_csv(workspace / "orders.csv", dtype=str)
    except Exception as e:
        print(f"[ERROR] 데이터 로딩 실패: {e}")
        return

    analysis_customers = groups["customer_id"].tolist()
    analysis_customers_set = set(analysis_customers)
    analysis_orders = merged[merged["customer_id"].isin(analysis_customers)]

    # 1. 고객별 지표 누락
    total_in_merged = len(merged["customer_id"].unique())
    total_in_metrics = len(metrics)
    ok = total_in_merged == total_in_metrics
    results.append({
        "항목": "고객별 지표 누락 여부",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"merged:{total_in_merged} vs metrics:{total_in_metrics}"
    })

    # 2. 분류 충돌
    dup_class = groups.groupby("customer_id")["고객군"].nunique()
    conflict = dup_class[dup_class > 1]
    ok = len(conflict) == 0
    results.append({
        "항목": "신규·재이용 충돌 여부",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"충돌 고객: {list(conflict.index)}"
    })

    # 3. 이탈 위험 판단 근거
    churn_df = groups[groups["고객군"] == "이탈 위험 고객"]
    no_reason = churn_df[churn_df["판단 근거"].isna() | (churn_df["판단 근거"] == "")]
    ok = len(no_reason) == 0
    results.append({
        "항목": "이탈 위험 고객 판단 근거 포함",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"근거 누락: {list(no_reason['customer_id'])}"
    })

    # 4. 인원 합계 일치
    group_total = groups["고객군"].value_counts().sum()
    ok = group_total == len(analysis_customers)
    results.append({
        "항목": "고객군별 인원 합계 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"합계:{group_total} vs 분석대상:{len(analysis_customers)}"
    })

    # 5. 지역 수치 일치
    region_total = pd.to_numeric(region["고객 수"], errors="coerce").sum()
    ok = int(region_total) == len(analysis_customers)
    results.append({
        "항목": "지역 수치 합계 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"지역합계:{region_total} vs 분석대상:{len(analysis_customers)}"
    })

    # 6. 업종 수치 일치
    industry_total = pd.to_numeric(industry["고객 수"], errors="coerce").sum()
    ok = int(industry_total) == len(analysis_customers)
    results.append({
        "항목": "업종 수치 합계 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"업종합계:{industry_total} vs 분석대상:{len(analysis_customers)}"
    })

    # 7. 품목 수치 일치
    product_total = pd.to_numeric(product["주문_건수"], errors="coerce").sum()
    analysis_order_count = len(analysis_orders)
    ok = int(product_total) == analysis_order_count
    results.append({
        "항목": "품목 수치 합계 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"품목합계:{product_total} vs 주문건수:{analysis_order_count}"
    })

    # 8. 원본 데이터 금액 일치
    merged_amount = pd.to_numeric(merged["order_amount_num"], errors="coerce").sum()
    orders["order_amount_num"] = pd.to_numeric(orders["order_amount"], errors="coerce")
    valid_orders_amount = orders.dropna(subset=["order_amount_num"])["order_amount_num"].sum()
    ok = abs(merged_amount - valid_orders_amount) < 1
    results.append({
        "항목": "누적 이용 금액 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"merged:{merged_amount:,.0f} vs orders:{valid_orders_amount:,.0f}"
    })

    # 9. 중복 order_id 처리
    dup_oid = merged[merged.duplicated(subset="order_id", keep=False)]
    ok = len(dup_oid) == 0
    results.append({
        "항목": "중복 order_id 처리",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"중복 order_id: {list(dup_oid['order_id'].unique())}"
    })

    # 10. 비회원 고객 별도 표시
    non_member_in_merged = set(merged["customer_id"].unique()) - set(members["customer_id"].unique())
    non_member_in_metrics = metrics[metrics["customer_id"].isin(non_member_in_merged)]
    ok = len(non_member_in_metrics) == 0 or all(non_member_metrics["회원 여부"] == "비회원" for _, non_member_metrics in non_member_in_metrics.iterrows())
    results.append({
        "항목": "비회원 고객 별도 표시",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else "비회원 고객의 회원 여부 표시가 '비회원'이 아님"
    })

    # 저장
    result_df = pd.DataFrame(results)
    result_df.to_csv(workspace / "validation_final.csv", index=False, encoding="utf-8-sig")

    print("📊 최종 검증 완료")
    all_pass = all(r["상태"] == "통과" for _, r in result_df.iterrows())
    for _, r in result_df.iterrows():
        symbol = "✅" if r["상태"] == "통과" else "❌"
        print(f"  {symbol} {r['항목']}: {r['상태']}" + (f" ({r['원인']})" if r['원인'] != "-" else ""))
    print(f"\n  전체: {'모두 통과' if all_pass else '일부 실패'}")
    print(f"  저장: validation_final.csv")

    return result_df, all_pass


if __name__ == "__main__":
    run_validation()
