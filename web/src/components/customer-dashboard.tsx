"use client";

import { useEffect, useMemo, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import { themeQuartz, type ColDef, type ICellEditorParams } from "ag-grid-community";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PieLabelRenderProps } from "recharts";
import { AlertTriangle, Check, Clock3, RefreshCw, Search, ShieldCheck, ShoppingBag, UserPlus, UserRoundCheck, Users } from "lucide-react";
import type { CustomerData } from "@/types/analytics";
import jejuGeoJson from "@/data/jeju-admdong.json";

const groups = ["전체", "신규 고객", "일반 고객", "재이용 고객", "이탈 위험 고객"];
const shortName: Record<string,string> = {"전체":"전체","신규 고객":"신규","일반 고객":"일반","재이용 고객":"재이용","이탈 위험 고객":"이탈 위험"};
const colors = ["var(--chart-accent)", "#13263D", "#F6C453", "#94A3B8", "#D97706"];
const gridTheme = themeQuartz.withParams({ accentColor: "#E98200", headerBackgroundColor: "#F7F9FB", headerTextColor: "#465568", oddRowBackgroundColor: "#FBFCFE", rowHoverColor: "#F7F8FA", selectedRowBackgroundColor: "#FFF0D6", wrapperBorderRadius: "14px", rowHeight: 46, headerHeight: 48 });
const number = (value: number) => new Intl.NumberFormat("ko-KR").format(value);
type GeoGeometry={type:"Polygon"|"MultiPolygon";coordinates:number[][][]|number[][][][]};
type JejuFeature={properties:{name:string};geometry:GeoGeometry};
const regionAliases:Record<string,string>={"일도일동":"일도1동","일도이동":"일도2동","이도일동":"이도1동","이도이동":"이도2동","삼도일동":"삼도1동","삼도이동":"삼도2동","용담일동":"용담1동","용담이동":"용담2동","화북일동":"화북동","화북이동":"화북동","삼양일동":"삼양동","삼양이동":"삼양동","아라일동":"아라동","아라이동":"아라동","오라일동":"오라동","오라이동":"오라동","오라삼동":"오라동","외도일동":"외도동","도두일동":"도두동","보목동":"송산동","서귀동":"중앙동","하효동":"효돈동","법환동":"대륜동","강정동":"대천동","월평동":"대천동","색달동":"예래동"};
const normalizeRegion=(name:string)=>regionAliases[name]??name;
const project=([lon,lat]:number[])=>[(lon-126.12)/(126.99-126.12)*740+10,(33.61-lat)/(33.61-33.20)*330+10];
const ringPath=(ring:number[][])=>ring.map((point,index)=>`${index?"L":"M"}${project(point).map((value)=>value.toFixed(1)).join(" ")}`).join(" ")+" Z";
const featurePath=(feature:JejuFeature)=>{const coordinates=feature.geometry.coordinates;if(feature.geometry.type==="Polygon")return (coordinates as number[][][]).map(ringPath).join(" ");return (coordinates as number[][][][]).flatMap((polygon)=>polygon.map(ringPath)).join(" ")};
const deltaText = (current:number,previous:number) => previous ? `${current >= previous ? "+" : ""}${((current-previous)/previous*100).toFixed(1)}%` : current ? "신규" : "변동 없음";
const isFullMonthRange = (from:string,to:string) => from.slice(0,7)===to.slice(0,7) && from.slice(8,10)==="01" && to.slice(8,10)===String(new Date(Number(from.slice(0,4)),Number(from.slice(5,7)),0).getDate()).padStart(2,"0");
function PiePercentLabel({cx,cy,midAngle,innerRadius,outerRadius,percent}:PieLabelRenderProps){
  const radius=Number(innerRadius)+(Number(outerRadius)-Number(innerRadius))*.58;
  const angle=-Number(midAngle)*Math.PI/180;
  const x=Number(cx)+radius*Math.cos(angle);
  const y=Number(cy)+radius*Math.sin(angle);
  return <text x={x} y={y} textAnchor="middle" dominantBaseline="central" fill="#fff" stroke="rgba(15,23,42,.72)" strokeWidth="2.5" paintOrder="stroke" fontSize="12" fontWeight="800">{`${(Number(percent)*100).toFixed(1)}%`}</text>;
}

