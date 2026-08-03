"""
data-loader: 회원·주문·배송 CSV 파일을 로드하고 기본 구조를 확인한다.
"""

import pandas as pd
import sys
from pathlib import Path


def load_data():
    """데이터 로드 및 기본 구조 확인"""
    workspace = Path(__file__).parent.parent  # 프로젝트 루트 (analysis/ 의 상위 디렉토리)
    files = ["members.csv", "orders.csv", "deliveries.csv", "invalid_orders.csv"]
    loaded = {}

    for fname in files:
        fpath = workspace / fname
        if not fpath.exists():
            print(f"[ERROR] {fname} 파일을 찾을 수 없습니다: {fpath}")
            continue
        df = pd.read_csv(fpath, dtype=str)
        print(f"\n{'='*60}")
        print(f"📄 {fname}")
        print(f"{'='*60}")
        print(f"  행 수: {len(df)}")
        print(f"  컬럼: {list(df.columns)}")
        print(f"  결측값:")
        for col in df.columns:
            null_count = df[col].isna().sum()
            empty_count = (df[col].astype(str).str.strip() == "").sum()
            if null_count > 0 or empty_count > 0:
                print(f"    - {col}: 결측 {null_count}건, 공백 {empty_count}건")
        loaded[fname] = df

    missing = set(files) - set(loaded.keys())
    if missing:
        print(f"\n[ERROR] 누락된 파일: {missing}")
        sys.exit(1)

    # 유효 orders 필터링
    orders = loaded["orders.csv"].copy()
    orders["order_amount_num"] = pd.to_numeric(orders["order_amount"], errors="coerce")
    orders["order_date_parsed"] = pd.to_datetime(orders["order_date"], errors="coerce")
    valid_mask = (
        orders["customer_id"].notna() & (orders["customer_id"].str.strip() != "") &
        orders["order_id"].notna() & (orders["order_id"].str.strip() != "") &
        orders["order_date_parsed"].notna() &
        orders["order_amount_num"].notna()
    )
    valid_orders = orders[valid_mask].drop_duplicates(subset="order_id", keep="first").copy()
    print(f"\n📊 유효 주문 데이터: {len(valid_orders)}건 (전체 {len(orders)}건 중)")
    print(f"  제외된 행: {len(orders) - len(valid_orders)}건")

    # 저장
    valid_orders.to_csv(workspace / "valid_orders_raw.csv", index=False)
    print(f"  저장: valid_orders_raw.csv")

    return loaded, valid_orders


if __name__ == "__main__":
    load_data()
