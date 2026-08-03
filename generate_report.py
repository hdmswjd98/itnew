"""
월간 리포트 자동 생성기
분석 결과 CSV 를 읽어 Markdown 리포트를 자동 생성합니다.

사용법:
    python generate_report.py [--month YYYY-MM]

예시:
    python generate_report.py                          # 현재월
    python generate_report.py --month 2026-07          # 특정 월
"""

import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Template


def load_data(workspace):
    """분석 결과 데이터 로드"""
    data = {}

    files = {
        "validation_results": "validation_results.csv",
        "invalid_records": "invalid_records.csv",
        "group_counts": "group_counts.csv",
        "metrics": "customer_metrics.csv",
        "groups": "customer_groups.csv",
        "churn_risk": "churn_risk_customers.csv",
        "region_analysis": "region_analysis.csv",
        "industry_analysis": "industry_analysis.csv",
        "product_analysis": "product_analysis.csv",
        "validation_final": "validation_final.csv",
        "ai_summary": "ai_summary.txt",
    }

    for key, filename in files.items():
        filepath = workspace / filename
        if filepath.exists():
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    data[key] = f.read()
            else:
                data[key] = pd.read_csv(filepath, dtype=str)
        else:
            data[key] = None

    # 분석 조건
    data["conditions"] = {
        "분석 기준일": datetime.now().strftime("%Y-%m-%d"),
        "조회 기간": "N/A",
    }

    return data


