"""실제 회원·배송 주문 CSV의 구조와 품질을 검증한다."""

import pandas as pd
from .paths import INPUT_DIR, OUTPUT_DIR, ensure_data_dirs


def run_validation():
    ensure_data_dirs()
    members = pd.read_csv(INPUT_DIR / "members.csv", dtype=str)
    orders = pd.read_csv(INPUT_DIR / "orders.csv", dtype=str)
    deliveries = pd.read_csv(INPUT_DIR / "deliveries.csv", dtype=str)
    results = []
    invalid = []

    def result(name, ok, detail="-"):
        results.append({"항목": name, "상태": "통과" if ok else "오류", "내용": detail})

    member_required = {"customer_id", "signup_date", "member_type"}
    order_required = {"order_id", "customer_id", "order_date", "item_name", "order_quantity", "order_channel"}
    delivery_required = {"order_id", "delivery_date", "origin_region", "destination_region"}
    result("members.csv 필수컬럼", member_required <= set(members), str(sorted(member_required - set(members))) or "모든 필수 컬럼 존재")
    result("orders.csv 필수컬럼", order_required <= set(orders), str(sorted(order_required - set(orders))) or "모든 필수 컬럼 존재")
    result("deliveries.csv 필수컬럼", delivery_required <= set(deliveries), str(sorted(delivery_required - set(deliveries))) or "모든 필수 컬럼 존재")

    duplicate_members = members["customer_id"].duplicated(keep=False)
    result("members.csv customer_id 중복", not duplicate_members.any(), f"중복 {int(duplicate_members.sum())}건")
    duplicate_orders = orders["order_id"].duplicated(keep=False)
    result("orders.csv order_id 중복", not duplicate_orders.any(), f"중복 {int(duplicate_orders.sum())}건")

    order_dates = pd.to_datetime(orders["order_date"], errors="coerce")
    quantities = pd.to_numeric(orders["order_quantity"], errors="coerce")
    bad_customer = orders["customer_id"].isna() | orders["customer_id"].str.strip().eq("")
    bad_date = order_dates.isna()
    bad_quantity = quantities.isna() | quantities.le(0)
    result("orders.csv customer_id 결측", not bad_customer.any(), f"오류 {int(bad_customer.sum())}건")
    result("orders.csv 날짜 형식", not bad_date.any(), f"오류 {int(bad_date.sum())}건")
    result("orders.csv 배송 수량", not bad_quantity.any(), f"오류 {int(bad_quantity.sum())}건")

    invalid_mask = bad_customer | bad_date | bad_quantity | duplicate_orders
    if invalid_mask.any():
        invalid = orders[invalid_mask].copy()
        invalid["오류 사유"] = "필수값·날짜·수량 또는 주문 ID 오류"

    member_ids = set(members["customer_id"].dropna())
    order_ids = set(orders["order_id"].dropna())
    orphan_customers = set(orders["customer_id"].dropna()) - member_ids
    orphan_deliveries = set(deliveries["order_id"].dropna()) - order_ids
    result("orders.csv 비회원 customer_id", not orphan_customers, f"연결 불가 {len(orphan_customers)}명")
    result("deliveries.csv 연결 오류", not orphan_deliveries, f"연결 불가 {len(orphan_deliveries)}건")

    result_df = pd.DataFrame(results)
    invalid_df = pd.DataFrame(invalid)
    result_df.to_csv(OUTPUT_DIR / "validation_results.csv", index=False, encoding="utf-8-sig")
    invalid_df.to_csv(OUTPUT_DIR / "invalid_records.csv", index=False, encoding="utf-8-sig")
    print(f"📊 실제 데이터 검증 완료: {len(result_df)}개 항목, 제외 {len(invalid_df)}건")
    for row in results:
        print(f"  {'✅' if row['상태'] == '통과' else '❌'} {row['항목']}: {row['상태']}")
    return result_df


if __name__ == "__main__":
    run_validation()
