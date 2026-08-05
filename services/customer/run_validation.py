"""
validation-suite: 분석 결과의 정합성을 검증한다.
"""

import pandas as pd
from .paths import INPUT_DIR, OUTPUT_DIR, ensure_data_dirs
from datetime import datetime

# 기준일 및 조회 기간
TODAY = datetime(2026, 7, 31)
END_DATE = TODAY
START_DATE = TODAY - pd.Timedelta(days=6)


def run_validation():
    """최종 검증 실행"""
    ensure_data_dirs()

    results = []

    # 데이터 로드
    try:
        metrics = pd.read_csv(OUTPUT_DIR / "customer_metrics.csv", dtype=str)
        groups = pd.read_csv(OUTPUT_DIR / "customer_groups.csv", dtype=str)
        merged = pd.read_csv(OUTPUT_DIR / "merged_data.csv", dtype=str, parse_dates=["order_date_parsed"])
        members = pd.read_csv(INPUT_DIR / "members.csv", dtype=str)
        region = pd.read_csv(OUTPUT_DIR / "region_analysis.csv", dtype=str)
        industry = pd.read_csv(OUTPUT_DIR / "industry_analysis.csv", dtype=str)
        product = pd.read_csv(OUTPUT_DIR / "product_analysis.csv", dtype=str)
        orders = pd.read_csv(INPUT_DIR / "orders.csv", dtype=str)
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

    # 3. 이탈 위험 판단 근거 및 필수 컬럼
    churn_columns = {
        "이탈 분석 대상 여부", "이탈 위험 등급", "판단 근거", "전체 주문 횟수",
        "최근 주문일", "평균 이용 주기", "최종 주문 후 경과일", "평균 주기 대비 경과 비율",
    }
    missing_columns = churn_columns - set(groups.columns)
    no_reason = groups[groups["판단 근거"].isna() | (groups["판단 근거"] == "")] if not missing_columns else groups
    ok = not missing_columns and len(no_reason) == 0
    reason = "-"
    if missing_columns:
        reason = f"필수 컬럼 누락: {sorted(missing_columns)}"
    elif len(no_reason):
        reason = f"근거 누락: {list(no_reason['customer_id'])}"
    results.append({
        "항목": "이탈 분석 결과 필수 항목 및 판단 근거",
        "상태": "통과" if ok else "실패",
        "원인": reason,
    })

    # 4. 주문 횟수별 이탈 분석 대상·등급 기준
    order_counts = pd.to_numeric(groups["전체 주문 횟수"], errors="coerce")
    invalid_one = groups[(order_counts == 1) & (
        (groups["이탈 분석 대상 여부"] != "아니오") | (groups["이탈 위험 등급"] != "판정 제외")
    )]
    invalid_two = groups[(order_counts == 2) & (
        (groups["이탈 분석 대상 여부"] != "아니오") | (groups["이탈 위험 등급"] != "판정 보류")
    )]
    cycle_days = pd.to_numeric(
        groups["평균 이용 주기"].astype(str).str.replace("일", "", regex=False),
        errors="coerce",
    )
    cycle_available = cycle_days.gt(0)
    invalid_three = groups[(order_counts >= 3) & cycle_available & (
        (groups["이탈 분석 대상 여부"] != "예") |
        (~groups["이탈 위험 등급"].isin(["정상", "주의", "위험"]))
    )]
    invalid_cycle = groups[(order_counts >= 3) & ~cycle_available & (
        (groups["이탈 분석 대상 여부"] != "아니오") | (groups["이탈 위험 등급"] != "판정 보류")
    )]
    invalid_rules = pd.concat([invalid_one, invalid_two, invalid_three, invalid_cycle]).drop_duplicates()
    ok = len(invalid_rules) == 0
    results.append({
        "항목": "주문 횟수별 이탈 분석 기준 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"기준 불일치 고객: {list(invalid_rules['customer_id'])}",
    })

    # 5. 분석 대상은 정상·주의·위험 등급 합계와 일치해야 한다.
    eligible = groups[groups["이탈 분석 대상 여부"] == "예"]
    graded = groups[groups["이탈 위험 등급"].isin(["정상", "주의", "위험"])]
    ok = set(eligible["customer_id"]) == set(graded["customer_id"])
    results.append({
        "항목": "이탈 분석 대상과 등급 합계 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"분석대상:{len(eligible)} vs 등급합계:{len(graded)}",
    })

    # 6. 인원 합계 일치
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

    # 10. 원본 배송 수량 일치
    merged_quantity = pd.to_numeric(merged["order_quantity_num"], errors="coerce").sum()
    orders["order_quantity_num"] = pd.to_numeric(orders["order_quantity"], errors="coerce")
    valid_orders_quantity = orders.dropna(subset=["order_quantity_num"])["order_quantity_num"].sum()
    ok = abs(merged_quantity - valid_orders_quantity) < 1
    results.append({
        "항목": "누적 배송 수량 일치",
        "상태": "통과" if ok else "실패",
        "원인": "-" if ok else f"merged:{merged_quantity:,.0f} vs orders:{valid_orders_quantity:,.0f}"
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
    result_df.to_csv(OUTPUT_DIR / "validation_final.csv", index=False, encoding="utf-8-sig")

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
