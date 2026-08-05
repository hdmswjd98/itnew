import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { parse } from "csv-parse/sync";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ProductRow = {
  order_id: string;
  item_name: string;
  order_date: string;
  대분류: string;
  중분류: string;
};

type OrderRow = { order_id:string; order_quantity:string };
type DeliveryRow = { order_id:string; destination_region:string };

function classifiedItemName(row: ProductRow) {
  const sub = row.중분류?.trim();
  const main = row.대분류?.trim();
  return sub && sub !== "기타" ? sub : main && main !== "기타" ? main : "미상";
}

const classificationPath = path.resolve(
  process.cwd(),
  "..",
  "data",
  "output",
  "product_classification.csv",
);

export async function GET(request: NextRequest) {
  try {
    const [content,ordersContent,deliveriesContent] = await Promise.all([readFile(classificationPath, "utf-8"),readFile(path.resolve(process.cwd(),"..","data","input","orders.csv"),"utf-8"),readFile(path.resolve(process.cwd(),"..","data","input","deliveries.csv"),"utf-8")]);
    const allRows = parse(content, { columns: true, bom: true, skip_empty_lines: true }) as ProductRow[];
    const from=request.nextUrl.searchParams.get("from")||"";
    const to=request.nextUrl.searchParams.get("to")||"";
    const rows=allRows.filter((row)=>(!from||row.order_date.slice(0,10)>=from)&&(!to||row.order_date.slice(0,10)<=to));
    const previousFrom=from?new Date(`${from}T00:00:00`):null; const previousTo=to?new Date(`${to}T00:00:00`):null;
    if(previousFrom&&previousTo){const isFullMonth=previousFrom.getDate()===1&&previousTo.getDate()===new Date(previousTo.getFullYear(),previousTo.getMonth()+1,0).getDate();if(isFullMonth){previousFrom.setMonth(previousFrom.getMonth()-1);previousTo.setDate(0)}else{const days=Math.round((previousTo.getTime()-previousFrom.getTime())/86400000)+1;previousFrom.setDate(previousFrom.getDate()-days);previousTo.setDate(previousTo.getDate()-days)}}
    const dateText=(date:Date|null)=>date?[date.getFullYear(),String(date.getMonth()+1).padStart(2,"0"),String(date.getDate()).padStart(2,"0")].join("-"):"";
    const priorRows=from&&to?allRows.filter((row)=>row.order_date.slice(0,10)>=dateText(previousFrom)&&row.order_date.slice(0,10)<=dateText(previousTo)):[];
    const orderRows=parse(ordersContent,{columns:true,bom:true,skip_empty_lines:true}) as OrderRow[];
    const deliveryRows=parse(deliveriesContent,{columns:true,bom:true,skip_empty_lines:true}) as DeliveryRow[];
    const quantityByOrder=new Map(orderRows.map((row)=>[row.order_id,Number(row.order_quantity)||0]));
    const regionByOrder=new Map(deliveryRows.map((row)=>[row.order_id,row.destination_region||"미상"]));
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
    const previousCounts=new Map<string,number>(); for(const row of priorRows){const name=classifiedItemName(row);previousCounts.set(name,(previousCounts.get(name)??0)+1)}
    const productMap=new Map<string,{name:string;orders:number;quantity:number;rate:number;previousOrders:number;change:number|null;items:Set<string>}>();
    const regionProducts=new Map<string,number>();
    for(const row of rows){const name=classifiedItemName(row);const item=productMap.get(name)??{name,orders:0,quantity:0,rate:0,previousOrders:previousCounts.get(name)??0,change:null,items:new Set<string>()};item.orders+=1;item.quantity+=quantityByOrder.get(row.order_id)??0;item.items.add(row.item_name);productMap.set(name,item);const region=regionByOrder.get(row.order_id)??"미상";if(region!=="미상")regionProducts.set(`${region}\u0000${name}`,(regionProducts.get(`${region}\u0000${name}`)??0)+1)}
    const productAnalytics=[...productMap.values()].map((item)=>({...item,items:[...item.items].sort((a,b)=>a.localeCompare(b,"ko")),rate:rows.length?item.orders/rows.length*100:0,change:item.previousOrders?(item.orders-item.previousOrders)/item.previousOrders*100:null})).sort((a,b)=>b.orders-a.orders);
    const growing=productAnalytics.filter((item)=>item.previousOrders>0&&item.change!==null).sort((a,b)=>(b.change??0)-(a.change??0))[0];
    const top=productAnalytics[0]; const topRegion=[...regionProducts].filter(([key])=>top&&key.endsWith(`\u0000${top.name}`)).sort((a,b)=>b[1]-a[1])[0];
    const aiReport=[top?`이번 조회기간 주문 비중이 가장 높은 품목은 ${top.name}으로 전체의 ${top.rate.toFixed(1)}%입니다.`:"조회기간 품목 데이터가 없습니다.",growing?`${growing.name} 주문은 직전 동일 기간 대비 ${growing.change!>=0?"증가":"감소"}(${Math.abs(growing.change!).toFixed(1)}%)했습니다.`:"직전 기간과 비교할 수 있는 품목 데이터가 부족합니다.",topRegion?`${topRegion[0].split("\u0000")[0]}에서 ${top?.name} 주문이 ${topRegion[1]}건으로 가장 많았습니다.`:"배송 지역이 확인된 품목 데이터가 부족합니다."];
    const fileStat = await stat(classificationPath);
    return NextResponse.json({
      total: rows.length,
      uniqueItems: new Set(rows.map(classifiedItemName)).size,
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
      productAnalytics,
      aiReport,
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "분류 결과를 불러오지 못했습니다." },
      { status: 500 },
    );
  }
}