export function TodayDashboard({range}:{range?:{from:string;to:string}}) {
  const [data,setData]=useState<CustomerData|null>(null);
  const [error,setError]=useState("");
  const [orderRows,setOrderRows]=useState<CustomerData["operations"]["orderList"]>([]);
  const [classificationSaving,setClassificationSaving]=useState(false);
  useEffect(()=>{const query=range?.from||range?.to?`?from=${encodeURIComponent(range.from)}&to=${encodeURIComponent(range.to)}`:"";void fetch(`/api/customers${query}`,{cache:"no-store"}).then(async(response)=>{const result=await response.json();if(!response.ok)throw new Error(result.error);setData(result)}).catch((reason)=>setError(reason instanceof Error?reason.message:"오늘 현황을 불러오지 못했습니다."))},[range?.from,range?.to]);
  useEffect(()=>{if(data)setOrderRows(data.operations.orderList)},[data]);
  if(error)return <ErrorBox message={error}/>;
  if(!data)return <Loading/>;
  const today=data.today;const operations=data.operations;
  const isFullMonth=isFullMonthRange(operations.from,operations.to);
  const showsSecondChart=operations.days!==1&&(isFullMonth||operations.days>7);
  const mainCategories=[...new Set(data.categoryOptions.map((row)=>row.main))];
  const saveCategory=async(row:(typeof operations.orderList)[number])=>{setClassificationSaving(true);const response=await fetch("/api/products/actions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"save_rules",itemNames:[row.sourceItemName],mainCategory:row.mainCategory,subcategory:row.subCategory})});if(!response.ok)setError((await response.json()).error??"품목분류 저장에 실패했습니다.");else setOrderRows((current)=>current.map((item)=>item.sourceItemName===row.sourceItemName?{...item,itemName:row.subCategory||row.mainCategory,mainCategory:row.mainCategory,subCategory:row.subCategory}:item));setClassificationSaving(false)};
  const orderColumns:ColDef<(typeof operations.orderList)[number]>[]=[{field:"orderTime",headerName:"접수시간",minWidth:170,sort:"desc"},{field:"channel",headerName:"접수형태",minWidth:140},{field:"itemName",headerName:"자동분류 품목",minWidth:170},{field:"sourceItemName",headerName:"고객 기입 품목",flex:1,minWidth:260,tooltipField:"sourceItemName"},{field:"quantity",headerName:"수량",width:80},{field:"mainCategory",headerName:"대분류 (수정)",minWidth:140,editable:true,cellEditor:"agSelectCellEditor",cellEditorParams:{values:mainCategories}},{field:"subCategory",headerName:"중분류 (수정)",minWidth:150,editable:true,cellEditor:"agSelectCellEditor",cellEditorParams:(params:ICellEditorParams<(typeof operations.orderList)[number]>)=>({values:data.categoryOptions.filter((row)=>row.main===params.data?.mainCategory).map((row)=>row.sub)})},{field:"orderId",headerName:"주문번호",minWidth:140}];
  return <>
    <PageHeading eyebrow="OPERATIONS" title="기간별 운영현황" description={`${operations.from} ~ ${operations.to} · ${operations.days}일 조회`}/>
    <div className="mb-6 grid gap-6 xl:grid-cols-[1.35fr_.65fr]">
      <div className="grid gap-4 sm:grid-cols-2">
        <TodayMetric icon={ShoppingBag} label="기간 주문 건수" value={`${number(operations.orders)}건`} change={deltaText(operations.orders,operations.previousOrders)} comparison={`직전 동일 기간 ${number(operations.previousOrders)}건 대비`}/>
        <TodayMetric icon={UserPlus} label="기간 신규 고객" value={`${number(operations.newCustomers)}명`} change={deltaText(operations.newCustomers,operations.previousNewCustomers)} comparison={`직전 동일 기간 ${number(operations.previousNewCustomers)}명 대비`}/>
      </div>
      <BusinessGoals data={data}/>
    </div>
    <div className={`mb-6 grid gap-6 ${showsSecondChart?"xl:grid-cols-2":""}`}>{operations.days===1?<OperationsBar title="시간대별 주문량" data={operations.hourlyOrders} dataKey="hour"/>:<OperationsBar title="요일별 주문량" data={operations.weekdayOrders} dataKey="name"/>}{operations.days!==1&&(isFullMonth?<OperationsBar title="시간대별 주문량" data={operations.hourlyOrders} dataKey="hour"/>:operations.days>7&&<OperationsBar title="월별 주문량" data={operations.monthlyOrders} dataKey="month"/>)}</div>
    <div className="card p-4"><div className="mb-4 flex items-start justify-between px-1"><div><h2 className="text-lg font-bold">기간 주문 목록 <span className="ml-2 text-sm font-normal text-slate-400">{number(orderRows.length)}건</span></h2><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">대분류·중분류 셀을 클릭하면 같은 품목의 분류 규칙을 수정할 수 있습니다.</p></div>{classificationSaving&&<span className="text-xs text-amber-600 dark:text-orange-300">분류 저장 중…</span>}</div><div className="h-[520px] ag-theme-itnew"><AgGridReact theme={gridTheme} rowData={orderRows} columnDefs={orderColumns} pagination paginationPageSize={50} onCellValueChanged={({data:row,colDef,api})=>{if(!row)return;if(colDef.field==="mainCategory"){row.subCategory=data.categoryOptions.find((option)=>option.main===row.mainCategory)?.sub??"기타";api.refreshCells({rowNodes:[api.getRowNode(row.orderId)!],columns:["subCategory"]})}void saveCategory(row)}} getRowId={({data:row})=>row.orderId}/></div></div>
  </>;
}

export function CustomerDashboard({range}:{range?:{from:string;to:string}}) {
  const [data, setData] = useState<CustomerData | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("전체");
  useEffect(() => {
    const query=range?.from||range?.to?`?from=${encodeURIComponent(range.from)}&to=${encodeURIComponent(range.to)}`:"";
    void fetch(`/api/customers${query}`, { cache: "no-store" }).then(async (response) => {
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setData(result);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "고객 데이터를 불러오지 못했습니다."));
  }, [range?.from,range?.to]);
  const columns = useMemo<ColDef<Record<string, string>>[]>(() => [
    { field: "customer_id", headerName: "고객 ID", minWidth: 130, pinned: "left" },
    { field: "고객군", headerName: "고객군", minWidth: 130 },
    { field: "주문 횟수", headerName: "주문 횟수", width: 110 },
    { field: "최근 주문일", headerName: "최근 주문일", width: 130 },
    { field: "평균 이용 주기", headerName: "평균 이용 주기", width: 140 },
    { field: "최종 주문 후 경과일", headerName: "경과일", width: 110 },
    { field: "이탈 위험 등급", headerName: "이탈 등급", width: 120 },
    { field: "누적 배송 수량", headerName: "누적 배송", width: 120 },
  ], []);
  if (error) return <ErrorBox message={error}/>;
  if (!data) return <Loading/>;

  const groupCount = new Map(data.groupSummary.map((row) => [row.name, row.count]));
  const filteredCustomers = selectedGroup === "전체" ? data.customers : data.customers.filter((row) => row["고객군"] === selectedGroup);
  const rawGroupProducts = selectedGroup === "전체" ? data.topProducts : data.topProducts.filter((row) => row.group === selectedGroup);
  const productTotals = new Map<string,{group:string;itemName:string;orders:number;quantity:number}>();
  for(const row of rawGroupProducts){const item=productTotals.get(row.itemName)??{...row,orders:0,quantity:0};item.orders+=row.orders;item.quantity+=row.quantity;productTotals.set(row.itemName,item)}
  const allGroupProducts = [...productTotals.values()];
  const productUnknown = allGroupProducts.find((row)=>row.itemName === "미상");
  const groupProducts = allGroupProducts.filter((row)=>row.itemName !== "미상").toSorted((a,b)=>b.orders-a.orders).slice(0, 12);
  const rawGroupRegions = selectedGroup === "전체" ? data.regions : data.regions.filter((row) => row.group === selectedGroup);
  const regionTotals = new Map<string,{group:string;name:string;customers:number;rate:number}>();
  for(const row of rawGroupRegions){const item=regionTotals.get(row.name)??{...row,customers:0,rate:0};item.customers+=row.customers;regionTotals.set(row.name,item)}
  const allGroupRegions = [...regionTotals.values()];
  const regionUnknown = allGroupRegions.find((row)=>row.name === "미상");
  const groupRegions = allGroupRegions.filter((row)=>row.name !== "미상").toSorted((a,b)=>b.customers-a.customers).slice(0,10);
  const rawChannels = data.channels.filter((row) => selectedGroup === "전체" || row.group === selectedGroup);
  const channelTotals = new Map<string,{group:string;name:string;orders:number;quantity:number}>();
  for(const row of rawChannels){const item=channelTotals.get(row.name)??{...row,orders:0,quantity:0};item.orders+=row.orders;item.quantity+=row.quantity;channelTotals.set(row.name,item)}
  const groupChannels = [...channelTotals.values()];
  const pickupRegions = data.pickupRegions.filter((row) => selectedGroup === "전체" || row.group === selectedGroup);
  const deliveryRegions = data.deliveryRegions.filter((row) => selectedGroup === "전체" || row.group === selectedGroup);
  const pickupGrids = data.pickupGrids.filter((row)=>selectedGroup==="전체"||row.group===selectedGroup);
  const deliveryGrids = data.deliveryGrids.filter((row)=>selectedGroup==="전체"||row.group===selectedGroup);
  const avgOrders = filteredCustomers.length ? filteredCustomers.reduce((sum,row)=>sum+(Number(row["주문 횟수"])||0),0)/filteredCustomers.length : 0;
  const avgQuantity = filteredCustomers.length ? filteredCustomers.reduce((sum,row)=>sum+(Number(row["누적 배송 수량"])||0),0)/filteredCustomers.length : 0;
  const riskCustomers = filteredCustomers.filter((row)=>["주의","위험"].includes(row["이탈 위험 등급"])).length;
  const riskRate = data.eligibleCustomers ? data.riskCustomers / data.eligibleCustomers * 100 : 0;

  return <>
    <PageHeading eyebrow="CUSTOMER ANALYTICS" title={selectedGroup === "전체" ? "고객분석" : `${selectedGroup} 상세 분석`} description={selectedGroup === "전체" ? "고객군, 이용 주기, 이탈 위험과 구매 특성을 한 화면에서 확인합니다." : `${selectedGroup}의 이용 지표와 구매 특성을 집중적으로 확인합니다.`}/>
    <div className="card mb-7 grid grid-cols-2 gap-2 p-2 md:grid-cols-5">
      {groups.map((group)=><button key={group} onClick={()=>{setSelectedGroup(group);setSearch("")}} className={`rounded-xl px-3 py-3 text-sm font-semibold transition ${selectedGroup===group?"bg-[#13263d] text-white shadow-md dark:bg-[#09182B] dark:ring-1 dark:ring-slate-600":"text-slate-500 hover:bg-orange-50 hover:text-orange-800 dark:text-slate-400 dark:hover:bg-[#0F1D30] dark:hover:text-orange-300"}`}><span>{shortName[group]}</span><span className={`ml-2 rounded-full px-2 py-0.5 text-xs ${selectedGroup===group?"bg-white/15":"bg-slate-100 dark:bg-slate-700"}`}>{group === "전체" ? data.totalCustomers : groupCount.get(group) ?? 0}</span></button>)}
    </div>

    {selectedGroup === "전체" ? <>
      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric icon={Users} label="전체 고객" value={`${number(data.totalCustomers)}명`} note="분석 대상 고객"/>
        <Metric icon={UserRoundCheck} label="재이용 고객" value={`${number(data.returningCustomers)}명`} note={`${(data.returningCustomers/data.totalCustomers*100).toFixed(1)}%`}/>
        <Metric icon={AlertTriangle} label="이탈 주의·위험" value={`${number(data.riskCustomers)}명`} note={`분석 대상의 ${riskRate.toFixed(1)}%`} warning/>
        <Metric icon={ShieldCheck} label="데이터 검증" value={`${data.validation.filter((row) => row.status === "통과").length}/${data.validation.length}`} note="검증 항목 통과"/>
      </div>
      <div className="mb-6 grid gap-6 xl:grid-cols-2">
        <ChartCard title="고객군 분포" description="신규·일반·재이용·이탈 위험 고객"><div className="customer-pie"><ResponsiveContainer width="100%" height={340}><PieChart margin={{top:24,right:32,bottom:12,left:32}}><Pie data={data.groupSummary} dataKey="count" nameKey="name" outerRadius={104} paddingAngle={2} stroke="#ffffff" strokeWidth={2} labelLine={false} label={PiePercentLabel}>{data.groupSummary.map((row,index)=><Cell key={row.name} fill={colors[index%colors.length]}/>)}</Pie><Tooltip formatter={(value)=>`${number(Number(value))}명`}/><Legend verticalAlign="top" align="center" formatter={(value)=>(shortName[String(value)]??String(value))}/></PieChart></ResponsiveContainer></div></ChartCard>
        <ChartCard title="이탈 위험 등급" description="평균 이용 주기 대비 경과일 기준"><ResponsiveContainer width="100%" height={340}><BarChart data={data.churnSummary}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E8E2D5"/><XAxis dataKey="name" axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip formatter={(value)=>`${number(Number(value))}명`}/><Bar dataKey="count" fill="var(--chart-accent)" radius={[8,8,0,0]}/></BarChart></ResponsiveContainer></ChartCard>
      </div>
    </> : <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Metric icon={Users} label={`${shortName[selectedGroup]} 고객`} value={`${number(filteredCustomers.length)}명`} note={`전체의 ${(filteredCustomers.length/data.totalCustomers*100).toFixed(1)}%`}/>
      <Metric icon={ShoppingBag} label="평균 주문 횟수" value={`${avgOrders.toFixed(1)}회`} note="고객 1인 기준"/>
      <Metric icon={UserRoundCheck} label="평균 배송 수량" value={`${avgQuantity.toFixed(1)}개`} note="고객 1인 누적"/>
      <Metric icon={AlertTriangle} label="주의·위험 고객" value={`${number(riskCustomers)}명`} note="현재 고객군 내" warning={riskCustomers>0}/>
    </div>}

    <div className="mb-6 grid gap-6 xl:grid-cols-[.55fr_1.45fr]">
      <ChartCard title={`${shortName[selectedGroup]} 접수 형태`} description="기업(B2B) · 개인(B2C) 주문 구성"><div className="customer-pie"><ResponsiveContainer width="100%" height={340}><PieChart margin={{top:24,right:32,bottom:12,left:32}}><Pie data={groupChannels} dataKey="orders" nameKey="name" outerRadius={100} paddingAngle={2} stroke="#ffffff" strokeWidth={2} labelLine={false} label={PiePercentLabel}>{groupChannels.map((row,index)=><Cell key={row.name} fill={index === 0 ? "var(--chart-accent)" : "var(--chart-accent-soft)"}/>)}</Pie><Tooltip formatter={(value)=>`${number(Number(value))}건`}/><Legend verticalAlign="top" align="center"/></PieChart></ResponsiveContainer></div></ChartCard>
      <div className="card p-5"><h2 className="text-lg font-bold">제주 상세주소 주문 밀집도</h2><p className="mb-4 mt-1 text-sm text-slate-500 dark:text-slate-400">GPS 변환 좌표 · 약 500m 격자 비교</p><div className="grid gap-5 2xl:grid-cols-2"><JejuRegionMap title="수거지" rows={pickupRegions} grids={pickupGrids}/><JejuRegionMap title="배송지" rows={deliveryRegions} grids={deliveryGrids}/></div></div>
    </div>

    <div className="mb-6 grid gap-6 xl:grid-cols-[1.15fr_.85fr]">
      <ChartCard title={`${shortName[selectedGroup]} 고객 상위 품목`} description="미상 제외 · 주문 건수 상위 12개"><ResponsiveContainer width="100%" height={330}><BarChart data={groupProducts} layout="vertical" margin={{left:30,right:20}}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F0DFCA"/><XAxis type="number" axisLine={false} tickLine={false}/><YAxis type="category" dataKey="itemName" width={120} tick={{fontSize:11}} axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="orders" fill="var(--chart-accent)" radius={[0,6,6,0]}/></BarChart></ResponsiveContainer>{productUnknown && <MissingDataNote label="품목 미상" value={productUnknown.orders} unit="건"/>}</ChartCard>
      <ChartCard title={`${shortName[selectedGroup]} 고객 지역 분포`} description="미상 제외 · 고객 수 상위 지역"><ResponsiveContainer width="100%" height={330}><BarChart data={groupRegions}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F0DFCA"/><XAxis dataKey="name" tick={{fontSize:11}} axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="customers" fill="var(--chart-accent)" radius={[7,7,0,0]}/></BarChart></ResponsiveContainer>{regionUnknown && <MissingDataNote label="지역 미상" value={regionUnknown.customers} unit="명"/>}</ChartCard>
    </div>
    <div className="card p-4"><div className="mb-4 flex flex-col justify-between gap-3 px-1 md:flex-row md:items-center"><div><h2 className="text-lg font-bold">{selectedGroup === "전체" ? "전체 고객별 이용 지표" : `${selectedGroup} 고객 목록`}</h2><p className="text-sm text-slate-500 dark:text-slate-400">정렬·필터로 상세 지표를 조회할 수 있습니다.</p></div><label className="relative"><Search className="absolute left-3 top-3 text-slate-400" size={16}/><input value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="고객 검색" className="h-10 rounded-xl border border-slate-200 bg-transparent pl-9 pr-4 text-sm outline-none focus:border-[#FA9C00] dark:border-slate-700"/></label></div><div className="h-[520px] ag-theme-itnew"><AgGridReact theme={gridTheme} rowData={filteredCustomers} columnDefs={columns} quickFilterText={search} pagination paginationPageSize={50}/></div></div>
  </>;
}

export function PageHeading({eyebrow,title,description}:{eyebrow:string;title:string;description:string}) { return <div className="mb-8"><p className="mb-2 text-sm font-semibold text-[#E98200]">{eyebrow}</p><h1 className="text-3xl font-bold tracking-tight">{title}</h1><p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{description}</p></div>; }
function Metric({icon:Icon,label,value,note}:{icon:typeof Users;label:string;value:string;note:string;warning?:boolean}) { return <div className="card p-5"><div className="flex items-center justify-between"><span className="text-sm text-slate-500 dark:text-slate-400">{label}</span><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E8EEF6] text-[#13263D] dark:bg-[#263A52] dark:text-[#DCE8F5]"><Icon size={17}/></span></div><div className="mt-3 text-3xl font-bold">{value}</div><div className="mt-2 text-xs text-slate-400">{note}</div></div>; }
function OperationsBar({title,data,dataKey}:{title:string;data:{orders:number;[key:string]:string|number}[];dataKey:string}){return <ChartCard title={title} description="선택 조회기간 주문 접수 기준"><ResponsiveContainer width="100%" height={360}><BarChart data={data}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E8E2D5"/><XAxis dataKey={dataKey} axisLine={false} tickLine={false} tick={{fontSize:11}}/><YAxis allowDecimals={false} axisLine={false} tickLine={false}/><Tooltip formatter={(value)=>`${number(Number(value))}건`}/><Bar dataKey="orders" name="주문 건수" fill="var(--chart-accent)" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></ChartCard>}
function TodayMetric({icon:Icon,label,value,change,comparison}:{icon:typeof Users;label:string;value:string;change:string;comparison:string}) { const positive=change.startsWith("+")||change==="신규"; return <div className="card p-6"><div className="flex items-center justify-between"><span className="text-sm text-slate-500 dark:text-slate-400">{label}</span><span className="grid h-10 w-10 place-items-center rounded-xl bg-amber-100 text-amber-700 dark:bg-[#0B1B30] dark:text-orange-300"><Icon size={19}/></span></div><div className="mt-5 text-4xl font-bold">{value}</div><div className="mt-3 text-xs text-slate-400"><b className={positive?"text-emerald-600 dark:text-emerald-400":"text-rose-500"}>{change}</b><span className="ml-2">{comparison}</span></div></div>; }
function BusinessGoals({data}:{data:CustomerData}) { const goals=[{label:"월 주문 3,000건",value:data.today.monthOrders,target:3000},{label:"신규 고객 200명",value:data.today.monthNewCustomers,target:200},{label:"MAU 100만",value:data.today.mau,target:1_000_000}]; const progress=Math.round(goals.reduce((sum,goal)=>sum+Math.min(goal.value/goal.target,1),0)/goals.length*100); return <div className="card p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-bold">기업 달성 목표</h2><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{data.today.date.slice(0,7)} KPI</p></div><Clock3 className="text-[var(--chart-accent)]" size={20}/></div><div className="mt-5 rounded-xl bg-amber-50 p-4 dark:bg-orange-950/35"><div className="mb-2.5 flex justify-between text-sm"><b>이번 달 종합 목표</b><strong className="text-amber-800 dark:text-orange-300">{progress}%</strong></div><div className="h-3.5 overflow-hidden rounded-full bg-amber-100 dark:bg-slate-700"><div className="h-full rounded-full bg-[#C96F00] dark:bg-[#F59E0B]" style={{width:`${progress}%`}}/></div></div><div className="mt-6 space-y-5">{goals.map((goal)=>{const goalProgress=Math.min(Math.round(goal.value/goal.target*100),100);const done=goalProgress>=100;return <div key={goal.label}><div className="mb-2 flex items-center gap-3"><span className={`grid h-5 w-5 place-items-center rounded border ${done?"border-amber-500 bg-amber-500 text-white":"border-slate-300 dark:border-slate-600"}`}>{done&&<Check size={13}/>}</span><span className="flex-1 text-sm font-medium">{goal.label}</span><span className="text-xs text-slate-400">{number(goal.value)} · {goalProgress}%</span></div><div className="ml-8 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700"><div className="h-full rounded-full bg-[var(--chart-accent)]" style={{width:`${goalProgress}%`}}/></div></div>})}</div></div>; }
function ChartCard({title,description,children}:{title:string;description:string;children:React.ReactNode}) { return <div className="card p-6"><h2 className="text-lg font-bold">{title}</h2><p className="mb-4 mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>{children}</div>; }
function MissingDataNote({label,value,unit}:{label:string;value:number;unit:string}) { return <div className="mt-3 flex items-center justify-between rounded-xl bg-slate-100 px-4 py-3 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-400"><span>{label} · 분석 그래프에서 제외</span><b>{number(value)}{unit}</b></div>; }
function JejuRegionMap({title,rows,grids}:{title:string;rows:{name:string;orders:number}[];grids:{lon:number;lat:number;orders:number}[]}) {
  const unknown=rows.filter((row)=>row.name==="미상").reduce((sum,row)=>sum+row.orders,0);
  const features=(jejuGeoJson.features as unknown as JejuFeature[]).filter((feature)=>feature.properties.name!=="추자면");
  const regionTotals=new Map<string,number>();
  for(const row of rows){
    if(row.name==="미상") continue;
    const region=normalizeRegion(row.name);
    regionTotals.set(region,(regionTotals.get(region)??0)+row.orders);
  }
  const regionMax=Math.max(...regionTotals.values(),1);
  const cells=new Map<string,{lon:number;lat:number;orders:number}>();
  for(const grid of grids){
    const key=`${grid.lon.toFixed(4)}:${grid.lat.toFixed(4)}`;
    const cell=cells.get(key)??{lon:grid.lon,lat:grid.lat,orders:0};
    cell.orders+=grid.orders;
    cells.set(key,cell);
  }
  const mapped=[...cells.values()];
  const max=Math.max(...mapped.map(cell=>cell.orders),1);
  const total=rows.reduce((sum,row)=>sum+row.orders,0);
  const mappedOrders=mapped.reduce((sum,row)=>sum+row.orders,0);
  const coverage=total?mappedOrders/total*100:0;
  return <div className="rounded-2xl border border-slate-100 p-4 dark:border-slate-700">
    <h3 className="text-sm font-bold">{title}</h3>
    <p className="mb-2 mt-1 text-[11px] text-slate-500 dark:text-slate-400">행정구역 주문 농도 + 상세주소 기반 약 500m 격자 · 좌표 변환 {coverage.toFixed(1)}%</p>
    <svg viewBox="0 0 760 350" className="h-auto w-full" role="img" aria-label={title}>
      {features.map((feature)=>{
        const orders=regionTotals.get(feature.properties.name)??0;
        const opacity=orders===0?1:.06+Math.pow(orders/regionMax,1.25)*.42;
        return <path key={feature.properties.name} d={featurePath(feature)} fill={orders>0?"var(--chart-accent)":"var(--map-land)"} fillOpacity={opacity} stroke="var(--map-line)" strokeWidth=".75" fillRule="evenodd"><title>{feature.properties.name} · 행정구역 합계 {number(orders)}건</title></path>;
      })}
      {mapped.map((cell,index)=>{const [x,y]=project([cell.lon,cell.lat]);return <rect key={index} x={x-2.5} y={y-2} width="5" height="4" rx=".55" fill="var(--chart-accent)" fillOpacity={Math.max(.68,cell.orders/max)} stroke="var(--map-grid-line)" strokeWidth=".8"><title>{number(cell.orders)}건 · 약 500m 격자</title></rect>})}
    </svg>
    <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400"><span>반투명 행정구역 농도 + 선명한 GPS 주문 격자 · 경계: 통계청 SGIS</span><span className="flex items-center gap-2"><span>낮음</span><span className="h-2 w-16 rounded-full bg-gradient-to-r from-amber-100/40 to-amber-600/60 dark:from-orange-950/40 dark:to-orange-500/60"/><span>높음</span></span></div>
    {unknown>0&&<MissingDataNote label="기존 행정동 추출 미상" value={unknown} unit="건"/>}
  </div>;
}
function Loading(){return <div className="grid min-h-[60vh] place-items-center"><RefreshCw className="animate-spin text-[#FA9C00]"/></div>}
function ErrorBox({message}:{message:string}){return <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">{message}</div>}
