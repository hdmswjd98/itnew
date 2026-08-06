"""제공받은 익명 Excel을 분석용 표준 CSV로 변환한다."""

from hashlib import sha256
import re
import unicodedata

import pandas as pd

from .paths import INPUT_DIR, RAW_DIR, REPO_ROOT, ensure_data_dirs


JEJU_UNITS = [
    "애월읍", "한림읍", "조천읍", "구좌읍", "성산읍", "표선면", "남원읍",
    "대정읍", "안덕면", "한경면", "연동", "노형동", "중문동", "서귀동",
    "동홍동", "서홍동", "법환동", "보목동", "하효동", "외도일동", "이도이동",
    "이도일동", "아라일동", "아라이동", "삼도일동", "삼도이동", "용담일동",
    "용담이동", "도두일동", "도두이동", "화북일동", "화북이동", "삼양일동",
    "삼양이동", "건입동", "일도일동", "일도이동", "오라일동", "오라이동",
    "오라삼동", "봉개동", "영평동", "월평동", "강정동", "대포동", "색달동",
]


def _customer_id(alias):
    return "C_" + sha256(str(alias).strip().encode("utf-8")).hexdigest()[:12].upper()


def _region(address):
    text = str(address)
    for unit in JEJU_UNITS:
        if unit in text:
            return unit
    return "미상"


def find_source_excel():
    candidates = [path for path in RAW_DIR.glob("*.xlsx") if not path.name.startswith("~$")]
    if candidates:
        return candidates[0]
    # data/raw/에 없으면 워크스페이스 루트에서 찾는다 (에이전트 실행 환경이 업로드 파일을
    # data/raw/가 아니라 루트에 놓는 경우 대응 — 예: Timely 채팅 파일 업로드는 워크스페이스
    # 루트에 자동 배치됨)
    root_candidates = [path for path in REPO_ROOT.glob("*.xlsx") if not path.name.startswith("~$")]
    if root_candidates:
        return root_candidates[0]
    raise FileNotFoundError(f"{RAW_DIR} 또는 워크스페이스 루트에서 실제 데이터 Excel을 찾지 못했습니다. 원본 엑셀 파일을 업로드해주세요.")


def import_real_data():
    """Excel 두 시트를 개인정보가 제거된 분석용 CSV 세 개로 변환한다."""
    ensure_data_dirs()
    source = find_source_excel()
    orders_raw = pd.read_excel(source, sheet_name="주문_2026년1-6월")
    members_raw = pd.read_excel(source, sheet_name="회원_전체누적")

    alias_to_id = {
        str(alias).strip(): _customer_id(alias)
        for alias in members_raw["회원명(가명)"].dropna().unique()
    }
    members = pd.DataFrame({
        "customer_id": members_raw["회원명(가명)"].astype(str).str.strip().map(alias_to_id),
        "signup_date": pd.to_datetime(members_raw["가입일시"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S"),
        "member_type": members_raw["회원유형"].fillna("미상"),
        "gender": members_raw["성별"].fillna("미상"),
        "age_group": members_raw["연령"].fillna("미상"),
    })

    customer_aliases = orders_raw["고객(사)명"].astype(str).str.strip()
    orders = pd.DataFrame({
        "order_id": [f"REAL{i:06d}" for i in range(1, len(orders_raw) + 1)],
        "customer_id": customer_aliases.map(alias_to_id),
        "order_date": pd.to_datetime(orders_raw["주문 접수 시간"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S"),
        "item_name": orders_raw["배송물품 품목명"].fillna("미상"),
        "order_quantity": pd.to_numeric(orders_raw["수량"], errors="coerce"),
        "order_channel": orders_raw["접수형태"].fillna("미상"),
    })
    deliveries = pd.DataFrame({
        "order_id": orders["order_id"],
        "delivery_date": pd.to_datetime(orders_raw["배송일"], errors="coerce").dt.strftime("%Y-%m-%d"),
        "origin_region": orders_raw["수거지 주소"].map(_region),
        "destination_region": orders_raw["배송지 주소"].map(_region),
    })

    members.to_csv(INPUT_DIR / "members.csv", index=False, encoding="utf-8-sig")
    orders.to_csv(INPUT_DIR / "orders.csv", index=False, encoding="utf-8-sig")
    deliveries.to_csv(INPUT_DIR / "deliveries.csv", index=False, encoding="utf-8-sig")

    print(f"✅ 실제 데이터 변환 완료: {source.name}")
    print(f"  회원 {len(members):,}명 / 배송 주문 {len(orders):,}건")
    print(f"  주문 고객 {orders['customer_id'].nunique():,}명")
    print(f"  목적지 지역 추출률 {(deliveries['destination_region'] != '미상').mean() * 100:.1f}%")
    print(f"  수거지 지역 추출률 {(deliveries['origin_region'] != '미상').mean() * 100:.1f}%")
    return members, orders, deliveries


if __name__ == "__main__":
    import_real_data()
