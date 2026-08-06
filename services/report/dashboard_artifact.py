"""launch-dashboard 스킬의 HTML 아티팩트 대안.

Next.js 대시보드를 브라우저로 열 수 없는 실행 환경(예: 타임리 샌드박스)에서,
사용자가 "HTML로 만들어줘"라고 요청했을 때 쓴다. 조회기간 기준 고객군 분류 같은
실제 계산은 이미 검증된 Next.js API(`/api/customers`, `/api/products`)가 그대로
수행하고, 이 스크립트는 그 결과를 표준 라이브러리로 호출해 운영현황·고객분석·
품목분류 3개 탭의 정적 HTML로 옮기기만 한다 — 계산 로직을 파이썬으로 다시
구현하지 않는다. 탭 전환은 CSS(라디오버튼)만으로 동작해 외부 JS 의존이 없다.

배색은 실제 웹앱(web/src/app/globals.css)의 브랜드 컬러(남색 #13263d,
주황/골드 #fa9c00·#f6c453)를 그대로 따른다 — 고객군(신규/일반/재이용/이탈위험)은
상태를 나타내는 값이라 브랜드 색과 별도의 의미색(파랑/회색/초록/빨강)을 쓴다.

사용법:
    python3 -m services.report.dashboard_artifact
    python3 -m services.report.dashboard_artifact --from 2026-06-01 --to 2026-06-07
"""

import argparse
import json
import urllib.request
from pathlib import Path

from shared.paths import REPO_ROOT

GROUP_COLORS = {"신규 고객": "#2563eb", "일반 고객": "#64748b", "재이용 고객": "#16a34a", "이탈 위험 고객": "#dc2626"}
ACCENT = "var(--accent)"


