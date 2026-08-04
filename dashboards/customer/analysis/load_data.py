"""검증된 실제 배송 주문을 로드한다."""

import pandas as pd
from paths import INPUT_DIR, OUTPUT_DIR, ensure_data_dirs


def load_data():
    ensure_data_dirs()
    loaded = {
        name: pd.read_csv(INPUT_DIR / name, dtype=str)
        for name in ["members.csv", "orders.csv", "deliveries.csv", "invalid_orders.csv"]
    }
    orders = loaded["orders.csv"].copy()
    orders["order_quantity_num"] = pd.to_numeric(orders["order_quantity"], errors="coerce")
    orders["order_date_parsed"] = pd.to_datetime(orders["order_date"], errors="coerce")
    valid_mask = (
        orders["customer_id"].notna() & orders["order_id"].notna()
        & orders["order_date_parsed"].notna() & orders["order_quantity_num"].gt(0)
    )
    valid_orders = orders[valid_mask].drop_duplicates("order_id", keep="first").copy()
    valid_orders.to_csv(OUTPUT_DIR / "valid_orders_raw.csv", index=False, encoding="utf-8-sig")
    print(f"📊 유효 배송 주문: {len(valid_orders):,}건 / 제외 {len(orders) - len(valid_orders):,}건")
    return loaded, valid_orders


if __name__ == "__main__":
    load_data()
