"""실제 회원·배송 주문·배송 지역 데이터를 연결한다."""

import pandas as pd
from .paths import INPUT_DIR, OUTPUT_DIR, ensure_data_dirs


def merge_data():
    ensure_data_dirs()
    members = pd.read_csv(INPUT_DIR / "members.csv", dtype=str)
    orders = pd.read_csv(OUTPUT_DIR / "valid_orders_raw.csv")
    deliveries = pd.read_csv(INPUT_DIR / "deliveries.csv", dtype=str)
    merged = orders.merge(members, on="customer_id", how="left").merge(deliveries, on="order_id", how="left")
    merged["order_date_parsed"] = pd.to_datetime(merged["order_date_parsed"], errors="coerce")
    merged["delivery_date_parsed"] = pd.to_datetime(merged["delivery_date"], errors="coerce")
    merged["member_type"] = merged["member_type"].fillna("미상")
    merged["destination_region"] = merged["destination_region"].fillna("미상")
    merged["origin_region"] = merged["origin_region"].fillna("미상")
    merged["회원 여부"] = merged["signup_date"].notna().map({True: "회원", False: "비회원"})
    merged = merged.sort_values(["customer_id", "order_date_parsed"]).reset_index(drop=True)
    merged.to_csv(OUTPUT_DIR / "merged_data.csv", index=False, encoding="utf-8-sig")
    print(f"✅ 실제 데이터 연결: {len(merged):,}건 / 주문 고객 {merged['customer_id'].nunique():,}명")
    return merged


if __name__ == "__main__":
    merge_data()