def generate_report(data, output_path):
    """Markdown 리포트 생성"""
    lines = []

    # 헤더
    lines.append("# 📅 월간 고객 분석 리포트")
    lines.append(f"\n- **분석 기준일**: {data['conditions']['분석 기준일']}")
    lines.append(f"- **생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 섹션 1: 조회 기간
    lines.append("## 1. 조회 기간 및 분석 조건")
    lines.append(f"- 분석 기준일: {data['conditions']['분석 기준일']}")
    lines.append(f"- 조회 기간: {data['conditions'].get('조회 기간', 'N/A')}")
    lines.append("")

    # 섹션 2: 데이터 검증
    lines.append("## 2. 데이터 검증 결과")
    if data.get("validation_results") is not None and len(data["validation_results"]) > 0:
        for _, r in data["validation_results"].iterrows():
            symbol = "✅" if r["상태"] == "통과" else "❌"
            lines.append(f"- {symbol} {r['항목']}: {r['상태']} ({r['내용']})")
    else:
        lines.append("- 검증 결과 데이터가 없습니다.")
    lines.append("")

    # 섹션 3: 고객군 현황
    lines.append("## 3. 고객군별 현황")
    if data.get("group_counts") is not None and len(data["group_counts"]) > 0:
        lines.append("| 고객군 | 고객 수 | 비율 |")
        lines.append("| --- | ---: | -: |")
        for _, r in data["group_counts"].iterrows():
            lines.append(f"| {r['고객군']} | {r['고객 수']}명 | {r['비율']}% |")
    else:
        lines.append("- 고객군 데이터가 없습니다.")
    lines.append("")

    # 섹션 4: 고객별 이용 지표
    lines.append("## 4. 고객별 이용 지표")
    if data.get("metrics") is not None and len(data["metrics"]) > 0:
        lines.append("| customer_id | 최근 주문일 | 주문 횟수 | 평균 이용 주기 | 최종 주문 후 경과일 | 누적 이용 금액 |")
        lines.append("| ----------- | ------ | ----: | -------: | ----------: | -------: |")
        for _, r in data["metrics"].iterrows():
            lines.append(f"| {r['customer_id']} | {r['최근 주문일']} | {r['주문 횟수']} | {r['평균 이용 주기']} | {r['최종 주문 후 경과일']}일 | {r['누적 이용 금액']} |")
    else:
        lines.append("- 이용 지표 데이터가 없습니다.")
    lines.append("")

    # 섹션 5: 고객군 분류
    lines.append("## 5. 신규·재이용·이탈 위험 고객 분류 결과")
    if data.get("groups") is not None and len(data["groups"]) > 0:
        lines.append("| customer_id | 고객군 | 이탈 상태 | 판단 근거 |")
        lines.append("| ----------- | ----- | ----- | ----- |")
        for _, r in data["groups"].iterrows():
            lines.append(f"| {r['customer_id']} | {r['고객군']} | {r['이탈 상태']} | {r['판단 근거']} |")
    else:
        lines.append("- 고객군 분류 데이터가 없습니다.")
    lines.append("")

    # 섹션 6: 이탈 위험 고객
    lines.append("## 6. 이탈 위험 고객 목록")
    if data.get("churn_risk") is not None and len(data["churn_risk"]) > 0:
        lines.append("| customer_id | 위험 등급 | 평균 이용 주기 | 최종 주문 후 경과일 | 판단 근거 |")
        lines.append("| ----------- | ----- | -------: | ----------: | ----- |")
        for _, r in data["churn_risk"].iterrows():
            lines.append(f"| {r['customer_id']} | {r['이탈 등급']} | {r['평균 이용 주기']} | {r['최종 주문 후 경과일']}일 | {r['판단 근거']} |")
    else:
        lines.append("- 이탈 위험 고객이 없습니다.")
    lines.append("")

    # 섹션 7: 지역 특성
    lines.append("## 7. 고객군별 지역 특성")
    if data.get("region_analysis") is not None and len(data["region_analysis"]) > 0:
        for grp in data["region_analysis"]["고객군"].unique():
            grp_data = data["region_analysis"][data["region_analysis"]["고객군"] == grp]
            lines.append(f"### {grp}")
            lines.append("| 지역 | 고객 수 | 비율 |")
            lines.append("| --- | ---: | -: |")
            for _, r in grp_data.iterrows():
                lines.append(f"| {r['region']} | {r['고객 수']}명 | {r['비율']}% |")
    else:
        lines.append("- 지역 데이터가 없습니다.")
    lines.append("")

    # 섹션 8: 업종 특성
    lines.append("## 8. 고객군별 업종 특성")
    if data.get("industry_analysis") is not None and len(data["industry_analysis"]) > 0:
        for grp in data["industry_analysis"]["고객군"].unique():
            grp_data = data["industry_analysis"][data["industry_analysis"]["고객군"] == grp]
            lines.append(f"### {grp}")
            lines.append("| 업종 | 고객 수 | 비율 |")
            lines.append("| --- | ---: | -: |")
            for _, r in grp_data.iterrows():
                lines.append(f"| {r['industry']} | {r['고객 수']}명 | {r['비율']}% |")
    else:
        lines.append("- 업종 데이터가 없습니다.")
    lines.append("")

    # 섹션 9: 품목 분석
    lines.append("## 9. 고객군별 품목 분석")
    if data.get("product_analysis") is not None and len(data["product_analysis"]) > 0:
        for grp in data["product_analysis"]["고객군"].unique():
            grp_data = data["product_analysis"][data["product_analysis"]["고객군"] == grp]
            lines.append(f"### {grp}")
            lines.append("| 품목 | 주문 건수 | 주문 금액 | 비율 |")
            lines.append("| ---- | ----: | -------: | -: |")
            for _, r in grp_data.iterrows():
                amt_str = str(r['주문_금액'])
                try:
                    amt = float(amt_str.replace(',', '').replace('원', ''))
                    amt_formatted = f"{amt:,.0f}원"
                except:
                    amt_formatted = amt_str
                lines.append(f"| {r['item_name']} | {r['주문_건수']}건 | {amt_formatted} | {r['비율']}% |")
    else:
        lines.append("- 품목 분석 데이터가 없습니다.")
    lines.append("")

    # 섹션 10: AI 요약
    lines.append("## 10. AI 분석 요약")
    if data.get("ai_summary"):
        for line in data["ai_summary"].split("\n"):
            if line.strip():
                lines.append(f"- {line.strip()}")
    else:
        lines.append("- AI 분석 요약이 없습니다.")
    lines.append("")

    # 섹션 11: 검증 결과
    lines.append("## 11. 분석 결과 검증 결과")
    if data.get("validation_final") is not None and len(data["validation_final"]) > 0:
        lines.append("| 검증 항목 | 통과/실패 | 원인 |")
        lines.append("| ----- | ----- | -- |")
        for _, r in data["validation_final"].iterrows():
            cause = str(r.get('원인', '-'))
            if cause == 'nan' or cause.strip() == '':
                cause = '-'
            lines.append(f"| {r['항목']} | {r['상태']} | {cause} |")
    else:
        lines.append("- 검증 결과 데이터가 없습니다.")
    lines.append("")

    # 저장
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ 리포트 생성 완료: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="월간 리포트 자동 생성기")
    parser.add_argument("--month", type=str, default=datetime.now().strftime("%Y-%m"),
                        help="리포트 대상 월 (기본: 현재월)")
    parser.add_argument("--output-dir", type=str, default="output",
                        help="출력 디렉토리 (기본: output)")
    args = parser.parse_args()

    workspace = Path(__file__).parent
    output_dir = workspace / args.output_dir
    output_dir.mkdir(exist_ok=True)

    report_filename = f"{args.month}월간리포트.md"
    report_path = output_dir / report_filename

    print(f"📅 {args.month} 월간 리포트 생성 시작...")
    data = load_data(workspace)

    if data["metrics"] is None and data["groups"] is None:
        print("[ERROR] 분석 결과 데이터를 찾을 수 없습니다.")
        print("  customer_metrics.csv 와 customer_groups.csv 가 필요합니다.")
        return

    generate_report(data, report_path)
    print(f"📄 리포트: {report_path}")


if __name__ == "__main__":
    main()
