"""
data-merger: 고객 ID 와 주문 ID 기준으로 회원·주문·배송 데이터를 연결한다.
"""

import pandas as pd
from pathlib import Path


def merge_data():
    """데이터 병합 실행"""
    workspace = Path.cwd()

    # 데이터 로드
    members = pd.read_csv(workspace / "members.csv", dtype=str)
    valid_orders_raw = pd.read_csv(workspace / "valid_orders_raw.csv", dtype=str)
    deliveries = pd.read_csv(workspace / "deliveries.csv", dtype=str)

    # 숫자 컬럼 변환
    valid_orders_raw["order_amount_num"] = pd.to_numeric(valid_orders_raw["order_amount_num"], errors="coerce")
    valid_orders_raw["order_date_parsed"] = pd.to_datetime(valid_orders_raw["order_date_parsed"], errors="coerce")

    # 1단계: 회원-주문 연결 (customer_id 기준)
    merged = valid_orders_raw.merge(
        members[["customer_id", "signup_date", "region", "industry", "customer_name"]],
        on="customer_id", how="left"
    )

    # 비회원 고객 표시
    merged["회원 여부"] = merged["region"].apply(lambda x: "회원" if pd.notna(x) and str(x).strip() != "" else "비회원")
    merged["region"] = merged["region"].fillna("미상")
    merged["industry"] = merged["industry"].fillna("미상")
    merged["customer_name"] = merged["customer_name"].fillna("미상")

    # 2단계: 주문-배송 연결 (order_id 기준)
    merged = merged.merge(deliveries[["order_id", "delivery_status", "delivery_date"]], on="order_id", how="left")

    # 정렬
    merged = merged.sort_values(["customer_id", "order_date_parsed"]).reset_index(drop=True)

    # 저장
    merged.to_csv(workspace / "merged_data.csv", index=False, encoding="utf-8-sig")
    print(f"✅ 데이터 연결 완료: merged_data.csv")
    print(f"  총 행 수: {len(merged)}")
    print(f"  고유 customer_id: {merged['customer_id'].nunique()}")
    print(f"  고유 order_id: {merged['order_id'].nunique()}")
    print(f"  비회원 고객: {(merged['회원 여부'] == '비회원').sum()}명")

    return merged


if __name__ == "__main__":
    merge_data()
