"use client";

import { useEffect, useMemo, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import { themeQuartz, type ColDef } from "ag-grid-community";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, RefreshCw, Search, ShieldCheck, ShoppingBag, UserRoundCheck, Users } from "lucide-react";
import type { CustomerData } from "@/types/analytics";

const groups = ["전체", "신규 고객", "일반 고객", "재이용 고객", "이탈 위험 고객"];
const shortName: Record<string,string> = {"전체":"전체","신규 고객":"신규","일반 고객":"일반","재이용 고객":"재이용","이탈 위험 고객":"이탈 위험"};
const colors = ["var(--chart-accent)", "#13263D", "#4F7CFF", "#94A3B8", "#D97706"];
const gridTheme = themeQuartz.withParams({ accentColor: "#E98200", headerBackgroundColor: "#F7F9FB", headerTextColor: "#465568", oddRowBackgroundColor: "#FBFCFE", rowHoverColor: "#F7F8FA", selectedRowBackgroundColor: "#FFF0D6", wrapperBorderRadius: "14px", rowHeight: 46, headerHeight: 48 });
const number = (value: number) => new Intl.NumberFormat("ko-KR").format(value);

export function CustomerDashboard() {
  const [data, setData] = useState<CustomerData | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("전체");
  useEffect(() => {
    void fetch("/api/customers", { cache: "no-store" }).then(async (response) => {
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setData(result);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "고객 데이터를 불러오지 못했습니다."));
  }, []);
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
  const groupProducts = (selectedGroup === "전체" ? data.topProducts : data.topProducts.filter((row) => row.group === selectedGroup)).slice(0, 12);
  const groupRegions = (selectedGroup === "전체" ? data.regions : data.regions.filter((row) => row.group === selectedGroup)).sort((a,b)=>b.customers-a.customers).slice(0,10);
  const avgOrders = filteredCustomers.length ? filteredCustomers.reduce((sum,row)=>sum+(Number(row["주문 횟수"])||0),0)/filteredCustomers.length : 0;
  const avgQuantity = filteredCustomers.length ? filteredCustomers.reduce((sum,row)=>sum+(Number(row["누적 배송 수량"])||0),0)/filteredCustomers.length : 0;
  const riskCustomers = filteredCustomers.filter((row)=>["주의","위험"].includes(row["이탈 위험 등급"])).length;
  const riskRate = data.eligibleCustomers ? data.riskCustomers / data.eligibleCustomers * 100 : 0;

  return <>
    <PageHeading eyebrow="CUSTOMER ANALYTICS" title={selectedGroup === "전체" ? "고객분석" : `${selectedGroup} 상세 분석`} description={selectedGroup === "전체" ? "고객군, 이용 주기, 이탈 위험과 구매 특성을 한 화면에서 확인합니다." : `${selectedGroup}의 이용 지표와 구매 특성을 집중적으로 확인합니다.`}/>
    <div className="card mb-7 grid grid-cols-2 gap-2 p-2 md:grid-cols-5">
      {groups.map((group)=><button key={group} onClick={()=>{setSelectedGroup(group);setSearch("")}} className={`rounded-xl px-3 py-3 text-sm font-semibold transition ${selectedGroup===group?"bg-[#13263d] text-white shadow-md dark:bg-[#E98200]":"text-slate-500 hover:bg-orange-50 hover:text-orange-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-orange-300"}`}><span>{shortName[group]}</span><span className={`ml-2 rounded-full px-2 py-0.5 text-xs ${selectedGroup===group?"bg-white/15":"bg-slate-100 dark:bg-slate-700"}`}>{group === "전체" ? data.totalCustomers : groupCount.get(group) ?? 0}</span></button>)}
    </div>

    {selectedGroup === "전체" ? <>
      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric icon={Users} label="전체 고객" value={`${number(data.totalCustomers)}명`} note="분석 대상 고객"/>
        <Metric icon={UserRoundCheck} label="재이용 고객" value={`${number(data.returningCustomers)}명`} note={`${(data.returningCustomers/data.totalCustomers*100).toFixed(1)}%`}/>
        <Metric icon={AlertTriangle} label="이탈 주의·위험" value={`${number(data.riskCustomers)}명`} note={`분석 대상의 ${riskRate.toFixed(1)}%`} warning/>
        <Metric icon={ShieldCheck} label="데이터 검증" value={`${data.validation.filter((row) => row.status === "통과").length}/${data.validation.length}`} note="검증 항목 통과"/>
      </div>
      <div className="mb-6 grid gap-6 xl:grid-cols-2">
        <ChartCard title="고객군 분포" description="고객별 최종 분류 결과"><div className="customer-pie"><ResponsiveContainer width="100%" height={340}><PieChart margin={{top:20,right:48,bottom:10,left:48}}><Pie data={data.groupSummary} dataKey="count" nameKey="name" outerRadius={104} paddingAngle={2} stroke="#ffffff" strokeWidth={2} labelLine label={({name,percent})=>(shortName[String(name)] ?? String(name)) + " " + ((percent ?? 0)*100).toFixed(0) + "%"}>{data.groupSummary.map((row,index)=><Cell key={row.name} fill={colors[index%colors.length]}/>)}</Pie><Tooltip formatter={(value)=>`${number(Number(value))}명`}/><Legend/></PieChart></ResponsiveContainer></div></ChartCard>
        <ChartCard title="이탈 위험 등급" description="평균 이용 주기 대비 경과일 기준"><ResponsiveContainer width="100%" height={310}><BarChart data={data.churnSummary}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E8E2D5"/><XAxis dataKey="name" axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip formatter={(value)=>`${number(Number(value))}명`}/><Bar dataKey="count" fill="var(--chart-accent)" radius={[8,8,0,0]}/></BarChart></ResponsiveContainer></ChartCard>
      </div>
    </> : <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Metric icon={Users} label={`${shortName[selectedGroup]} 고객`} value={`${number(filteredCustomers.length)}명`} note={`전체의 ${(filteredCustomers.length/data.totalCustomers*100).toFixed(1)}%`}/>
      <Metric icon={ShoppingBag} label="평균 주문 횟수" value={`${avgOrders.toFixed(1)}회`} note="고객 1인 기준"/>
      <Metric icon={UserRoundCheck} label="평균 배송 수량" value={`${avgQuantity.toFixed(1)}개`} note="고객 1인 누적"/>
      <Metric icon={AlertTriangle} label="주의·위험 고객" value={`${number(riskCustomers)}명`} note="현재 고객군 내" warning={riskCustomers>0}/>
    </div>}

    <div className="mb-6 grid gap-6 xl:grid-cols-[1.15fr_.85fr]">
      <ChartCard title={`${shortName[selectedGroup]} 고객 상위 품목`} description="주문 건수 상위 12개"><ResponsiveContainer width="100%" height={360}><BarChart data={groupProducts} layout="vertical" margin={{left:30,right:20}}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F0DFCA"/><XAxis type="number" axisLine={false} tickLine={false}/><YAxis type="category" dataKey="itemName" width={120} tick={{fontSize:11}} axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="orders" fill="var(--chart-accent)" radius={[0,6,6,0]}/></BarChart></ResponsiveContainer></ChartCard>
      {selectedGroup === "전체" ? <div className="card p-6"><h2 className="text-lg font-bold">데이터 검증</h2><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">파이프라인 정합성 검사 결과</p><div className="mt-5 space-y-3">{data.validation.map((row)=><div key={row.item} className="flex items-start gap-3 rounded-xl border border-slate-100 p-3 dark:border-slate-700"><span className={`mt-1 h-2.5 w-2.5 rounded-full ${row.status === "통과" ? "bg-orange-400" : "bg-amber-400"}`}/><div><div className="text-sm font-semibold">{row.item}</div><div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{row.detail}</div></div></div>)}</div></div> : <ChartCard title={`${shortName[selectedGroup]} 고객 지역 분포`} description="고객 수 상위 지역"><ResponsiveContainer width="100%" height={360}><BarChart data={groupRegions}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F0DFCA"/><XAxis dataKey="name" tick={{fontSize:11}} axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="customers" fill="#4f7cff" radius={[7,7,0,0]}/></BarChart></ResponsiveContainer></ChartCard>}
    </div>
    <div className="card p-4"><div className="mb-4 flex flex-col justify-between gap-3 px-1 md:flex-row md:items-center"><div><h2 className="text-lg font-bold">{selectedGroup === "전체" ? "전체 고객별 이용 지표" : `${selectedGroup} 고객 목록`}</h2><p className="text-sm text-slate-500 dark:text-slate-400">정렬·필터로 상세 지표를 조회할 수 있습니다.</p></div><label className="relative"><Search className="absolute left-3 top-3 text-slate-400" size={16}/><input value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="고객 검색" className="h-10 rounded-xl border border-slate-200 bg-transparent pl-9 pr-4 text-sm outline-none focus:border-[#FA9C00] dark:border-slate-700"/></label></div><div className="h-[520px] ag-theme-itnew"><AgGridReact theme={gridTheme} rowData={filteredCustomers} columnDefs={columns} quickFilterText={search} pagination paginationPageSize={50}/></div></div>
  </>;
}

