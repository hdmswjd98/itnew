"""
data-validator: 회원·주문·배송 CSV 의 필수 컬럼, 결측값, 중복, 타입 오류를 검증하고 결과를 저장한다.
"""

import pandas as pd
from pathlib import Path


def run_validation():
    """데이터 검증 실행. WORKSPACE 는 호출 측에서 설정됨."""
    workspace = Path.cwd()

    validation_results = []
    invalid_records = []

    # ── members.csv 검증 ──────────────────────────────
    members_path = workspace / "members.csv"
    if not members_path.exists():
        print(f"[ERROR] {members_path} 파일을 찾을 수 없습니다.")
        return

    members = pd.read_csv(members_path, dtype=str)
    required_members = ["customer_id", "signup_date", "region", "industry"]
    missing_cols = [c for c in required_members if c not in members.columns]
    if missing_cols:
        validation_results.append({"항목": "members.csv 필수컬럼", "상태": "오류", "내용": f"누락된 컬럼: {missing_cols}"})
    else:
        validation_results.append({"항목": "members.csv 필수컬럼", "상태": "통과", "내용": "모든 필수 컬럼 존재"})

    dup_cid = members[members.duplicated(subset="customer_id", keep=False)]
    if len(dup_cid) > 0:
        validation_results.append({"항목": "members.csv customer_id 중복", "상태": "오류", "내용": f"{len(dup_cid)}건 중복"})
    else:
        validation_results.append({"항목": "members.csv customer_id 중복", "상태": "통과", "내용": "중복 없음"})

    # ── orders.csv 검증 ──────────────────────────────
    orders_path = workspace / "orders.csv"
    if not orders_path.exists():
        print(f"[ERROR] {orders_path} 파일을 찾을 수 없습니다.")
        return

    orders = pd.read_csv(orders_path, dtype=str)
    required_orders = ["order_id", "customer_id", "order_date", "order_amount"]
    missing_colso = [c for c in required_orders if c not in orders.columns]
    if missing_colso:
        validation_results.append({"항목": "orders.csv 필수컬럼", "상태": "오류", "내용": f"누락된 컬럼: {missing_colso}"})
    else:
        validation_results.append({"항목": "orders.csv 필수컬럼", "상태": "통과", "내용": "모든 필수 컬럼 존재"})

    # customer_id 결측
    null_cid = orders[orders["customer_id"].isna() | (orders["customer_id"].str.strip() == "")]
    if len(null_cid) > 0:
        validation_results.append({"항목": "orders.csv customer_id 결측", "상태": "오류", "내용": f"{len(null_cid)}건 누락"})
        for _, r in null_cid.iterrows():
            invalid_records.append({"order_id": r.get("order_id", ""), "customer_id": r.get("customer_id", ""), "order_date": r.get("order_date", ""), "item_name": r.get("item_name", ""), "order_amount": r.get("order_amount", ""), "오류 사유": "customer_id 누락"})
    else:
        validation_results.append({"항목": "orders.csv customer_id 결측", "상태": "통과", "내용": "결측 없음"})

    # order_id 결측
    null_oid = orders[orders["order_id"].isna() | (orders["order_id"].str.strip() == "")]
    if len(null_oid) > 0:
        validation_results.append({"항목": "orders.csv order_id 결측", "상태": "오류", "내용": f"{len(null_oid)}건 누락"})
    else:
        validation_results.append({"항목": "orders.csv order_id 결측", "상태": "통과", "내용": "결측 없음"})

    # 중복 order_id
    dup_oid = orders[orders.duplicated(subset="order_id", keep=False)]
    if len(dup_oid) > 0:
        dup_list = dup_oid["order_id"].unique().tolist()
        validation_results.append({"항목": "orders.csv 중복 order_id", "상태": "오류", "내용": f"{dup_list} 중복"})
        for _, r in dup_oid.iterrows():
            invalid_records.append({"order_id": r["order_id"], "customer_id": r["customer_id"], "order_date": r["order_date"], "item_name": r["item_name"], "order_amount": r["order_amount"], "오류 사유": "중복 order_id"})
    else:
        validation_results.append({"항목": "orders.csv 중복 order_id", "상태": "통과", "내용": "중복 없음"})

    # 날짜 형식
    orders["_order_date_parsed"] = pd.to_datetime(orders["order_date"], errors="coerce")
    bad_date = orders[orders["_order_date_parsed"].isna()]
    if len(bad_date) > 0:
        validation_results.append({"항목": "orders.csv 날짜 형식 오류", "상태": "오류", "내용": f"{len(bad_date)}건 변환 불가"})
        for _, r in bad_date.iterrows():
            invalid_records.append({"order_id": r["order_id"], "customer_id": r["customer_id"], "order_date": r["order_date"], "item_name": r["item_name"], "order_amount": r["order_amount"], "오류 사유": "order_date 날짜 형식 변환 불가"})
    else:
        validation_results.append({"항목": "orders.csv 날짜 형식 오류", "상태": "통과", "내용": "모든 주문일 정상"})

    # 주문 금액
    orders["_order_amount_num"] = pd.to_numeric(orders["order_amount"], errors="coerce")
    bad_amount = orders[orders["_order_amount_num"].isna()]
    if len(bad_amount) > 0:
        validation_results.append({"항목": "orders.csv 주문 금액 오류", "상태": "오류", "내용": f"{len(bad_amount)}건 변환 불가"})
        for _, r in bad_amount.iterrows():
            invalid_records.append({"order_id": r["order_id"], "customer_id": r["customer_id"], "order_date": r["order_date"], "item_name": r["item_name"], "order_amount": r["order_amount"], "오류 사유": "order_amount 숫자 변환 불가"})
    else:
        validation_results.append({"항목": "orders.csv 주문 금액 오류", "상태": "통과", "내용": "모든 금액 정상"})

    # ── deliveries.csv 검증 ──────────────────────────
    deliveries_path = workspace / "deliveries.csv"
    if not deliveries_path.exists():
        print(f"[ERROR] {deliveries_path} 파일을 찾을 수 없습니다.")
        return

    deliveries = pd.read_csv(deliveries_path, dtype=str)
    required_del = ["order_id", "delivery_status", "delivery_date"]
    missing_cold = [c for c in required_del if c not in deliveries.columns]
    if missing_cold:
        validation_results.append({"항목": "deliveries.csv 필수컬럼", "상태": "오류", "내용": f"누락된 컬럼: {missing_cold}"})
    else:
        validation_results.append({"항목": "deliveries.csv 필수컬럼", "상태": "통과", "내용": "모든 필수 컬럼 존재"})

    # 주문 데이터에 없는 배송 order_id
    valid_order_ids = set(orders["order_id"].dropna().unique())
    delivery_order_ids = set(deliveries["order_id"].dropna().unique())
    orphan_delivery = delivery_order_ids - valid_order_ids
    if orphan_delivery:
        validation_results.append({"항목": "deliveries.csv 연결 오류", "상태": "오류", "내용": f"주문 데이터에 없는 배송 order_id: {list(orphan_delivery)}"})
    else:
        validation_results.append({"항목": "deliveries.csv 연결 오류", "상태": "통과", "내용": "모든 배송 데이터 연결 가능"})

    # ── invalid_orders.csv 검증 ──────────────────────
    invalid_orders_path = workspace / "invalid_orders.csv"
    if invalid_orders_path.exists():
        invalid_orders = pd.read_csv(invalid_orders_path, dtype=str)
        for _, r in invalid_orders.iterrows():
            issues = []
            if pd.isna(r.get("customer_id")) or str(r.get("customer_id")).strip() == "":
                issues.append("customer_id 누락")
            if r["order_id"] in orders[orders.duplicated(subset="order_id", keep=False)]["order_id"].values:
                issues.append("중복 order_id")
            try:
                float(r["order_amount"])
            except:
                issues.append("주문 금액 비숫자")
            invalid_records.append({"order_id": r["order_id"], "customer_id": r["customer_id"], "order_date": r["order_date"], "item_name": r["item_name"], "order_amount": r["order_amount"], "오류 사유": ", ".join(issues) if issues else "검증 대상 데이터"})

    # ── 통합 검증 ───────────────────────────────────
    # 회원 데이터에 없는 customer_id
    valid_orders_filtered = orders[
        orders["customer_id"].notna() & (orders["customer_id"].str.strip() != "") &
        orders["order_id"].notna() & (orders["order_id"].str.strip() != "") &
        orders["_order_date_parsed"].notna() &
        orders["_order_amount_num"].notna()
    ].drop_duplicates(subset="order_id", keep="first")
    orphan_cid = set(valid_orders_filtered["customer_id"].unique()) - set(members["customer_id"].unique())
    if orphan_cid:
        validation_results.append({"항목": "orders.csv 비회원 customer_id", "상태": "오류", "내용": f"회원 데이터에 없는 customer_id: {list(orphan_cid)}"})
    else:
        validation_results.append({"항목": "orders.csv 비회원 customer_id", "상태": "통과", "내용": "모든 customer_id 가 회원 데이터에 존재"})

    # 저장
    val_df = pd.DataFrame(validation_results)
    val_df.to_csv(workspace / "validation_results.csv", index=False, encoding="utf-8-sig")

    inv_df = pd.DataFrame(invalid_records)
    inv_df.to_csv(workspace / "invalid_records.csv", index=False, encoding="utf-8-sig")

    print("📊 데이터 검증 완료")
    print(f"  검증 항목: {len(val_df)}건")
    print(f"  제외 데이터: {len(inv_df)}건")
    for _, r in val_df.iterrows():
        symbol = "✅" if r["상태"] == "통과" else "❌"
        print(f"  {symbol} {r['항목']}: {r['상태']} ({r['내용']})")
    print(f"  저장: validation_results.csv, invalid_records.csv")


if __name__ == "__main__":
    run_validation()
