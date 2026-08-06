"""launch-dashboard 스킬의 HTML 아티팩트 대안.

Next.js 대시보드를 브라우저로 열 수 없는 실행 환경(예: 타임리 샌드박스)에서,
사용자가 "HTML로 만들어줘"라고 요청했을 때 쓴다. 조회기간 기준 고객군 분류 같은
실제 계산은 이미 검증된 Next.js API(`/api/customers`, `/api/products`)가 그대로
수행하고, 이 스크립트는 그 결과를 curl 대신 표준 라이브러리로 호출해 정적
HTML로 옮기기만 한다 — 계산 로직을 파이썬으로 다시 구현하지 않는다.

사용법:
    python3 -m services.report.dashboard_artifact
    python3 -m services.report.dashboard_artifact --from 2026-06-01 --to 2026-06-07
"""

import argparse
import json
import urllib.request
from pathlib import Path

from shared.paths import REPO_ROOT


def fetch_json(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def bar_rows(items, label_key, value_key, unit="", color="#38bdf8", limit=10):
    items = items[:limit]
    max_value = max((item.get(value_key, 0) for item in items), default=1) or 1
    rows = []
    for item in items:
        value = item.get(value_key, 0)
        width = round(value / max_value * 100, 1)
        rows.append(
            f'<div class="bar-row">'
            f'<span class="bar-label">{esc(item.get(label_key, "미상"))}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%;background:{color}"></div></div>'
            f'<span class="bar-value">{value:,}{unit}</span>'
            f"</div>"
        )
    return "\n".join(rows) or '<p class="muted">데이터 없음</p>'


def render(customers, products, period_label, source):
    group_colors = {"신규 고객": "#38bdf8", "일반 고객": "#94a3b8", "재이용 고객": "#4ade80", "이탈 위험 고객": "#f87171"}
    group_summary = customers.get("groupSummary", [])
    total_customers = customers.get("totalCustomers", 0)
    risk_customers = customers.get("riskCustomers", 0)
    returning_customers = customers.get("returningCustomers", 0)
    operations = customers.get("operations", {})

    group_rows = "\n".join(
        f'<div class="bar-row">'
        f'<span class="bar-label">{esc(row["name"])}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{round(row["count"]/max(total_customers,1)*100,1)}%;'
        f'background:{group_colors.get(row["name"], "#38bdf8")}"></div></div>'
        f'<span class="bar-value">{row["count"]:,}명</span>'
        f"</div>"
        for row in group_summary
    ) or '<p class="muted">데이터 없음</p>'

    region_rows = bar_rows(
        sorted(customers.get("regions", []), key=lambda r: -r.get("customers", 0)),
        "name", "customers", "명", "#818cf8",
    )
    product_items = sorted(products.get("productAnalytics", []), key=lambda p: -p.get("orders", 0))
    product_rows = bar_rows(product_items, "name", "orders", "건", "#facc15")

    kpis = [
        ("전체 고객", f"{total_customers:,}명", "#38bdf8"),
        ("조회기간 주문", f"{operations.get('orders', 0):,}건", "#818cf8"),
        ("재이용 고객", f"{returning_customers:,}명", "#4ade80"),
        ("이탈 위험 고객", f"{risk_customers:,}명", "#f87171"),
    ]
    kpi_html = "\n".join(
        f'<div class="kpi"><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value" style="color:{color}">{esc(value)}</div></div>'
        for label, value, color in kpis
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>잇뉴 대시보드 요약 — {esc(period_label)}</title>
<style>
  :root{{--bg:#0f172a;--panel:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:-apple-system,'Noto Sans KR',sans-serif;padding:24px}}
  h1{{font-size:20px;margin-bottom:4px}}
  .sub{{color:var(--muted);font-size:13px;margin-bottom:20px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px}}
  .kpi{{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px}}
  .kpi-label{{font-size:11px;color:var(--muted);text-transform:uppercase}}
  .kpi-value{{font-size:22px;font-weight:700;margin-top:4px}}
  .card{{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:16px}}
  .card h2{{font-size:13px;color:var(--muted);text-transform:uppercase;margin-bottom:12px}}
  .bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px}}
  .bar-label{{width:110px;flex-shrink:0;text-align:right;color:var(--text)}}
  .bar-track{{flex:1;background:#0b1220;border-radius:6px;height:14px;overflow:hidden}}
  .bar-fill{{height:100%;border-radius:6px}}
  .bar-value{{width:60px;flex-shrink:0;color:var(--muted)}}
  .muted{{color:var(--muted);font-size:12px}}
  .footer{{color:var(--muted);font-size:11px;margin-top:12px}}
</style>
</head>
<body>
  <h1>잇뉴 대시보드 요약</h1>
  <div class="sub">조회기간: {esc(period_label)} · 데이터 출처: {esc(source)}</div>

  <div class="grid">{kpi_html}</div>

  <div class="card"><h2>고객군 분포</h2>{group_rows}</div>
  <div class="card"><h2>지역별 고객 분포 (상위 10)</h2>{region_rows}</div>
  <div class="card"><h2>품목별 주문 건수 (상위 10)</h2>{product_rows}</div>

  <div class="footer">Next.js API(/api/customers, /api/products)가 실시간 계산한 값을 그대로 옮긴 정적 요약입니다. 계산 로직은 이 스크립트에 없습니다.</div>
</body>
</html>"""


def build_artifact(date_from="", date_to="", base_url="http://localhost:3000", out_path=None):
    query = f"?from={date_from}&to={date_to}" if date_from or date_to else ""
    customers = fetch_json(f"{base_url}/api/customers{query}")
    products = fetch_json(f"{base_url}/api/products{query}")
    period_label = f"{date_from} ~ {date_to}" if date_from else "전체 기간"
    html = render(customers, products, period_label, base_url)
    out = Path(out_path) if out_path else REPO_ROOT / "dashboard_artifact.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ HTML 대시보드 생성: {out} ({len(html):,} bytes)")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", default="")
    parser.add_argument("--to", dest="date_to", default="")
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    build_artifact(args.date_from, args.date_to, args.base_url, args.out)


if __name__ == "__main__":
    main()
