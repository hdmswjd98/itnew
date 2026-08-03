"""
dashboard-formatter: 검증된 결과를 spec.md 의 11개 섹션에 맞춰 Markdown 보고서로 조립한다.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(".")
TODAY = datetime(2026, 7, 31)
END_DATE = TODAY
START_DATE = TODAY - pd.Timedelta(days=6)

def fmt_money(v):
    try:
        return f"{float(v):,.0f}원"
    except:
        return str(v)

def build_report():
    # 데이터 로드
    members = pd.read_csv(WORKSPACE / "members.csv", dtype=str)
    orders = pd.read_csv(WORKSPACE / "orders.csv", dtype=str)
    deliveries = pd.read_csv(WORKSPACE / "deliveries.csv", dtype=str)
    invalid_orders = pd.read_csv(WORKSPACE / "invalid_orders.csv", dtype=str)

    try:
        validation_results = pd.read_csv(WORKSPACE / "validation_results.csv", dtype=str)
    except:
        validation_results = pd.DataFrame(columns=["항목", "상태", "내용"])

    group_counts = pd.read_csv(WORKSPACE / "group_counts.csv", dtype=str)
    metrics = pd.read_csv(WORKSPACE / "customer_metrics.csv", dtype=str)
    groups = pd.read_csv(WORKSPACE / "customer_groups.csv", dtype=str)
    churn_df = pd.read_csv(WORKSPACE / "churn_risk_customers.csv", dtype=str)
    region = pd.read_csv(WORKSPACE / "region_analysis.csv", dtype=str)
    industry = pd.read_csv(WORKSPACE / "industry_analysis.csv", dtype=str)
    product = pd.read_csv(WORKSPACE / "product_analysis.csv", dtype=str)
    validation_final = pd.read_csv(WORKSPACE / "validation_final.csv", dtype=str)

    with open(WORKSPACE / "ai_summary.txt", "r", encoding="utf-8") as f:
        ai_summary = f.read()

    analysis_customers = groups["customer_id"].tolist()
    analysis_order_count = len(groups)  # 실제는 merged 기준

    md = []

    # 1. 조회 기간 및 분석 조건
    md.append("# 고객 분석 결과\n")
    md.append("## 1. 조회 기간 및 분석 조건\n")
    md.append(f"- **분석 기준일**: {END_DATE.strftime('%Y-%m-%d')}")
    md.append(f"- **조회 시작일**: {START_DATE.strftime('%Y-%m-%d')}")
    md.append(f"- **조회 종료일**: {END_DATE.strftime('%Y-%m-%d')}")
    md.append("- **입력 파일**: members.csv, orders.csv, deliveries.csv, invalid_orders.csv")
    md.append(f"- **분석 대상 고객 수**: {len(analysis_customers)}명")
    # 실제 분석 대상 주문 수
    merged = pd.read_csv(WORKSPACE / "merged_data.csv", dtype=str)
    analysis_orders_count = len(merged[merged["customer_id"].isin(analysis_customers)])
    md.append(f"- **분석 대상 주문 수**: {analysis_orders_count}건")
    md.append("")

    # 2. 데이터 검증 결과
    md.append("## 2. 데이터 검증 결과\n")
    md.append("| 검증 항목 | 통과·실패 | 확인 결과 |")
    md.append("| ----- | ----- | ----- |")
    for _, r in validation_results.iterrows():
        md.append(f"| {r['항목']} | {r['상태']} | {r['내용']} |")
    md.append("")

    # invalid_orders 상세
    md.append("### 제외 데이터 상세 (invalid_orders.csv)\n")
    if len(invalid_orders) > 0:
        md.append("| order_id | customer_id | order_date | item_name | order_amount | 오류 사유 |")
        md.append("| -------- | ----------- | ---------- | --------- | ------------ | -------- |")
        for _, r in invalid_orders.iterrows():
            issues = []
            if pd.isna(r.get("customer_id")) or str(r.get("customer_id")).strip() == "":
                issues.append("customer_id 누락")
            if r["order_id"] in invalid_orders[invalid_orders.duplicated(subset="order_id", keep=False)]["order_id"].values:
                issues.append("중복 order_id")
            try:
                float(r["order_amount"])
            except:
                issues.append("주문 금액 비숫자")
            issue_str = ", ".join(issues) if issues else "검증 대상 데이터"
            cid = r["customer_id"] if pd.notna(r["customer_id"]) else "-"
            amt = r["order_amount"] if pd.notna(r["order_amount"]) else "-"
            md.append(f"| {r['order_id']} | {cid} | {r['order_date']} | {r['item_name']} | {amt} | {issue_str} |")
    else:
        md.append("*제외 데이터 없음*")
    md.append("")

    # 3. 고객군별 현황
    md.append("## 3. 고객군별 현황\n")
    md.append("| 고객군 | 고객 수 | 비율 |")
    md.append("| --- | ---: | -: |")
    for _, r in group_counts.iterrows():
        md.append(f"| {r['고객군']} | {r['고객 수']}명 | {r['비율']}% |")
    md.append("")

    # 4. 고객별 이용 지표
    md.append("## 4. 고객별 이용 지표\n")
    md.append("| customer_id | 최근 주문일 | 주문 횟수 | 평균 이용 주기 | 최종 주문 후 경과일 | 누적 이용 금액 |")
    md.append("| ----------- | ------ | ----: | -------: | ----------: | -------: |")
    for _, r in metrics.iterrows():
        md.append(f"| {r['customer_id']} | {r['최근 주문일']} | {r['주문 횟수']} | {r['평균 이용 주기']} | {r['최종 주문 후 경과일']}일 | {r['누적 이용 금액']} |")
    md.append("")

    # 5. 고객군 분류 결과
    md.append("## 5. 신규·재이용·이탈 위험 고객 분류 결과\n")
    md.append("| customer_id | 고객군 | 이탈 상태 | 판단 근거 |")
    md.append("| ----------- | ----- | ----- | ----- |")
    for _, r in groups.iterrows():
        md.append(f"| {r['customer_id']} | {r['고객군']} | {r['이탈 상태']} | {r['판단 근거']} |")
    md.append("")

    # 6. 이탈 위험 고객 목록
    md.append("## 6. 이탈 위험 고객 목록 및 분류 근거\n")
    if len(churn_df) > 0:
        md.append("| customer_id | 위험 등급 | 평균 이용 주기 | 최종 주문 후 경과일 | 판단 근거 |")
        md.append("| ----------- | ----- | -------: | ----------: | ----- |")
        for _, r in churn_df.iterrows():
            md.append(f"| {r['customer_id']} | {r['이탈 등급']} | {r['평균 이용 주기']} | {r['최종 주문 후 경과일']}일 | {r['판단 근거']} |")
    else:
        md.append("*이탈 위험 고객 없음*")
    md.append("")

    # 7. 지역 특성
    md.append("## 7. 고객군별 지역 특성\n")
    for grp in ["신규 고객", "재이용 고객", "이탈 위험 고객", "일반 고객"]:
        grp_data = region[region["고객군"] == grp]
        if len(grp_data) == 0:
            continue
        md.append(f"### {grp}\n")
        md.append("| 지역 | 고객 수 | 비율 |")
        md.append("| --- | ---: | -: |")
        for _, r in grp_data.iterrows():
            md.append(f"| {r['region']} | {r['고객 수']}명 | {r['비율']}% |")
        top_region = grp_data.loc[grp_data["고객 수"].idxmax(), "region"]
        md.append(f"**주요 지역**: {top_region}\n")
    md.append("")

    # 8. 업종 특성
    md.append("## 8. 고객군별 업종 특성\n")
    for grp in ["신규 고객", "재이용 고객", "이탈 위험 고객", "일반 고객"]:
        grp_data = industry[industry["고객군"] == grp]
        if len(grp_data) == 0:
            continue
        md.append(f"### {grp}\n")
        md.append("| 업종 | 고객 수 | 비율 |")
        md.append("| --- | ---: | -: |")
        for _, r in grp_data.iterrows():
            md.append(f"| {r['industry']} | {r['고객 수']}명 | {r['비율']}% |")
        top_industry = grp_data.loc[grp_data["고객 수"].idxmax(), "industry"]
        md.append(f"**주요 업종**: {top_industry}\n")
    md.append("")

    # 9. 품목 특성
    md.append("## 9. 고객군별 품목 주문 횟수·주문 금액·비율 및 상위 품목\n")
    for grp in ["신규 고객", "재이용 고객", "이탈 위험 고객", "일반 고객"]:
        grp_data = product[product["고객군"] == grp].sort_values("주문_건수", ascending=False)
        if len(grp_data) == 0:
            continue
        md.append(f"### {grp}\n")
        md.append("| 품목 | 주문 건수 | 주문 금액 | 비율 |")
        md.append("| ---- | ----: | -------: | -: |")
        for _, r in grp_data.iterrows():
            md.append(f"| {r['item_name']} | {r['주문_건수']}건 | {fmt_money(r['주문_금액'])} | {r['비율']}% |")
        top_item = grp_data.iloc[0]["item_name"]
        top_amount = grp_data.iloc[0]["주문_금액"]
        md.append(f"**상위 품목**: {top_item} ({fmt_money(top_amount)})\n")
    md.append("")

    # 10. AI 분석 요약
    md.append("## 10. AI 분석 요약\n")
    for line in ai_summary.split("\n"):
        if line.strip():
            md.append(f"- {line}")
    md.append("")

    # 11. 최종 검증 결과
    md.append("## 11. 분석 결과 검증 결과\n")
    md.append("| 검증 항목 | 통과·실패 | 원인 |")
    md.append("| ----- | ----- | -- |")
    for _, r in validation_final.iterrows():
        cause = str(r["원인"]) if pd.notna(r["원인"]) and str(r["원인"]).strip() != "" else "-"
        md.append(f"| {r['항목']} | {r['상태']} | {cause} |")
    md.append("")

    # 저장
    output_path = WORKSPACE / "customer_analysis_result.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print("✅ 보고서 생성 완료: customer_analysis_result.md")
    return output_path

if __name__ == "__main__":
    build_report()
