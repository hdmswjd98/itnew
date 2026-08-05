"""상세주소를 Kakao Local API로 좌표화하고 비식별 좌표 캐시를 생성한다."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import time

import pandas as pd

from .import_real_data import find_source_excel
from .paths import OUTPUT_DIR, ensure_data_dirs


REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = OUTPUT_DIR / "geocode_cache.json"
COORDINATES_PATH = OUTPUT_DIR / "order_coordinates.csv"


def _load_key():
    key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    env_path = REPO_ROOT / ".env"
    if not key and env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("KAKAO_REST_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"\'')
                break
    if not key:
        raise RuntimeError("KAKAO_REST_API_KEY가 .env에 없습니다.")
    return key


def _hash(address):
    return sha256(address.strip().encode("utf-8")).hexdigest()


def _queries(address):
    address = re.sub(r"\s+", " ", str(address)).strip()
    yield address
    simplified = re.sub(r"\s+(지하|지상)?\d+층.*$", "", address)
    simplified = re.sub(r"\s+\d+호.*$", "", simplified)
    if simplified != address:
        yield simplified


def _geocode_one(address, key):
    for query in _queries(address):
        try:
            response = subprocess.run([
                "curl", "-sS", "--fail", "--max-time", "15", "-G",
                "https://dapi.kakao.com/v2/local/search/address.json",
                "-H", f"Authorization: KakaoAK {key}",
                "--data-urlencode", f"query={query}", "--data", "size=1",
            ], capture_output=True, text=True, timeout=20, check=True)
            payload = json.loads(response.stdout)
            if payload.get("documents"):
                result = payload["documents"][0]
                return {"lon": float(result["x"]), "lat": float(result["y"]), "ok": True}
        except Exception as error:
            return {"ok": False, "error": type(error).__name__}
    return {"ok": False, "error": "not_found"}


def geocode_orders(limit=None):
    ensure_data_dirs()
    key = _load_key()
    source = find_source_excel()
    orders = pd.read_excel(source, sheet_name="주문_2026년1-6월", usecols=["수거지 주소", "배송지 주소"])
    addresses = sorted(set(orders["수거지 주소"].dropna().astype(str).str.strip()) | set(orders["배송지 주소"].dropna().astype(str).str.strip()))
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    pending = [address for address in addresses if not cache.get(_hash(address), {}).get("ok")]
    if limit:
        pending = pending[:limit]
    print(f"지오코딩 대상: 전체 고유주소 {len(addresses):,}개 / 신규 {len(pending):,}개")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_geocode_one, address, key): address for address in pending}
        for index, future in enumerate(as_completed(futures), 1):
            address = futures[future]
            cache[_hash(address)] = future.result()
            if index % 100 == 0:
                CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
                print(f"  {index:,}/{len(pending):,} 완료")
            time.sleep(0.01)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    def coordinate(address, key_name):
        result = cache.get(_hash(str(address).strip()), {})
        return result.get(key_name) if result.get("ok") else None

    output = pd.DataFrame({
        "order_id": [f"REAL{i:06d}" for i in range(1, len(orders) + 1)],
        "origin_lon": orders["수거지 주소"].map(lambda value: coordinate(value, "lon")),
        "origin_lat": orders["수거지 주소"].map(lambda value: coordinate(value, "lat")),
        "destination_lon": orders["배송지 주소"].map(lambda value: coordinate(value, "lon")),
        "destination_lat": orders["배송지 주소"].map(lambda value: coordinate(value, "lat")),
    })
    output.to_csv(COORDINATES_PATH, index=False, encoding="utf-8-sig")
    success = sum(1 for value in cache.values() if value.get("ok"))
    print(f"좌표 변환 완료: {success:,}/{len(cache):,}개 고유주소")
    print(f"주문 좌표 저장: {COORDINATES_PATH} ({output[['origin_lat','destination_lat']].notna().sum().sum():,}개 좌표)")
    return output


if __name__ == "__main__":
    geocode_orders()
