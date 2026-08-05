"""
run_analysis.py — run-customer-analysis 스킬의 실제 실행 스크립트

사용자가 Timely 대화에 첨부한 엑셀(잇뉴 주문·회원 데이터)을 찾아
고객분석 전체 파이프라인을 자동 실행한다.

실행 로직:
1. 첨부 엑셀 탐색 (프로젝트 루트 직하 *.xlsx 우선)
2. Excel → CSV 변환 (services.customer.import_real_data)
3. 고객분석 파이프라인 전체 실행 (services.customer.pipeline)
4. data/output/ 결과 요약 출력 (고객군 분포 + AI 요약 + 대시보드 안내)

이 스크립트는 runpy 로 pipeline.py 를 실행하므로
services.customer 를 import 할 수 있도록 sys.path 에 프로젝트 루트를 추가한다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# 프로젝트 루트 탐색: 이 스크립트 위치 기준으로 services/ 가 보일 때까지 상위 탐색
# ----------------------------------------------------------------------
_SCRIPT = Path(__file__).resolve()
_SCRIPT_DIR = _SCRIPT.parent


def find_project_root() -> Path:
    """script_dir 기준 상위 n단계 중 services/ + data/ 가 둘 다 있는 첫 경로를 반환."""
    for n in range(1, 8):
        parent = _SCRIPT_DIR.parents[n - 1] if n <= len(list(_SCRIPT_DIR.parents)) else None
        if parent is None:
            break
        if (parent / "services").exists() and (parent / "data").exists():
            return parent
    raise RuntimeError("프로젝트 루트(services/ + data/ 있는 경로)을 찾지 못함")


PROJECT_ROOT = find_project_root()
sys.path.insert(0, str(PROJECT_ROOT))

# ----------------------------------------------------------------------
# 1. 첨부 엑셀 탐색
# ----------------------------------------------------------------------


def find_attached_excel() -> Path | None:
    """프로젝트 루트 직하 *.xlsx → 상위 rglob → 환경변수 순으로 엑셀 탐색."""
    # (a) 프로젝트 루트 직하
    for f in PROJECT_ROOT.glob("*.xlsx"):
        return f

    # (b) 상위 4레벨 rglob (첫 번째 발견 기준)
    for n in range(1, 5):
        parent = PROJECT_ROOT.parent
        if n > 1:
            parent = parent.parent if parent.parent != parent else parent
        for f in parent.rglob("*.xlsx"):
            return f

    # (c) 환경변수
    for key in ("ATTACHED_FILE", "EXCEL_PATH", "DATA_FILE", "INPUT_FILE", "FILE_PATH"):
        v = os.environ.get(key)
        if v and Path(v).exists():
            return Path(v)

    return None


# ----------------------------------------------------------------------
# 2. Excel → CSV 변환 (import_real_data 의 변환 로직만 사용)
# ----------------------------------------------------------------------


def import_excel_to_csv(excel_path: Path) -> dict[str, Path]:
    """
    첨부 Excel 파일을 data/input/ 의 members.csv / orders.csv /
    deliveries.csv / invalid_orders.csv 로 변환한다.

    services.customer.import_real_data 의 실제 변환 함수를 호출하되,
    중복 변환을 막기 위해 export_real_data(변환 후 CSV를 output에 복사하는 함수)는
    no-op 으로 패치한다.
    """
    import types
    import importlib

    # import_real_data 모듈을 import
    import_real_data = importlib.import_module("services.customer.import_real_data")

    # export_real_data 가 있으면 no-op 으로 덮어쓴다 (이미 data/input/ 에 CSV가 생기므로)
    if hasattr(import_real_data, "export_real_data"):
        import_real_data.export_real_data = lambda *a, **k: None  # type: ignore[method-assign]

    # 메인 변환 함수 호출. 모듈에 run() 또는 convert() 가 있으면 그걸, 없으면
    # 직접 두 시트를 읽는 코드를 실행.
    func = getattr(import_real_data, "run", None) or getattr(import_real_data, "convert", None)
    if callable(func):
        result = func(str(excel_path))
    else:
        # import_real_data 모듈의 상수와 함수를 직접 사용
        src = excel_path
        INPUT_DIR = PROJECT_ROOT / "data" / "input"
        OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        import pandas as pd

        xls = pd.ExcelFile(src)
        orders_df = pd.read_excel(xls, sheet_name="주문_2026년1-6월")
        members_df = pd.read_excel(xls, sheet_name="회원_전체누적")

        # 컬럼 매핑 (import_real_data.py 와 동일한 매핑)
        col_map_orders = {
            "배송일": "order_date",
            "접수형태": "order_type",
            "고객(사)명": "customer_name",
            "요청사항": "request",
            "수거지 주소": "pickup_address",
            "송화인": "sender",
            "배송지 주소": "delivery_address",
            "배송물품 품목명": "item_name",
            "수량": "quantity",
            "주문 접수 시간": "order_time",
        }
        col_map_members = {
            "회원명(가명)": "customer_name",
            "회원유형": "member_type",
            "성별": "gender",
            "연령": "age",
            "가입일시": "signup_date",
        }

        def rename_cols(df: "pd.DataFrame", mapping: dict[str, str]) -> "pd.DataFrame":
            rename = {c: mapping[c] for c in df.columns if c in mapping}
            return df.rename(columns=rename)

        orders_df = rename_cols(orders_df, col_map_orders)
        members_df = rename_cols(members_df, col_map_members)

        # _customer_id 할당: orders.customer_name → members 기준 인덱스
        name_to_id = {name: i + 1 for i, name in enumerate(members_df["customer_name"].dropna().unique())}
        orders_df["_customer_id"] = orders_df["customer_name"].map(name_to_id).fillna(0).astype(int)

        # 목적지/수거지 지역 추출
        def extract_region(addr: str | float) -> str | None:
            if pd.isna(addr):
                return None
            addr = str(addr)
            for token in addr.split():
                token = token.strip()
                if len(token) >= 2 and ("도" in token or "시" in token or "군" in token or "구" in token):
                    return token
            parts = addr.split()
            if parts:
                return parts[-1][:4]
            return None

        orders_df["_region"] = orders_df["delivery_address"].map(extract_region)

        # CSV 저장
        members_df.to_csv(INPUT_DIR / "members.csv", index=False)
        orders_df.to_csv(INPUT_DIR / "orders.csv", index=False)

        # deliveries.csv, invalid_orders.csv 는 빈 파일(또는 orders 기반)로 생성
        pd.DataFrame(columns=["order_id", "delivery_status", "delivery_day", "driver"]).to_csv(
            INPUT_DIR / "deliveries.csv", index=False
        )
        pd.DataFrame(columns=["order_id", "reason"]).to_csv(
            INPUT_DIR / "invalid_orders.csv", index=False
        )

        result = {
            "members": INPUT_DIR / "members.csv",
            "orders": INPUT_DIR / "orders.csv",
            "deliveries": INPUT_DIR / "deliveries.csv",
            "invalid_orders": INPUT_DIR / "invalid_orders.csv",
        }

    return result  # type: ignore[return-value]


# ----------------------------------------------------------------------
# 3. 파이프라인 실행
# ----------------------------------------------------------------------


def run_pipeline() -> None:
    """services.customer.pipeline 모듈을 run_mode='__main__' 로 실행."""
    import runpy
    import types

    # import_real_data 중복 변환 방지를 위해 no-op 패치한 상태로 pipeline 실행
    pipeline = importlib.import_module("services.customer.pipeline")  # noqa: F811
    runpy.run_module("services.customer.pipeline", run_name="__main__", alter_sys=True)


# ----------------------------------------------------------------------
# 4. 결과 요약
# ----------------------------------------------------------------------


def summarize_output() -> None:
    """data/output/ 의 결과 파일을 간단히 요약 출력."""
    OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
    if not OUTPUT_DIR.exists():
        print("결과 디렉토리 없음:", OUTPUT_DIR)
        return

    files = sorted(OUTPUT_DIR.iterdir())
    csv_files = [f for f in files if f.suffix == ".csv"]
    txt_files = [f for f in files if f.suffix == ".txt"]
    md_files = [f for f in files if f.suffix == ".md"]

    print("\n=== 파이프라인 결과 ===")
    print(f"data/output/ 파일 수: {len(files)}개")
    print(f"  CSV: {len(csv_files)}개")
    print(f"  TXT: {len(txt_files)}개")
    print(f"  MD : {len(md_files)}개")
    print("")
    print("생성된 파일:")
    for f in files:
        size = f.stat().st_size
        print(f"  {f.name:40s} {size:>10,} bytes")

    # 고객군 분포 읽기
    groups_path = OUTPUT_DIR / "customer_groups.csv"
    if groups_path.exists():
        import csv
        from collections import Counter
        cnt: Counter[str] = Counter()
        with groups_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                g = row.get("customer_group") or row.get("group") or row.get("구분") or ""
                if g:
                    cnt[g] += 1
        total = sum(cnt.values())
        print("")
        print("고객군 분포:")
        for g, c in cnt.most_common():
            pct = (c / total * 100) if total else 0
            print(f"  {g}: {c}명 ({pct:.1f}%)")
        print(f"  합계: {total}명")

    # AI 요약 앞부분
    ai_path = OUTPUT_DIR / "ai_summary.txt"
    if ai_path.exists():
        text = ai_path.read_text(encoding="utf-8").strip()
        preview = text.splitlines()[:6]
        print("")
        print("AI 요약 (ai_summary.txt 앞부분):")
        for line in preview:
            print(f"  {line}")

    print("")
    print("=== Next.js 대시보드 실행 ===")
    print("웹 대시보드에서 결과를 보려면:")
    print("  cd web && npm run dev")
    print("")
    print("Streamlit 대시보드(과거)를 쓰려면:")
    print(f"  streamlit run {PROJECT_ROOT / 'app.py'}")
    print("")


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def main() -> None:
    import importlib  # reuse inside functions

    print("=== run-customer-analysis 시작 ===")
    print(f"프로젝트 루트: {PROJECT_ROOT}")

    # 1. 엑셀 찾기
    excel = find_attached_excel()
    if excel is None:
        print("오류: 첨부 엑셀 파일을 찾지 못함.")
        print("Timely 대화에 엑셀 파일을 첨부한 뒤 다시 실행해줘.")
        sys.exit(1)
    print(f"첨부 엑셀: {excel.name} ({excel.stat().st_size:,} bytes)")

    # 2. CSV 변환
    print("\n--- Excel → CSV 변환 중 ---")
    try:
        converted = import_excel_to_csv(excel)
    except Exception as e:
        print(f"Excel 변환 중 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

    print("변환 완료:")
    for name, path in converted.items():
        print(f"  {name}: {path.name} ({path.stat().st_size:,} bytes)")

    # 3. 파이프라인 실행
    print("\n--- 고객분석 파이프라인 실행 중 ---")
    try:
        run_pipeline()
    except Exception as e:
        print(f"파이프라인 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)

    # 4. 결과 요약
    print("\n--- 결과 요약 ---")
    summarize_output()


if __name__ == "__main__":
    main()
