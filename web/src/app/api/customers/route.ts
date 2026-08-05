import { readFile } from "node:fs/promises";
import path from "node:path";
import { parse } from "csv-parse/sync";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const outputDirectory = path.resolve(process.cwd(), "..", "data", "output");

async function csv<T>(name: string): Promise<T[]> {
  const content = await readFile(path.join(outputDirectory, name), "utf-8");
  return parse(content, { columns: true, bom: true, skip_empty_lines: true }) as T[];
}

export async function GET(request: NextRequest) {
  try {
    const [groups, metrics, churn, regions, industries, products, validation, orders, deliveries, coordinates, classifications, members] = await Promise.all([
      csv<Record<string, string>>("customer_groups.csv"),
      csv<Record<string, string>>("customer_metrics.csv"),
      csv<Record<string, string>>("churn_scores.csv"),
      csv<Record<string, string>>("region_analysis.csv"),
      csv<Record<string, string>>("industry_analysis.csv"),
      csv<Record<string, string>>("product_analysis.csv"),
      csv<Record<string, string>>("validation_results.csv"),
      csv<Record<string, string>>(path.join("..", "input", "orders.csv")),
      csv<Record<string, string>>(path.join("..", "input", "deliveries.csv")),
      csv<Record<string, string>>("order_coordinates.csv").catch(()=>[]),
      csv<Record<string, string>>("product_classification.csv").catch(()=>[]),
      csv<Record<string, string>>(path.join("..", "input", "members.csv")),
    ]);
    const from = request.nextUrl.searchParams.get("from") || "";
    const to = request.nextUrl.searchParams.get("to") || "";
    const analysisOrders = orders.filter((row) => (!from || row.order_date.slice(0,10) >= from) && (!to || row.order_date.slice(0,10) <= to));
    const activeCustomerIds = new Set(analysisOrders.map((row)=>row.customer_id));
    const countBy = (rows: Record<string, string>[], key: string) => {
      const result = new Map<string, number>();
      for (const row of rows) result.set(row[key] || "미상", (result.get(row[key] || "미상") ?? 0) + 1);
      return [...result].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
    };
    const eligible = churn.filter((row) => row["이탈 분석 대상 여부"] === "예");
    const risk = eligible.filter((row) => ["주의", "위험"].includes(row["이탈 위험 등급"]));
    const deliveryByOrder = new Map(deliveries.map((row) => [row.order_id, row]));
    const coordinatesByOrder = new Map(coordinates.map((row)=>[row.order_id,row]));
    const classificationByOrder = new Map(classifications.map((row)=>[row.order_id,row]));
    const classifiedItemName=(orderId:string)=>{const category=classificationByOrder.get(orderId);const sub=category?.["중분류"]?.trim();const main=category?.["대분류"]?.trim();return sub&&sub!=="기타"?sub:main&&main!=="기타"?main:"미상"};
    const orderListRow=(row:Record<string,string>)=>{const category=classificationByOrder.get(row.order_id);return {orderId:row.order_id,orderTime:row.order_date,channel:row.order_channel||"미상",itemName:classifiedItemName(row.order_id),sourceItemName:row.item_name||"미상",quantity:Number(row.order_quantity)||0,mainCategory:category?.["대분류"]||"기타",subCategory:category?.["중분류"]||"기타"}};
    const channelMap = new Map<string, { group: string; name: string; orders: number; quantity: number }>();
    const pickupMap = new Map<string, { group: string; name: string; orders: number }>();
    const destinationMap = new Map<string, { group: string; name: string; orders: number }>();
    const productMap = new Map<string, { group: string; itemName: string; orders: number; quantity: number }>();
    const pickupGridMap = new Map<string,{group:string;lon:number;lat:number;orders:number}>();
    const deliveryGridMap = new Map<string,{group:string;lon:number;lat:number;orders:number}>();
    const firstOrderByCustomer = new Map<string, string>();
    for (const order of orders) {
      const orderDate = order.order_date?.slice(0, 10) || "";
      const firstOrder = firstOrderByCustomer.get(order.customer_id);
      if (orderDate && (!firstOrder || orderDate < firstOrder)) firstOrderByCustomer.set(order.customer_id, orderDate);
    }
    // 고객군(신규/일반/재이용/이탈 위험)은 조회기간(from~to)에 맞춰 매 요청마다 재계산한다.
    // 신규=조회기간 내 첫 주문, 일반/재이용=조회기간 내 주문 1회/2회 이상(신규·이탈위험 제외), 이탈 위험=평균 주문주기 대비 최근 주문 지연(파이프라인의 전역 판정을 그대로 사용).
    const memberIds = new Set(members.map((row) => row.customer_id));
    const groupRowByCustomer = new Map(groups.map((row) => [row.customer_id, row]));
    const periodOrderCountByCustomer = new Map<string, number>();
    for (const order of analysisOrders) periodOrderCountByCustomer.set(order.customer_id, (periodOrderCountByCustomer.get(order.customer_id) ?? 0) + 1);
    const classifyFrom = from || orders.reduce((value, row) => !value || row.order_date.slice(0,10) < value ? row.order_date.slice(0,10) : value, "");
    const classifyTo = to || orders.reduce((value, row) => row.order_date.slice(0,10) > value ? row.order_date.slice(0,10) : value, "");
    const atRiskCustomerIds = new Set(groups.filter((row) => ["주의","위험"].includes(row["이탈 위험 등급"])).map((row) => row.customer_id));
    const analysisCustomerIds = [...new Set([...activeCustomerIds, ...atRiskCustomerIds])].filter((id) => memberIds.has(id));
    const analysisGroups = analysisCustomerIds.map((id) => {
      const base = groupRowByCustomer.get(id);
      const firstOrder = firstOrderByCustomer.get(id) ?? "";
      const isNew = !!firstOrder && firstOrder >= classifyFrom && firstOrder <= classifyTo;
      const churnGrade = base?.["이탈 위험 등급"] ?? "판정 보류";
      const periodOrders = periodOrderCountByCustomer.get(id) ?? 0;
      const group = isNew ? "신규 고객" : ["주의","위험"].includes(churnGrade) ? "이탈 위험 고객" : periodOrders >= 2 ? "재이용 고객" : "일반 고객";
      return { ...base, customer_id: id, "고객군": group };
    });
    const groupByCustomer = new Map(analysisGroups.map((row) => [row.customer_id, row["고객군"]]));
    const metricsById = new Map(metrics.map((row) => [row.customer_id, row]));
    const customers = analysisGroups.map((row) => ({ ...metricsById.get(row.customer_id), ...row }));
    for (const order of analysisOrders) {
      const group = groupByCustomer.get(order.customer_id);
      if (!group) continue;
      const channelName = order.order_channel?.toUpperCase().startsWith("B2B") ? "B2B" : order.order_channel?.toUpperCase().startsWith("B2C") ? "B2C" : "기타";
      const channelKey = `${group}\u0000${channelName}`;
      const channel = channelMap.get(channelKey) ?? { group, name: channelName, orders: 0, quantity: 0 };
      channel.orders += 1;
      channel.quantity += Number(order.order_quantity) || 0;
      channelMap.set(channelKey, channel);
      const itemName=classifiedItemName(order.order_id);
      const productKey = `${group}\u0000${itemName}`;
      const product = productMap.get(productKey) ?? { group, itemName, orders: 0, quantity: 0 };
      product.orders += 1;
      product.quantity += Number(order.order_quantity) || 0;
      productMap.set(productKey, product);
      const delivery = deliveryByOrder.get(order.order_id);
      for (const [map, name] of [[pickupMap, delivery?.origin_region || "미상"], [destinationMap, delivery?.destination_region || "미상"]] as const) {
        const key = `${group}\u0000${name}`;
        const item = map.get(key) ?? { group, name, orders: 0 };
        item.orders += 1;
        map.set(key, item);
      }
      const coordinate=coordinatesByOrder.get(order.order_id);
      for(const [map,lonValue,latValue] of [[pickupGridMap,coordinate?.origin_lon,coordinate?.origin_lat],[deliveryGridMap,coordinate?.destination_lon,coordinate?.destination_lat]] as const){const lon=Number(lonValue),lat=Number(latValue);if(!Number.isFinite(lon)||!Number.isFinite(lat))continue;const gridLon=Math.round(lon/.0054)*.0054;const gridLat=Math.round(lat/.0045)*.0045;const key=`${group}\u0000${gridLon.toFixed(4)}\u0000${gridLat.toFixed(4)}`;const cell=map.get(key)??{group,lon:gridLon,lat:gridLat,orders:0};cell.orders+=1;map.set(key,cell)}
    }
    const latestDate = (from || to ? analysisOrders : orders).reduce((latest, row) => row.order_date?.slice(0, 10) > latest ? row.order_date.slice(0, 10) : latest, "");
    const previousDate = latestDate ? new Date(`${latestDate}T00:00:00`) : new Date();
    previousDate.setDate(previousDate.getDate() - 1);
    const previousDateText = [previousDate.getFullYear(), String(previousDate.getMonth()+1).padStart(2,"0"), String(previousDate.getDate()).padStart(2,"0")].join("-");
    const month = latestDate.slice(0, 7);
    const todayOrders = latestDate ? orders.filter((row) => row.order_date?.startsWith(latestDate)) : [];
    const previousOrders = orders.filter((row) => row.order_date?.startsWith(previousDateText));
    const monthOrders = month ? orders.filter((row) => row.order_date?.startsWith(month)) : [];
    const hourlyOrders = Array.from({length:24},(_,hour)=>({hour:`${String(hour).padStart(2,"0")}시`,orders:0}));
    for (const order of todayOrders) { const hour=Number(order.order_date?.slice(11,13)); if(Number.isInteger(hour) && hourlyOrders[hour]) hourlyOrders[hour].orders += 1; }
    const newCustomers = latestDate ? [...firstOrderByCustomer.values()].filter((date)=>date===latestDate).length : 0;
    const previousNewCustomers = [...firstOrderByCustomer.values()].filter((date)=>date===previousDateText).length;
    const operationFrom=from||analysisOrders.reduce((value,row)=>!value||row.order_date.slice(0,10)<value?row.order_date.slice(0,10):value,"");
    const operationTo=to||analysisOrders.reduce((value,row)=>row.order_date.slice(0,10)>value?row.order_date.slice(0,10):value,"");
    const operationStart=operationFrom?new Date(`${operationFrom}T00:00:00`):new Date();const operationEnd=operationTo?new Date(`${operationTo}T00:00:00`):operationStart;
    const operationDays=Math.max(1,Math.round((operationEnd.getTime()-operationStart.getTime())/86400000)+1);
    const priorEnd=new Date(operationStart);priorEnd.setDate(priorEnd.getDate()-1);const priorStart=new Date(priorEnd);priorStart.setDate(priorStart.getDate()-operationDays+1);
    const dateString=(value:Date)=>[value.getFullYear(),String(value.getMonth()+1).padStart(2,"0"),String(value.getDate()).padStart(2,"0")].join("-");
    const priorFrom=dateString(priorStart),priorTo=dateString(priorEnd);
    const priorPeriodOrders=orders.filter((row)=>row.order_date.slice(0,10)>=priorFrom&&row.order_date.slice(0,10)<=priorTo);
    const operationHourly=Array.from({length:24},(_,hour)=>({hour:`${String(hour).padStart(2,"0")}시`,orders:0}));
    const weekdays=["일","월","화","수","목","금","토"].map((name)=>({name:`${name}요일`,orders:0}));
    const operationMonths=new Map<string,number>();
    for(const order of analysisOrders){const hour=Number(order.order_date.slice(11,13));if(operationHourly[hour])operationHourly[hour].orders+=1;const day=new Date(`${order.order_date.slice(0,10)}T00:00:00`).getDay();weekdays[day].orders+=1;const key=order.order_date.slice(0,7);operationMonths.set(key,(operationMonths.get(key)??0)+1)}
    return NextResponse.json({
      totalCustomers: customers.length,
      groupSummary: countBy(analysisGroups, "고객군"),
      churnSummary: countBy(from || to ? churn.filter((row)=>activeCustomerIds.has(row.customer_id)) : churn, "이탈 위험 등급"),
      eligibleCustomers: eligible.length,
      riskCustomers: risk.length,
      returningCustomers: analysisGroups.filter((row) => row["고객군"] === "재이용 고객").length,
      customers,
      regions: regions.map((row) => ({ group: row["고객군"], name: row.region, customers: Number(row["고객 수"]), rate: Number(row["비율"]) })),
      pickupRegions: [...pickupMap.values()],
      deliveryRegions: [...destinationMap.values()],
      pickupGrids: [...pickupGridMap.values()],
      deliveryGrids: [...deliveryGridMap.values()],
      channels: [...channelMap.values()],
      industries: industries.map((row) => ({ group: row["고객군"], name: row.industry, customers: Number(row["고객 수"]), orders: Number(row["주문_건수"]), quantity: Number(row["배송_수량"]) })),
      topProducts: [...productMap.values()].sort((a,b)=>b.orders-a.orders),
      validation: validation.map((row) => ({ item: row["항목"], status: row["상태"], detail: row["내용"] })),
      categoryOptions:[...new Map(classifications.map((row)=>[`${row["대분류"]}\u0000${row["중분류"]}`,{main:row["대분류"],sub:row["중분류"]}])).values()].filter((row)=>row.main&&row.sub),
      today: {
        date: latestDate,
        orders: todayOrders.length,
        previousOrders: previousOrders.length,
        newCustomers,
        previousNewCustomers,
        hourlyOrders,
        monthOrders: monthOrders.length,
        monthNewCustomers: month ? [...firstOrderByCustomer.values()].filter((date)=>date.startsWith(month)).length : 0,
        mau: new Set(monthOrders.map((row)=>row.customer_id)).size,
        orderList: todayOrders.map(orderListRow).sort((a,b)=>b.orderTime.localeCompare(a.orderTime)),
      },
      operations:{from:operationFrom,to:operationTo,days:operationDays,orders:analysisOrders.length,previousOrders:priorPeriodOrders.length,newCustomers:[...firstOrderByCustomer.values()].filter((date)=>date>=operationFrom&&date<=operationTo).length,previousNewCustomers:[...firstOrderByCustomer.values()].filter((date)=>date>=priorFrom&&date<=priorTo).length,hourlyOrders:operationHourly,weekdayOrders:[...weekdays.slice(1),weekdays[0]],monthlyOrders:[...operationMonths].map(([month,orders])=>({month,orders})).sort((a,b)=>a.month.localeCompare(b.month)),orderList:analysisOrders.map(orderListRow).sort((a,b)=>b.orderTime.localeCompare(a.orderTime))},
    });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "고객분석 데이터를 불러오지 못했습니다." }, { status: 500 });
  }
}
