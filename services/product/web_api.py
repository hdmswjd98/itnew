"""Next.js 서버가 기존 품목 분석 서비스를 호출하는 JSON 표준입출력 진입점."""

from contextlib import redirect_stdout
import io
import json
import sys

from .classifier import classify_products
from .rules import save_exact_rules


def _classify_without_console_output():
    logs = io.StringIO()
    with redirect_stdout(logs):
        result = classify_products()
    if not result or not result.get("ok"):
        raise RuntimeError((result or {}).get("message", "품목 자동분류에 실패했습니다."))
    return result


def handle(payload):
    action = payload.get("action")
    if action == "refresh":
        return _classify_without_console_output()
    if action == "save_rules":
        save_exact_rules(
            payload.get("itemNames", []),
            payload.get("mainCategory", ""),
            payload.get("subcategory", ""),
        )
        result = _classify_without_console_output()
        result["saved"] = len(payload.get("itemNames", []))
        return result
    raise ValueError(f"지원하지 않는 작업입니다: {action}")


def main():
    try:
        payload = json.load(sys.stdin)
        print(json.dumps({"ok": True, "data": handle(payload)}, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
