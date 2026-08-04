import { readFile } from "node:fs/promises";
import path from "node:path";
import { parse } from "csv-parse/sync";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const outputDirectory = path.resolve(process.cwd(), "..", "data", "output");

async function csv<T>(name: string): Promise<T[]> {
  const content = await readFile(path.join(outputDirectory, name), "utf-8");
  return parse(content, { columns: true, bom: true, skip_empty_lines: true }) as T[];
}

export async function GET() {
  try {
    const [groups, metrics, churn, regions, industries, products, validation] = await Promise.all([
      csv<Record<string, string>>("customer_groups.csv"),
      csv<Record<string, string>>("customer_metrics.csv"),
      csv<Record<string, string>>("churn_scores.csv"),
      csv<Record<string, string>>("region_analysis.csv"),
      csv<Record<string, string>>("industry_analysis.csv"),
      csv<Record<string, string>>("product_analysis.csv"),
      csv<Record<string, string>>("validation_results.csv"),
    ]);
    const metricsById = new Map(metrics.map((row) => [row.customer_id, row]));
    const customers = groups.map((row) => ({ ...metricsById.get(row.customer_id), ...row }));
    const countBy = (rows: Record<string, string>[], key: string) => {
      const result = new Map<string, number>();
      for (const row of rows) result.set(row[key] || "미상", (result.get(row[key] || "미상") ?? 0) + 1);
      return [...result].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
    };
    const eligible = churn.filter((row) => row["이탈 분석 대상 여부"] === "예");
    const risk = eligible.filter((row) => ["주의", "위험"].includes(row["이탈 위험 등급"]));
    return NextResponse.json({
      totalCustomers: customers.length,
      groupSummary: countBy(groups, "고객군"),
      churnSummary: countBy(churn, "이탈 위험 등급"),
      eligibleCustomers: eligible.length,
      riskCustomers: risk.length,
      returningCustomers: groups.filter((row) => row["고객군"] === "재이용 고객").length,
      customers,
      regions: regions.map((row) => ({ group: row["고객군"], name: row.region, customers: Number(row["고객 수"]), rate: Number(row["비율"]) })),
      industries: industries.map((row) => ({ group: row["고객군"], name: row.industry, customers: Number(row["고객 수"]), orders: Number(row["주문_건수"]), quantity: Number(row["배송_수량"]) })),
      topProducts: products.map((row) => ({ group: row["고객군"], itemName: row.item_name, orders: Number(row["주문_건수"]), quantity: Number(row["배송_수량"]) })).sort((a, b) => b.orders - a.orders).slice(0, 30),
      validation: validation.map((row) => ({ item: row["항목"], status: row["상태"], detail: row["내용"] })),
    });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "고객분석 데이터를 불러오지 못했습니다." }, { status: 500 });
  }
}
