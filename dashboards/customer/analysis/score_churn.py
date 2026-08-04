"""
churn-risk-scorer: 이탈 위험 비율과 등급을 산정한다.
"""

import pandas as pd
from paths import OUTPUT_DIR, ensure_data_dirs


def classify_churn(order_count, avg_cycle, days_since):
    """주문 횟수와 재이용 주기를 기준으로 이탈 분석 여부·등급·근거를 반환한다."""
    cycle_text = f"{avg_cycle:.1f}일" if avg_cycle is not None else "계산 불가"
    ratio = round(days_since / avg_cycle, 2) if avg_cycle else None
    ratio_text = f"{ratio:.2f}배" if ratio is not None else "계산 불가"
    facts = (
        f"주문 {order_count}회, 평균 이용 주기 {cycle_text}, "
        f"최종 주문 후 {int(days_since)}일 경과, 평균 주기 대비 경과 비율 {ratio_text}"
    )

    if order_count == 1:
        return "아니오", "판정 제외", ratio, f"{facts}; 단발 이용으로 이탈 위험 분석에서 제외"
    if order_count == 2:
        return "아니오", "판정 보류", ratio, f"{facts}; 주문 간격이 1개뿐이므로 판정 보류"
    if avg_cycle is None or avg_cycle <= 0:
        return "아니오", "판정 보류", ratio, f"{facts}; 평균 이용 주기를 계산할 수 없어 판정 보류"
    if days_since <= avg_cycle:
        grade = "정상"
    elif days_since <= avg_cycle * 1.5:
        grade = "주의"
    else:
        grade = "위험"
    return "예", grade, ratio, facts


def score_churn():
    """이탈 위험 점수 산정"""
    ensure_data_dirs()
    metrics = pd.read_csv(OUTPUT_DIR / "customer_metrics.csv", dtype=str)

    scores = []
    for _, row in metrics.iterrows():
        order_count = int(row["주문 횟수"])
        avg_cycle_raw = row["_avg_cycle_raw"]
        days_since_raw = row["_days_since_raw"]
        avg_cycle_val = None if pd.isna(avg_cycle_raw) or avg_cycle_raw == "" else float(avg_cycle_raw)
        days_val = float(days_since_raw)
        eligible, grade, churn_ratio, reason = classify_churn(
            order_count, avg_cycle_val, days_val
        )

        scores.append({
            "customer_id": row["customer_id"],
            "전체 주문 횟수": order_count,
            "최근 주문일": row["최근 주문일"],
            "평균 이용 주기": row["평균 이용 주기"],
            "최종 주문 후 경과일": row["최종 주문 후 경과일"],
            "평균 주기 대비 경과 비율": f"{churn_ratio:.2f}" if churn_ratio is not None else "N/A",
            "_churn_ratio_raw": churn_ratio,
            "이탈 분석 대상 여부": eligible,
            "이탈 위험 등급": grade,
            "판단 근거": reason,
        })

    df = pd.DataFrame(scores)
    df.to_csv(OUTPUT_DIR / "churn_scores.csv", index=False, encoding="utf-8-sig")

    print("📊 이탈 위험 점수 산정 완료")
    print(f"  등급 분포: {df['이탈 위험 등급'].value_counts().to_dict()}")

    print(f"  저장: churn_scores.csv")
    return df


if __name__ == "__main__":
    score_churn()
