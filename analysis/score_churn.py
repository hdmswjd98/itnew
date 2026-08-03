"""
churn-risk-scorer: 이탈 위험 비율과 등급을 산정한다.
"""

import pandas as pd
from pathlib import Path


def score_churn():
    """이탈 위험 점수 산정"""
    workspace = Path.cwd()
    metrics = pd.read_csv(workspace / "customer_metrics.csv", dtype=str)

    scores = []
    for _, row in metrics.iterrows():
        avg_cycle_raw = row["_avg_cycle_raw"]
        days_since_raw = row["_days_since_raw"]

        if pd.isna(avg_cycle_raw) or avg_cycle_raw == "":
            churn_ratio = None
            grade = "적용 안 함"
            reason = "주문 이력이 1회이거나 평균 이용 주기를 계산할 수 없음"
        else:
            avg_cycle_val = float(avg_cycle_raw)
            days_val = float(days_since_raw)
            churn_ratio = round(days_val / avg_cycle_val, 2)

            if days_val <= avg_cycle_val:
                grade = "정상"
                reason = f"평균 이용 주기({int(avg_cycle_val)}일) 이내 재방문"
            elif days_val <= avg_cycle_val * 1.5:
                grade = "주의"
                reason = f"평균 이용 주기({int(avg_cycle_val)}일) 대비 경과일({int(days_val)}일)이 1~1.5배 초과"
            else:
                grade = "위험"
                reason = f"평균 이용 주기({int(avg_cycle_val)}일) 대비 경과일({int(days_val)}일)이 1.5배 초과"

        scores.append({
            "customer_id": row["customer_id"],
            "평균 이용 주기": row["평균 이용 주기"],
            "최종 주문 후 경과일": row["최종 주문 후 경과일"],
            "이탈 위험 비율": f"{churn_ratio:.2f}" if churn_ratio is not None else "N/A",
            "_churn_ratio_raw": churn_ratio,
            "등급": grade,
            "판정 근거": reason,
        })

    df = pd.DataFrame(scores)
    df.to_csv(workspace / "churn_scores.csv", index=False, encoding="utf-8-sig")

    print("📊 이탈 위험 점수 산정 완료")
    for _, r in df.iterrows():
        print(f"  {r['customer_id']}: 비율={r['이탈 위험 비율']}, 등급={r['등급']}, 근거={r['판정 근거']}")

    print(f"  저장: churn_scores.csv")
    return df


if __name__ == "__main__":
    score_churn()