export function PageHeading({eyebrow,title,description}:{eyebrow:string;title:string;description:string}) { return <div className="mb-8"><p className="mb-2 text-sm font-semibold text-[#E98200]">{eyebrow}</p><h1 className="text-3xl font-bold tracking-tight">{title}</h1><p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{description}</p></div>; }
function Metric({icon:Icon,label,value,note}:{icon:typeof Users;label:string;value:string;note:string;warning?:boolean}) { return <div className="card p-5"><div className="flex items-center justify-between"><span className="text-sm text-slate-500 dark:text-slate-400">{label}</span><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E8EEF6] text-[#13263D] dark:bg-[#263A52] dark:text-[#DCE8F5]"><Icon size={17}/></span></div><div className="mt-3 text-3xl font-bold">{value}</div><div className="mt-2 text-xs text-slate-400">{note}</div></div>; }
function ChartCard({title,description,children}:{title:string;description:string;children:React.ReactNode}) { return <div className="card p-6"><h2 className="text-lg font-bold">{title}</h2><p className="mb-4 mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>{children}</div>; }
function Loading(){return <div className="grid min-h-[60vh] place-items-center"><RefreshCw className="animate-spin text-[#FA9C00]"/></div>}
function ErrorBox({message}:{message:string}){return <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">{message}</div>}
