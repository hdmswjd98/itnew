"""실제 배송 데이터 분석 결과를 Markdown으로 요약한다."""

import pandas as pd
from .paths import OUTPUT_DIR, ensure_data_dirs


def build_report():
    ensure_data_dirs()
    merged = pd.read_csv(OUTPUT_DIR / "merged_data.csv")
    groups = pd.read_csv(OUTPUT_DIR / "customer_groups.csv")
    validation = pd.read_csv(OUTPUT_DIR / "validation_final.csv")
    start = pd.to_datetime(merged["order_date_parsed"], errors="coerce").min()
    end = pd.to_datetime(merged["order_date_parsed"], errors="coerce").max()
    quantity = pd.to_numeric(merged["order_quantity_num"], errors="coerce").sum()
    eligible = (groups["이탈 분석 대상 여부"] == "예").sum()
    danger = (groups["이탈 위험 등급"] == "위험").sum()
    risk_rate = danger / eligible * 100 if eligible else 0

    lines = [
        "# 잇뉴 실제 배송 데이터 고객 분석 결과", "",
        "## 분석 범위", "",
        f"- 주문 접수 기간: {start:%Y-%m-%d} ~ {end:%Y-%m-%d}",
        f"- 실제 배송 주문: {len(merged):,}건",
        f"- 배송 수량: {quantity:,.0f}개",
        f"- 주문 고객: {groups['customer_id'].nunique():,}명",
        "- 원본 데이터에 주문 금액이 없어 매출 지표는 계산하지 않음", "",
        "## 고객군", "",
    ]
    for group, count in groups["고객군"].value_counts().items():
        lines.append(f"- {group}: {count:,}명")
    lines += [
        "", "## 이탈 위험", "",
        "- 분석 대상: 전체 주문 3회 이상이며 평균 이용 주기 계산 가능 고객",
        f"- 분석 대상 고객: {eligible:,}명",
        f"- 위험 고객: {danger:,}명",
        f"- 위험률: {danger:,} ÷ {eligible:,} × 100 = {risk_rate:.1f}%", "",
        "## 최종 검증", "",
    ]
    for _, row in validation.iterrows():
        lines.append(f"- {row['상태']}: {row['항목']}")
    output = OUTPUT_DIR / "customer_analysis_result.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 실제 데이터 보고서 생성: {output.name}")
    return output


if __name__ == "__main__":
    build_report()
