import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { parse } from "csv-parse/sync";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ProductRow = {
  order_id: string;
  item_name: string;
  order_date: string;
  대분류: string;
  중분류: string;
};

const classificationPath = path.resolve(
  process.cwd(),
  "..",
  "data",
  "output",
  "product_classification.csv",
);

export async function GET() {
  try {
    const content = await readFile(classificationPath, "utf-8");
    const rows = parse(content, { columns: true, bom: true, skip_empty_lines: true }) as ProductRow[];
    const categories = new Map<string, number>();
    const details = new Map<string, { main: string; sub: string; count: number; unique: Set<string> }>();
    const review = new Map<string, { itemName: string; orderCount: number; lastOrderDate: string }>();

    for (const row of rows) {
      const main = row.대분류 || "기타";
      const sub = row.중분류 || "기타";
      categories.set(main, (categories.get(main) ?? 0) + 1);
      const detailKey = `${main}\u0000${sub}`;
      const detail = details.get(detailKey) ?? { main, sub, count: 0, unique: new Set<string>() };
      detail.count += 1;
      detail.unique.add(row.item_name);
      details.set(detailKey, detail);
      if (main === "기타") {
        const current = review.get(row.item_name) ?? {
          itemName: row.item_name,
          orderCount: 0,
          lastOrderDate: "",
        };
        current.orderCount += 1;
        if (row.order_date > current.lastOrderDate) current.lastOrderDate = row.order_date;
        review.set(row.item_name, current);
      }
    }

    const reviewCount = rows.filter((row) => row.대분류 === "기타").length;
    const fileStat = await stat(classificationPath);
    return NextResponse.json({
      total: rows.length,
      uniqueItems: new Set(rows.map((row) => row.item_name)).size,
      classified: rows.length - reviewCount,
      reviewCount,
      updatedAt: fileStat.mtime.toISOString(),
      categories: [...categories].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count),
      categoryDetails: [...details.values()].map(({ main, sub, count, unique }) => ({
        main,
        sub,
        count,
        uniqueItems: unique.size,
      })).sort((a, b) => b.count - a.count),
      reviewItems: [...review.values()].sort((a, b) => b.orderCount - a.orderCount),
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "분류 결과를 불러오지 못했습니다." },
      { status: 500 },
    );
  }
}
