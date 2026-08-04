"""고객분석용 현실적인 더미 CSV를 생성한다."""

from datetime import datetime, timedelta
from pathlib import Path
import random

import pandas as pd


SEED = 20260803
CUSTOMER_COUNT = 100
INPUT_DIR = Path(__file__).resolve().parents[1] / "input"
BASE_DATE = datetime(2026, 7, 31)

REGIONS = ["애월읍", "한림읍", "조천읍", "구좌읍", "성산읍", "표선면", "대정읍", "중문동", "서귀동", "노형동"]
REGION_COORDINATES = {
    "애월읍": (33.462, 126.329), "한림읍": (33.410, 126.267),
    "조천읍": (33.542, 126.642), "구좌읍": (33.522, 126.853),
    "성산읍": (33.448, 126.910), "표선면": (33.326, 126.832),
    "대정읍": (33.226, 126.252), "중문동": (33.251, 126.413),
    "서귀동": (33.247, 126.561), "노형동": (33.483, 126.477),
}
SHIPPING_HUBS = {
    "제주 물류센터": (33.499, 126.531),
    "서귀포 물류센터": (33.254, 126.560),
    "애월 물류센터": (33.462, 126.329),
}
INDUSTRIES = ["카페", "음식점", "호텔", "세탁소", "병원", "학교", "사무실", "의류매장"]
ITEMS = {
    "와이셔츠": (10000, 18000),
    "정장": (35000, 75000),
    "이불": (25000, 60000),
    "유니폼": (18000, 45000),
    "운동화": (12000, 30000),
    "커튼": (30000, 90000),
    "수건": (5000, 20000),
    "작업복": (15000, 40000),
}
FAMILY_NAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
GIVEN_NAMES = ["민준", "서연", "도윤", "지우", "현우", "수빈", "지훈", "예은", "준서", "하윤"]


def random_date(start, end, rng):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def build_members(rng):
    rows = []
    for number in range(1, CUSTOMER_COUNT + 1):
        signup_date = random_date(datetime(2025, 1, 1), datetime(2026, 7, 20), rng)
        rows.append({
            "customer_id": f"C{number:03d}",
            "customer_name": rng.choice(FAMILY_NAMES) + rng.choice(GIVEN_NAMES),
            "signup_date": signup_date.strftime("%Y-%m-%d"),
            "region": rng.choice(REGIONS),
            "industry": rng.choice(INDUSTRIES),
        })

    # 실제 수집 데이터처럼 선택 정보에 일부 결측치를 둔다.
    for index in rng.sample(range(CUSTOMER_COUNT), 5):
        rows[index]["region"] = ""
    for index in rng.sample(range(CUSTOMER_COUNT), 4):
        rows[index]["industry"] = ""
    for index in rng.sample(range(CUSTOMER_COUNT), 2):
        rows[index]["customer_name"] = ""
    return pd.DataFrame(rows)


def build_orders(rng):
    rows = []
    order_number = 1
    # 일반적인 서비스 분포를 반영하되 고객별 군 배정은 매번 섞는다.
    group_plan = (
        ["new"] * 12
        + ["returning"] * 58
        + ["churn"] * 15
        + ["general"] * 15
    )
    rng.shuffle(group_plan)

    def add_order(customer_id, order_date):
        nonlocal order_number
        item = rng.choice(list(ITEMS))
        low, high = ITEMS[item]
        rows.append({
            "order_id": f"O{order_number:04d}",
            "customer_id": customer_id,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "item_name": item,
            "order_amount": rng.randrange(low, high + 1000, 1000),
        })
        order_number += 1

    for number, customer_type in enumerate(group_plan, start=1):
        customer_id = f"C{number:03d}"
        if customer_type == "new":  # 신규: 조회 기간 내 첫 주문
            add_order(customer_id, random_date(datetime(2026, 7, 25), BASE_DATE, rng))
        elif customer_type == "returning":  # 재이용: 과거 주문과 최근 재주문
            first = random_date(datetime(2026, 2, 1), datetime(2026, 4, 30), rng)
            add_order(customer_id, first)
            # 일부는 주문 2회로 만들어 재이용 고객이지만 이탈 판정은 보류되게 한다.
            if rng.random() >= 0.20:
                for _ in range(rng.randint(1, 3)):
                    first += timedelta(days=rng.randint(20, 50))
                    if first < datetime(2026, 7, 20):
                        add_order(customer_id, first)
            add_order(customer_id, random_date(datetime(2026, 7, 25), BASE_DATE, rng))
        elif customer_type == "churn":  # 이탈 위험: 일정한 이용 후 장기간 미방문
            first = random_date(datetime(2026, 1, 1), datetime(2026, 2, 15), rng)
            cycle = rng.randint(18, 35)
            add_order(customer_id, first)
            add_order(customer_id, first + timedelta(days=cycle))
            add_order(customer_id, first + timedelta(days=cycle * 2))
        else:  # 일반: 오래된 단건 이용자
            add_order(customer_id, random_date(datetime(2026, 1, 1), datetime(2026, 6, 30), rng))

    return pd.DataFrame(rows)


