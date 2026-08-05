"""
test_env.py — Timely 스킬 실행 환경 검사 (run-customer-analysis 용)

이 스크립트는 Timely가 스킬 스크립트를 실행할 때의 환경을 기록한다:
- cwd, argv, 환경변수
- 프로젝트 루트에 있는 xlsx 파일 목록
- data/ 디렉토리 상태 (input/output)
- services/customer/ 존재 여부
- find_source_excel() 테스트

결과: JSON 비슷한 형태로 stdout 에 출력. 사용자는 이 결과를 보고
run_analysis.py 가 엑셀 파일 경로를 어떻게 받을지 결정한다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main():
    cwd = Path.cwd()
    script = Path(sys.argv[0]).resolve() if sys.argv else Path("<unknown>")
    script_dir = script.parent

    lines = []
    lines.append("=== Timely 스킬 실행 환경 검사 ===")
    lines.append(f"cwd           : {cwd}")
    lines.append(f"script        : {script}")
    lines.append(f"script_dir    : {script_dir}")
    lines.append(f"argv          : {sys.argv!r}")
    lines.append("")

    # 환경변수 중 파일 경로와 관련 있을 법한 것들
    lines.append("=== 환경변수 (파일 경로 관련) ===")
    keys_of_interest = [
        "ATTACHED_FILE", "EXCEL_PATH", "DATA_FILE", "INPUT_FILE",
        "FILE_PATH", "TIMELY_FILE", "UPLOADED_FILE",
    ]
    found = False
    for k in keys_of_interest:
        v = os.environ.get(k)
        if v:
            lines.append(f"  {k} = {v}")
            found = True
    if not found:
        lines.append("  (해당 환경변수 없음)")
    lines.append("")

    # 프로젝트 루트 추정: script_dir 기준 4~5단계 상위
    candidates = []
    for n in range(2, 7):
        p = script_dir.parents[n - 1] if n <= len(list(script_dir.parents)) else None
        if p is not None:
            candidates.append((n, p))
    lines.append("=== 프로젝트 루트 후보 (script_dir.parent*n) ===")
    for n, p in candidates:
        has_services = (p / "services").exists()
        has_data = (p / "data").exists()
        has_pypi = (p / ".pi").exists()
        mark = ""
        if has_services and has_data:
            mark = "  <-- services+data 있음"
        lines.append(f"  parent[{n}] = {p}{mark}")
    lines.append("")

    # 프로젝트 루트 직하 xlsx 파일
    root = None
    for n, p in candidates:
        if (p / "services").exists() and (p / "data").exists():
            root = p
            break
    lines.append("=== 프로젝트 루트 직하 *.xlsx ===")
    if root:
        xlsx_files = sorted(root.glob("*.xlsx"))
        if xlsx_files:
            for f in xlsx_files:
                size = f.stat().st_size
                lines.append(f"  {f.name}  ({size:,} bytes)")
        else:
            lines.append("  (프로젝트 루트 직하 xlsx 없음)")
    else:
        lines.append("  (프로젝트 루트 판정 불가)")
    lines.append("")

    # data/ 디렉토리 상태
    lines.append("=== data/ 디렉토리 상태 ===")
    if root:
        for sub in ["input", "output"]:
            d = root / "data" / sub
            exists = d.exists()
            if exists:
                files = sorted(d.iterdir())
                file_list = ", ".join(f.name + ("/" if f.is_dir() else "") for f in files) or "(비어있음)"
                lines.append(f"  data/{sub}/ : 존재 — {file_list}")
            else:
                lines.append(f"  data/{sub}/ : 없음")
    else:
        lines.append("  (프로젝트 루트 판정 불가)")
    lines.append("")

    # services/customer/ 존재
    lines.append("=== services/customer/ ===")
    if root:
        sc = root / "services" / "customer"
        if sc.exists():
            pyfiles = sorted(p.name for p in sc.glob("*.py"))
            lines.append(f"  존재 — {len(pyfiles)}개 .py 파일: {', '.join(pyfiles)}")
        else:
            lines.append("  없음")
    else:
        lines.append("  (프로젝트 루트 판정 불가)")
    lines.append("")

    # find_source_excel() 흉내 테스트
    lines.append("=== find_source_excel() 테스트 ===")

    def find_source_excel():
        if root is None:
            return None
        # 1) 프로젝트 루트 직하
        for f in root.glob("*.xlsx"):
            return f
        # 2) 상위 디렉토리 rglob
        for n in range(1, 4):
            parent = root.parent
            for f in parent.rglob("*.xlsx"):
                # 부트캠프 폴더 조건은 무시 — 그냥 첫 xlsx 반환
                return f
        return None

    src = find_source_excel()
    if src:
        size = src.stat().st_size
        lines.append(f"  찾음: {src.name} ({size:,} bytes) — {src}")
    else:
        lines.append("  찾지 못함")

    lines.append("")
    lines.append("=== 검사 완료 ===")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