def fetch_json(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def aggregate_by_name(items, name_key="name", value_key="orders"):
    """고객군별로 나뉜 항목(channels/industries 등)을 이름 기준으로 합산해 그룹 구분 없이 만든다."""
    totals = {}
    for item in items:
        name = item.get(name_key, "미상")
        totals[name] = totals.get(name, 0) + item.get(value_key, 0)
    return sorted(({"name": name, value_key: value} for name, value in totals.items()), key=lambda x: -x[value_key])


def hbar_rows(items, label_key, value_key, unit="", color=ACCENT, limit=10):
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


def vbar_chart(items, label_key, value_key, color=ACCENT):
    """요일별/시간대별처럼 순서가 고정된 항목을 세로 막대로 그린다."""
    max_value = max((item.get(value_key, 0) for item in items), default=1) or 1
    bars = []
    for item in items:
        value = item.get(value_key, 0)
        height = max(2, round(value / max_value * 100, 1))
        bars.append(
            f'<div class="vbar-col">'
            f'<div class="vbar-track"><div class="vbar-fill" style="height:{height}%;background:{color}"></div></div>'
            f'<span class="vbar-label">{esc(item.get(label_key, ""))}</span>'
            f"</div>"
        )
    return f'<div class="vbar-chart">{"".join(bars)}</div>' if bars else '<p class="muted">데이터 없음</p>'


def kpi_grid(kpis):
    return "\n".join(
        f'<div class="kpi"><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value" style="color:{color}">{esc(value)}</div></div>'
        for label, value, color in kpis
    )


def render_operations_tab(customers):
    operations = customers.get("operations", {})
    kpis = [
        ("조회기간 주문", f"{operations.get('orders', 0):,}건", ACCENT),
        ("직전 기간 주문", f"{operations.get('previousOrders', 0):,}건", "var(--muted)"),
        ("조회기간 신규 고객", f"{operations.get('newCustomers', 0):,}명", GROUP_COLORS["신규 고객"]),
        ("조회 일수", f"{operations.get('days', 0):,}일", "var(--navy-tint)"),
    ]
    weekday_html = vbar_chart(operations.get("weekdayOrders", []), "name", "orders", ACCENT)
    hourly_html = vbar_chart(operations.get("hourlyOrders", []), "hour", "orders", "var(--navy-tint)")
    monthly_rows = hbar_rows(
        sorted(operations.get("monthlyOrders", []), key=lambda m: m.get("month", "")),
        "month", "orders", "건", ACCENT, limit=12,
    )
    return f"""
    <div class="grid">{kpi_grid(kpis)}</div>
    <div class="card"><h2>요일별 주문량 (월~일)</h2>{weekday_html}</div>
    <div class="card"><h2>시간대별 주문량 (0~23시)</h2>{hourly_html}</div>
    <div class="card"><h2>월별 주문량</h2>{monthly_rows}</div>
    """


def render_customer_tab(customers):
    group_summary = customers.get("groupSummary", [])
    total_customers = customers.get("totalCustomers", 0)
    kpis = [
        ("전체 고객", f"{total_customers:,}명", "var(--text)"),
        ("재이용 고객", f"{customers.get('returningCustomers', 0):,}명", GROUP_COLORS["재이용 고객"]),
        ("이탈 위험 고객", f"{customers.get('riskCustomers', 0):,}명", GROUP_COLORS["이탈 위험 고객"]),
        ("이탈 분석 대상", f"{customers.get('eligibleCustomers', 0):,}명", "var(--muted)"),
    ]
    group_rows = "\n".join(
        f'<div class="bar-row">'
        f'<span class="bar-label"><span class="dot" style="background:{GROUP_COLORS.get(row["name"], ACCENT)}"></span>{esc(row["name"])}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{round(row["count"]/max(total_customers,1)*100,1)}%;'
        f'background:{GROUP_COLORS.get(row["name"], ACCENT)}"></div></div>'
        f'<span class="bar-value">{row["count"]:,}명</span>'
        f"</div>"
        for row in group_summary
    ) or '<p class="muted">데이터 없음</p>'
    region_rows = hbar_rows(
        sorted(customers.get("regions", []), key=lambda r: -r.get("customers", 0)),
        "name", "customers", "명", ACCENT,
    )
    industry_rows = hbar_rows(aggregate_by_name(customers.get("industries", []), "name", "customers"), "name", "customers", "명", "var(--navy-tint)")
    channel_rows = hbar_rows(aggregate_by_name(customers.get("channels", []), "name", "orders"), "name", "orders", "건", ACCENT)
    return f"""
    <div class="grid">{kpi_grid(kpis)}</div>
    <div class="card"><h2>고객군 분포</h2>{group_rows}</div>
    <div class="grid-2">
      <div class="card"><h2>지역별 고객 분포 (상위 10)</h2>{region_rows}</div>
      <div class="card"><h2>업종(회원유형) 분포</h2>{industry_rows}</div>
    </div>
    <div class="card"><h2>접수 형태 (B2B/B2C)</h2>{channel_rows}</div>
    """


def render_product_tab(products):
    total = products.get("total", 0)
    classified = products.get("classified", 0)
    rate = (classified / total * 100) if total else 0
    kpis = [
        ("전체 품목 건수", f"{total:,}건", "var(--text)"),
        ("자동분류율", f"{rate:.1f}%", GROUP_COLORS["재이용 고객"]),
        ("검토 필요", f"{products.get('reviewCount', 0):,}건", GROUP_COLORS["이탈 위험 고객"]),
        ("고유 품목", f"{products.get('uniqueItems', 0):,}개", ACCENT),
    ]
    product_items = sorted(products.get("productAnalytics", []), key=lambda p: -p.get("orders", 0))
    product_rows = hbar_rows(product_items, "name", "orders", "건", ACCENT)
    category_rows = hbar_rows(
        sorted(products.get("categories", []), key=lambda c: -c.get("count", 0)),
        "name", "count", "건", "var(--navy-tint)",
    )
    ai_report = products.get("aiReport", [])
    ai_html = "".join(f'<p>{esc(line)}</p>' for line in ai_report) or '<p class="muted">AI 요약 없음</p>'
    return f"""
    <div class="grid">{kpi_grid(kpis)}</div>
    <div class="grid-2">
      <div class="card"><h2>품목별 주문 건수 (상위 10)</h2>{product_rows}</div>
      <div class="card"><h2>대분류 현황</h2>{category_rows}</div>
    </div>
    <div class="card"><h2>AI 품목 리포트</h2><div class="ai-box">{ai_html}</div></div>
    """


def render(customers, products, period_label, source):
    operations_html = render_operations_tab(customers)
    customer_html = render_customer_tab(customers)
    product_html = render_product_tab(products)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>잇뉴 대시보드 요약 — {esc(period_label)}</title>
<style>
  :root{{
    --bg:#f6f8fb; --panel:#ffffff; --border:#e6eaf0; --text:#17202a; --muted:#64748b;
    --heading:#13263d; --navy-tint:#3a5578; --accent:#f6c453; --accent-soft:#fff5e6;
  }}
  @media (prefers-color-scheme: dark){{
    :root{{--bg:#111827;--panel:#182234;--border:#2b3648;--text:#f1f5f9;--muted:#94a3b8;--heading:#f1f5f9;--navy-tint:#7d93b3;--accent:#d97706;--accent-soft:#3a2a12}}
  }}
  :root[data-theme="dark"]{{--bg:#111827;--panel:#182234;--border:#2b3648;--text:#f1f5f9;--muted:#94a3b8;--heading:#f1f5f9;--navy-tint:#7d93b3;--accent:#d97706;--accent-soft:#3a2a12}}
  :root[data-theme="light"]{{--bg:#f6f8fb;--panel:#ffffff;--border:#e6eaf0;--text:#17202a;--muted:#64748b;--heading:#13263d;--navy-tint:#3a5578;--accent:#f6c453;--accent-soft:#fff5e6}}

  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:"Apple SD Gothic Neo","Pretendard","Noto Sans KR",-apple-system,system-ui,sans-serif;padding:28px;transition:background .2s,color .2s}}
  h1{{font-size:21px;font-weight:800;letter-spacing:-.2px;margin-bottom:4px;color:var(--heading)}}
  .sub{{color:var(--muted);font-size:13px;margin-bottom:18px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}}
  .grid-2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}
  .kpi{{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px}}
  .kpi-label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}}
  .kpi-value{{font-size:23px;font-weight:700;margin-top:4px;font-variant-numeric:tabular-nums}}
  .card{{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:16px}}
  .card h2{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:12px;font-weight:700}}
  .bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px}}
  .bar-label{{width:130px;flex-shrink:0;text-align:right;color:var(--text);display:flex;align-items:center;justify-content:flex-end;gap:6px}}
  .dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
  .bar-track{{flex:1;background:var(--bg);border:1px solid var(--border);border-radius:6px;height:14px;overflow:hidden}}
  .bar-fill{{height:100%;border-radius:6px}}
  .bar-value{{width:64px;flex-shrink:0;color:var(--muted);font-variant-numeric:tabular-nums}}
  .vbar-chart{{display:flex;align-items:flex-end;gap:4px;height:140px;padding-top:10px}}
  .vbar-col{{flex:1;display:flex;flex-direction:column;align-items:center;height:100%}}
  .vbar-track{{flex:1;width:100%;display:flex;align-items:flex-end;background:var(--bg);border:1px solid var(--border);border-radius:4px;overflow:hidden}}
  .vbar-fill{{width:100%;border-radius:4px 4px 0 0}}
  .vbar-label{{font-size:9px;color:var(--muted);margin-top:4px;white-space:nowrap}}
  .muted{{color:var(--muted);font-size:12px}}
  .ai-box{{font-size:12px;line-height:1.7;color:var(--text)}}
  .ai-box p{{margin-bottom:6px;padding-left:10px;border-left:2px solid var(--accent)}}
  .footer{{color:var(--muted);font-size:11px;margin-top:16px}}

  .tabs{{display:flex;gap:4px;margin-bottom:18px;border-bottom:1px solid var(--border)}}
  .tabs input{{display:none}}
  .tabs label{{padding:10px 18px;font-size:13px;font-weight:700;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent}}
  .tab-panel{{display:none}}
  #tab-1:checked ~ .tabs label[for="tab-1"],
  #tab-2:checked ~ .tabs label[for="tab-2"],
  #tab-3:checked ~ .tabs label[for="tab-3"]{{color:var(--text);border-bottom-color:var(--accent)}}
  #tab-1:checked ~ #panel-1,
  #tab-2:checked ~ #panel-2,
  #tab-3:checked ~ #panel-3{{display:block}}
</style>
</head>
<body>
  <h1>잇뉴 대시보드 요약</h1>
  <div class="sub">조회기간: {esc(period_label)} · 데이터 출처: {esc(source)}</div>

  <input type="radio" name="tab" id="tab-1" checked>
  <input type="radio" name="tab" id="tab-2">
  <input type="radio" name="tab" id="tab-3">
  <div class="tabs">
    <label for="tab-1">운영현황</label>
    <label for="tab-2">고객분석</label>
    <label for="tab-3">품목분류</label>
  </div>

  <div class="tab-panel" id="panel-1">{operations_html}</div>
  <div class="tab-panel" id="panel-2">{customer_html}</div>
  <div class="tab-panel" id="panel-3">{product_html}</div>

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