def build_deliveries(orders, members, rng):
    rows = []
    member_regions = members.set_index("customer_id")["region"].to_dict()
    for _, order in orders.iterrows():
        # 방문 수령이나 아직 배차되지 않은 주문은 배송 레코드가 없을 수 있다.
        if rng.random() < 0.10:
            continue
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
        status = rng.choices(["완료", "배송중", "지연", "취소"], [82, 9, 6, 3])[0]
        delivery_date = order_date + timedelta(days=rng.randint(1, 5))
        destination_region = member_regions.get(order["customer_id"]) or rng.choice(REGIONS)
        destination_lat, destination_lon = REGION_COORDINATES[destination_region]
        destination_lat += rng.uniform(-0.018, 0.018)
        destination_lon += rng.uniform(-0.025, 0.025)
        origin_hub = rng.choices(list(SHIPPING_HUBS), weights=[60, 25, 15])[0]
        origin_lat, origin_lon = SHIPPING_HUBS[origin_hub]
        origin_lat += rng.uniform(-0.004, 0.004)
        origin_lon += rng.uniform(-0.006, 0.006)
        rows.append({
            "order_id": order["order_id"],
            "delivery_date": "" if rng.random() < 0.03 else delivery_date.strftime("%Y-%m-%d"),
            "delivery_status": status,
            "origin_hub": origin_hub,
            "origin_latitude": round(origin_lat, 6),
            "origin_longitude": round(origin_lon, 6),
            "destination_region": destination_region,
            "destination_latitude": round(destination_lat, 6),
            "destination_longitude": round(destination_lon, 6),
        })
    return pd.DataFrame(rows)


def build_invalid_orders(orders):
    duplicate_id = orders.iloc[0]["order_id"]
    return pd.DataFrame([
        ["X0001", "", "2026-07-30", "수건", "12000"],
        ["X0002", "C999", "2026-07-29", "정장", "55000"],
        [duplicate_id, "C001", "2026-07-28", "이불", "30000"],
        ["X0004", "C010", "2026-13-01", "커튼", "45000"],
        ["X0005", "C020", "", "유니폼", "22000"],
        ["X0006", "C030", "2026-07-25", "운동화", "금액미상"],
        ["", "C040", "2026-07-24", "작업복", "18000"],
        ["X0008", "C050", "2026-07-23", "", "15000"],
        ["X0009", "C060", "2026-07-22", "와이셔츠", "-5000"],
        ["X0010", "C070", "날짜미상", "수건", "9000"],
        ["X0011", "", "2026-07-20", "이불", "40000"],
        ["X0012", "C080", "2026-07-19", "정장", ""],
    ], columns=["order_id", "customer_id", "order_date", "item_name", "order_amount"])


def main():
    rng = random.Random(SEED)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    members = build_members(rng)
    orders = build_orders(rng)
    deliveries = build_deliveries(orders, members, rng)
    invalid_orders = build_invalid_orders(orders)

    datasets = {
        "members.csv": members,
        "orders.csv": orders,
        "deliveries.csv": deliveries,
        "invalid_orders.csv": invalid_orders,
    }
    for filename, dataframe in datasets.items():
        dataframe.to_csv(INPUT_DIR / filename, index=False, encoding="utf-8-sig")
        print(f"{filename}: {len(dataframe)}행")


if __name__ == "__main__":
    main()
