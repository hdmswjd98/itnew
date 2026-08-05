"use client";

import {
  Boxes,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Home,
  Moon,
  RefreshCw,
  Search,
  Sparkles,
  Sun,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AgGridReact } from "ag-grid-react";
import { themeQuartz, type ColDef, type GridApi } from "ag-grid-community";
import type { ProductDashboardData, ReviewItem } from "@/types/products";
import { CustomerDashboard, TodayDashboard } from "@/components/customer-dashboard";
import { MonthlyDashboard } from "@/components/monthly-dashboard";

type View = "home" | "customer" | "monthly" | "product";
type ProductView = "analysis" | "status" | "review" | "rules";
type DateRange = { from: string; to: string };
const shiftDate=(date:string,days:number)=>{const value=new Date(`${date}T00:00:00`);value.setDate(value.getDate()+days);return [value.getFullYear(),String(value.getMonth()+1).padStart(2,"0"),String(value.getDate()).padStart(2,"0")].join("-")};
const monthRange=(month:string):DateRange=>{const [year,value]=month.split("-").map(Number);const last=new Date(year,value,0).getDate();return {from:`${month}-01`,to:`${month}-${String(last).padStart(2,"0")}`}};
const shiftMonth=(month:string,delta:number)=>{const [year,value]=month.split("-").map(Number);const date=new Date(year,value-1+delta,1);return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}`};
const weekRangeFromDate=(date:string):DateRange=>{const day=(new Date(`${date}T00:00:00`).getDay()+6)%7;const monday=shiftDate(date,-day);return {from:monday,to:shiftDate(monday,6)}};

const navigation = [
  { key: "home" as View, label: "운영현황", icon: Home },
  { key: "customer" as View, label: "고객분석", icon: Users },
  { key: "monthly" as View, label: "월간리포트", icon: CalendarDays },
  { key: "product" as View, label: "품목 자동분류", icon: Boxes },
];

const gridTheme = themeQuartz.withParams({
  accentColor: "#FA9C00",
  borderColor: "#e6eaf0",
  headerBackgroundColor: "#f7f9fb",
  rowHoverColor: "#f0faf7",
  selectedRowBackgroundColor: "#e4f7f2",
  wrapperBorderRadius: "12px",
});

function number(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value);
}

export function DashboardShell() {
  const [view, setView] = useState<View>("home");
  const [productView, setProductView] = useState<ProductView>("analysis");
  const [data, setData] = useState<ProductDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [refreshingAll, setRefreshingAll] = useState(false);
  const [globalRange,setGlobalRange]=useState<DateRange>({from:"",to:""});
  const [rangeDraft,setRangeDraft]=useState<DateRange>({from:"",to:""});
  const [tabRanges,setTabRanges]=useState<Partial<Record<View,DateRange>>>({});
  const [monthPickerOpen,setMonthPickerOpen]=useState(false);
  const [monthPickerYear,setMonthPickerYear]=useState(new Date().getFullYear());
  const [monthlyMonth,setMonthlyMonth]=useState("");
  const effectiveRange=tabRanges[view]??globalRange;
  const monthlyRange=monthlyMonth?monthRange(monthlyMonth):undefined;

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const query=effectiveRange.from||effectiveRange.to?`?from=${encodeURIComponent(effectiveRange.from)}&to=${encodeURIComponent(effectiveRange.to)}`:"";
      const response = await fetch(`/api/products${query}`, { cache: "no-store" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setData(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "데이터를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [effectiveRange.from,effectiveRange.to]);

  useEffect(()=>{void fetch("/api/customers",{cache:"no-store"}).then((response)=>response.json()).then((result)=>{if(!globalRange.to&&result.today?.date){const initial={from:`${result.today.date.slice(0,7)}-01`,to:result.today.date};setGlobalRange(initial);setRangeDraft(initial);setMonthlyMonth(result.today.date.slice(0,7))}}).catch(()=>undefined)},[globalRange.to]);

  useEffect(() => {
    void Promise.resolve().then(loadData);
  }, [loadData]);

  useEffect(() => {
    void Promise.resolve().then(() => {
      const saved = localStorage.getItem("itnew-theme");
      const nextTheme = saved === "dark" ? "dark" : "light";
      document.documentElement.classList.toggle("dark", nextTheme === "dark");
      setTheme(nextTheme);
    });
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("itnew-theme", nextTheme);
    document.documentElement.classList.toggle("dark", nextTheme === "dark");
  };

  const refreshAll = async () => {
    setRefreshingAll(true);
    setError("");
    try {
      const response = await fetch("/api/refresh", { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      await loadData();
      window.location.reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "전체 데이터 새로고침에 실패했습니다.");
      setRefreshingAll(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f6f8fb] text-[#17202a] transition-colors dark:bg-[#111827] dark:text-slate-100 lg:flex">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col bg-[#13263d] px-5 py-7 text-white lg:flex">
        <div className="mb-10 flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#FA9C00] font-bold">잇</div>
          <div><div className="text-lg font-bold">잇뉴</div><div className="text-xs text-slate-400">통합 분석 플랫폼</div></div>
        </div>
        <nav className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = view === item.key;
            return (
              <button key={item.key} onClick={() => setView(item.key)} className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm transition ${active ? "bg-white/12 font-semibold text-white" : "text-slate-300 hover:bg-white/7 hover:text-white"}`}>
                <Icon size={18} /><span>{item.label}</span>{active && <ChevronRight className="ml-auto" size={16} />}
              </button>
            );
          })}
        </nav>
        <div className="mt-auto rounded-2xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-slate-300">
          <div className="mb-1 font-semibold text-white">시스템 상태</div>
          <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-orange-400" />Python 분석 서비스 연결</div>
        </div>
      </aside>

      <main className="min-w-0 flex-1 lg:ml-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-[#e6eaf0] bg-white/90 px-6 backdrop-blur transition-colors dark:border-slate-700 dark:bg-slate-900/90 lg:px-10">
          <div className="text-sm text-slate-500 dark:text-slate-400">잇뉴 <span className="mx-2">/</span> <b className="text-[#17202a] dark:text-slate-100">{navigation.find((item) => item.key === view)?.label}</b></div>
          <div className="flex items-center gap-3"><div className="hidden text-xs text-slate-500 dark:text-slate-400 xl:block">{data ? `마지막 갱신 ${new Date(data.updatedAt).toLocaleString("ko-KR")}` : "데이터 확인 중"}</div><button onClick={refreshAll} disabled={refreshingAll} className="flex h-9 items-center gap-2 rounded-xl border border-amber-300 bg-amber-50 px-3 text-xs font-semibold text-amber-800 transition hover:bg-amber-100 disabled:opacity-60 dark:border-slate-600 dark:bg-[#0F1D30] dark:text-orange-300"><RefreshCw size={14} className={refreshingAll?"animate-spin":""}/><span className="hidden sm:inline">{refreshingAll?"임포트·분류 중":"데이터 새로고침"}</span></button><button onClick={toggleTheme} aria-label="테마 전환" className="grid h-9 w-9 place-items-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:border-[#FA9C00] dark:border-slate-700 dark:bg-[#0F1D30] dark:text-slate-200">{theme === "light" ? <Moon size={17}/> : <Sun size={17}/>}</button></div>
        </header>
        {view==="monthly"?(
          <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-6 py-3 text-xs dark:border-slate-700 dark:bg-slate-900 lg:px-10">
            <b>조회 월</b>
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 px-1.5 py-1 dark:border-slate-700">
              <button onClick={()=>setMonthlyMonth((current)=>shiftMonth(current||new Date().toISOString().slice(0,7),-1))} className="rounded-lg p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="이전 달"><ChevronLeft size={16}/></button>
              <b className="min-w-[64px] text-center">{monthlyMonth.replace("-",".")}</b>
              <button onClick={()=>setMonthlyMonth((current)=>shiftMonth(current||new Date().toISOString().slice(0,7),1))} className="rounded-lg p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="다음 달"><ChevronRight size={16}/></button>
            </div>
            <input type="month" value={monthlyMonth} onChange={(event)=>event.target.value&&setMonthlyMonth(event.target.value)} className="rounded-lg border border-slate-200 bg-transparent px-2 py-1.5 dark:border-slate-700" aria-label="조회 연월 직접 선택"/>
            <span className="ml-auto text-slate-400">공통 조회기간과 무관하게 월 단위로 조회합니다</span>
          </div>
        ):(
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-6 py-3 text-xs dark:border-slate-700 dark:bg-slate-900 lg:px-10">
          <b>공통 조회기간</b>
          <label className="relative cursor-pointer rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-700"><span>하루</span><input type="date" value={rangeDraft.from===rangeDraft.to?rangeDraft.to:""} onChange={(event)=>event.target.value&&setRangeDraft({from:event.target.value,to:event.target.value})} className="absolute inset-0 h-full w-full cursor-pointer opacity-0" aria-label="하루 조회 날짜 선택"/></label>
          <label className="relative cursor-pointer rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-700"><span>1주</span><input type="date" onChange={(event)=>event.target.value&&setRangeDraft(weekRangeFromDate(event.target.value))} className="absolute inset-0 h-full w-full cursor-pointer opacity-0" aria-label="주에 포함된 날짜 하나 선택"/></label>
          <div className="relative"><button onClick={()=>{setMonthPickerYear(Number((rangeDraft.to||rangeDraft.from).slice(0,4))||new Date().getFullYear());setMonthPickerOpen((open)=>!open)}} className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-2 dark:border-slate-700" aria-label="조회 연도와 월 선택"><CalendarDays size={14} className="text-slate-400"/><span className="text-slate-500 dark:text-slate-400">월</span><b>{(rangeDraft.to||rangeDraft.from).slice(0,7).replace("-",".")}</b></button>{monthPickerOpen&&<div className="absolute left-0 top-full z-50 mt-2 w-60 rounded-xl border border-slate-200 bg-white p-3 shadow-xl dark:border-slate-600 dark:bg-[#101C2E]"><div className="mb-3 flex items-center justify-between"><button onClick={()=>setMonthPickerYear((year)=>year-1)} className="rounded-lg p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"><ChevronLeft size={16}/></button><b>{monthPickerYear}년</b><button onClick={()=>setMonthPickerYear((year)=>year+1)} className="rounded-lg p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"><ChevronRight size={16}/></button></div><div className="grid grid-cols-3 gap-1">{Array.from({length:12},(_,index)=>{const month=String(index+1).padStart(2,"0");const value=`${monthPickerYear}-${month}`;const active=(rangeDraft.to||rangeDraft.from).slice(0,7)===value;return <button key={value} onClick={()=>{setRangeDraft(monthRange(value));setMonthPickerOpen(false)}} className={`rounded-lg py-2 text-xs font-semibold ${active?"bg-[#13263d] text-white dark:bg-[#D97706]":"hover:bg-amber-50 dark:hover:bg-slate-800"}`}>{index+1}월</button>})}</div></div>}</div>
          <input type="date" value={rangeDraft.from} onChange={(event)=>setRangeDraft({...rangeDraft,from:event.target.value})} className="rounded-lg border border-slate-200 bg-transparent px-2 py-1.5 dark:border-slate-700"/><span>~</span><input type="date" value={rangeDraft.to} onChange={(event)=>setRangeDraft({...rangeDraft,to:event.target.value})} className="rounded-lg border border-slate-200 bg-transparent px-2 py-1.5 dark:border-slate-700"/><button onClick={()=>{setGlobalRange({...rangeDraft});setTabRanges({})}} disabled={!rangeDraft.from||!rangeDraft.to} className="rounded-lg bg-[#13263d] px-4 py-2 font-semibold text-white disabled:opacity-40 dark:bg-[#0A192C] dark:ring-1 dark:ring-slate-600">조회</button>
          <span className="ml-auto text-slate-400">{tabRanges[view]?"현재 탭만 별도 기간 적용 중":"모든 탭에 공통 적용 중"}</span>
          {tabRanges[view]?<button onClick={()=>setTabRanges((current)=>{const next={...current};delete next[view];return next})} className="rounded-lg bg-slate-100 px-3 py-2 dark:bg-[#0F1D30]">공통 기간으로 복귀</button>:<button onClick={()=>setTabRanges((current)=>({...current,[view]:{...globalRange}}))} className="rounded-lg bg-amber-100 px-3 py-2 text-amber-800 dark:bg-[#0F1D30] dark:text-orange-300">이 탭만 기간 변경</button>}
          {tabRanges[view]&&<><input type="date" value={effectiveRange.from} onChange={(event)=>setTabRanges((current)=>({...current,[view]:{...effectiveRange,from:event.target.value}}))} className="rounded-lg border border-amber-300 bg-transparent px-2 py-1.5"/><span>~</span><input type="date" value={effectiveRange.to} onChange={(event)=>setTabRanges((current)=>({...current,[view]:{...effectiveRange,to:event.target.value}}))} className="rounded-lg border border-amber-300 bg-transparent px-2 py-1.5"/></>}
        </div>
        )}
        <div className="p-6 lg:p-10">
          {error && <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
          {loading && !data ? <Loading /> : view === "home" ? <TodayDashboard range={effectiveRange} /> : view === "product" ? <ProductDashboard data={data} productView={productView} setProductView={setProductView} reload={loadData} /> : view === "customer" ? <CustomerDashboard range={effectiveRange} /> : <MonthlyDashboard range={monthlyRange} />}
        </div>
      </main>
    </div>
  );
}

function Loading() {
  return <div className="grid min-h-[60vh] place-items-center"><RefreshCw className="animate-spin text-[#FA9C00]" /></div>;
}

function HomeDashboard({ data, onNavigate }: { data: ProductDashboardData | null; onNavigate: (view: View) => void }) {
  if (!data) return null;
  const rate = data.total ? (data.classified / data.total) * 100 : 0;
  return <>
    <div className="mb-8"><p className="mb-2 text-sm font-semibold text-[#E98200]">OVERVIEW</p><h1 className="text-3xl font-bold tracking-tight text-[#17202a] dark:text-slate-100">오늘의 데이터 현황</h1><p className="mt-2 text-sm text-slate-500 dark:text-slate-400">고객과 품목 분석 상태를 한눈에 확인하세요.</p></div>
    <div className="mb-7 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Kpi label="전체 주문 품목" value={`${number(data.total)}건`} note="등록된 주문 기준" />
      <Kpi label="고유 품목명" value={`${number(data.uniqueItems)}개`} note="중복 품목 제외" />
      <Kpi label="자동분류율" value={`${rate.toFixed(1)}%`} note={`${number(data.classified)}건 분류 완료`} tone="mint" />
      <button onClick={() => onNavigate("product")} className="card p-5 text-left transition hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-lg"><div className="text-sm text-slate-500">검토 필요</div><div className="mt-3 flex items-end justify-between"><strong className="text-3xl text-amber-600">{number(data.reviewCount)}건</strong><ChevronRight className="text-amber-500" /></div><div className="mt-3 text-xs text-slate-400">클릭하여 품목 검토</div></button>
    </div>
    <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
      <CategoryChart data={data} />
      <div className="card p-6"><h2 className="text-lg font-bold">분석 바로가기</h2><p className="mt-1 text-sm text-slate-500">자주 사용하는 업무로 이동합니다.</p><div className="mt-5 space-y-3">{navigation.slice(1).map((item) => <button key={item.key} onClick={() => onNavigate(item.key)} className="flex w-full items-center rounded-xl border border-[#edf0f4] p-4 text-left text-sm font-semibold transition hover:border-[#FA9C00] hover:bg-[#FFF8EB]"><item.icon className="mr-3 text-[#E98200]" size={18}/>{item.label}<ChevronRight className="ml-auto text-slate-400" size={16}/></button>)}</div></div>
    </div>
  </>;
}

function Kpi({ label, value, note, tone }: { label: string; value: string; note: string; tone?: "mint" }) {
  return <div className={`card p-5 ${tone === "mint" ? "border-orange-100 bg-orange-50/30 dark:border-orange-500/40 dark:bg-orange-500/10" : ""}`}><div className="text-sm text-slate-500 dark:text-slate-400">{label}</div><div className={`mt-3 text-3xl font-bold ${tone === "mint" ? "dark:text-[#FFB23F]" : ""}`}>{value}</div><div className="mt-3 text-xs text-slate-400">{note}</div></div>;
}

function CategoryChart({ data }: { data: ProductDashboardData }) {
  return <div className="card p-6"><div className="mb-5"><h2 className="text-lg font-bold">대분류별 품목 현황</h2><p className="mt-1 text-sm text-slate-500">주문 건수를 기준으로 집계했습니다.</p></div><div className="h-[360px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.categories.slice(0, 10)} layout="vertical" margin={{ left: 15, right: 30 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#edf0f4"/><XAxis type="number" tick={{fontSize: 11}} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="name" width={80} tick={{fontSize: 12}} axisLine={false} tickLine={false}/><Tooltip formatter={(value) => `${number(Number(value))}건`}/><Bar dataKey="count" fill="var(--chart-accent)" radius={[0, 6, 6, 0]} barSize={18}/></BarChart></ResponsiveContainer></div></div>;
}

function ProductDashboard({ data, productView, setProductView, reload }: { data: ProductDashboardData | null; productView: ProductView; setProductView: (view: ProductView) => void; reload: () => Promise<void> }) {
  const [refreshing, setRefreshing] = useState(false);
  if (!data) return null;
  const refresh = async () => { setRefreshing(true); await fetch("/api/products/actions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "refresh" }) }); await reload(); setRefreshing(false); };
  return <>
    <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="mb-2 text-sm font-semibold text-[#E98200]">PRODUCT ANALYTICS</p><h1 className="text-3xl font-bold">품목 자동분류</h1><p className="mt-2 text-sm text-slate-500">자동분류 현황을 확인하고 검토 품목을 일괄 수정합니다.</p></div><button onClick={refresh} disabled={refreshing} className="flex items-center justify-center gap-2 rounded-xl bg-[#13263d] px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"><RefreshCw size={16} className={refreshing ? "animate-spin" : ""}/>{refreshing ? "분류 중" : "데이터 새로고침"}</button></div>
    <div className="mb-6 grid gap-4 md:grid-cols-4"><Kpi label="전체 주문 품목" value={`${number(data.total)}건`} note="전체 행 기준"/><Kpi label="고유 품목" value={`${number(data.uniqueItems)}개`} note="중복 제외"/><Kpi label="자동분류" value={`${number(data.classified)}건`} note={`${((data.classified/data.total)*100).toFixed(1)}% 완료`} tone="mint"/><Kpi label="검토 필요" value={`${number(data.reviewCount)}건`} note={`${data.reviewItems.length}개 고유 품목`}/></div>
    <div className="mb-6 flex gap-2 border-b border-[#e6eaf0]">{(["analysis","status","review","rules"] as ProductView[]).map((tab) => <button key={tab} onClick={() => setProductView(tab)} className={`border-b-2 px-5 py-3 text-sm font-semibold ${productView === tab ? "border-[#FA9C00] text-[#C96F00]" : "border-transparent text-slate-500"}`}>{tab === "analysis"?"품목 분석":tab === "status" ? "자동분류" : tab === "review" ? `분류 검토 ${number(data.reviewCount)}` : "기업 규칙"}</button>)}</div>
    {productView === "analysis"?<ProductAnalysis data={data}/>:productView === "status" ? <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]"><CategoryChart data={data}/><div className="card overflow-hidden"><div className="border-b border-[#edf0f4] p-5"><h2 className="font-bold">카테고리 상세</h2></div><div className="max-h-[410px] overflow-auto"><table className="w-full text-sm"><thead className="sticky top-0 bg-[#f7f9fb] text-left text-xs text-slate-500"><tr><th className="p-3">대분류</th><th className="p-3">중분류</th><th className="p-3 text-right">건수</th></tr></thead><tbody>{data.categoryDetails.map((row) => <tr key={`${row.main}-${row.sub}`} className="border-t border-[#f0f2f5]"><td className="p-3 font-medium">{row.main}</td><td className="p-3 text-slate-500">{row.sub}</td><td className="p-3 text-right">{number(row.count)}</td></tr>)}</tbody></table></div></div></div> : productView === "review" ? <ReviewGrid data={data} reload={reload}/> : <div className="card p-8"><h2 className="text-lg font-bold">기업 우선 분류 규칙</h2><p className="mt-2 text-sm text-slate-500">수기 분류로 등록한 규칙을 조회·수정하는 화면을 연결하고 있습니다.</p></div>}
  </>;
}

function ProductAnalysis({data}:{data:ProductDashboardData}){
  const rows=data.productAnalytics.filter((row)=>row.name!=="미상").slice(0,12);
  const [selected,setSelected]=useState<string|null>(null);
  const selectedRow=rows.find((row)=>row.name===selected);
  return <div className="space-y-6"><div className="grid gap-6 xl:grid-cols-[1.25fr_.75fr]"><div className="card p-6"><h2 className="text-lg font-bold">품목별 주문건수·비율</h2><p className="mb-5 mt-1 text-sm text-slate-500 dark:text-slate-400">미상 제외 · 주문 상위 12개</p><ResponsiveContainer width="100%" height={390}><BarChart data={rows} layout="vertical" margin={{left:25,right:25}}><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" axisLine={false} tickLine={false}/><YAxis type="category" dataKey="name" width={115} tick={{fontSize:11}} axisLine={false} tickLine={false}/><Tooltip formatter={(value,name)=>name==="rate"?`${Number(value).toFixed(1)}%`:`${number(Number(value))}건`}/><Bar dataKey="orders" name="주문건수" fill="var(--chart-accent)" radius={[0,6,6,0]}/></BarChart></ResponsiveContainer></div><div className="card overflow-hidden"><div className="border-b border-slate-100 p-5 dark:border-slate-700"><h2 className="font-bold">품목 비율 상세</h2><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">행을 클릭하면 이 분류로 묶인 원본 품목명을 확인할 수 있습니다.</p></div><div className="max-h-[450px] overflow-auto"><table className="w-full text-sm"><thead className="sticky top-0 bg-slate-50 text-xs text-slate-500 dark:bg-[#0F1D30]"><tr><th className="p-3 text-left">품목</th><th className="p-3 text-right">주문</th><th className="p-3 text-right">비율</th></tr></thead><tbody>{rows.map((row)=><tr key={row.name} onClick={()=>setSelected((current)=>current===row.name?null:row.name)} className={`cursor-pointer border-t border-slate-100 transition dark:border-slate-700 ${selected===row.name?"bg-amber-50 dark:bg-[#17233A]":"hover:bg-slate-50 dark:hover:bg-[#111D30]"}`}><td className="p-3">{row.name}</td><td className="p-3 text-right">{number(row.orders)}건</td><td className="p-3 text-right font-semibold text-amber-700 dark:text-orange-300">{row.rate.toFixed(1)}%</td></tr>)}</tbody></table></div>{selectedRow&&<div className="border-t border-slate-100 bg-slate-50 p-4 dark:border-slate-700 dark:bg-[#0B1B30]"><div className="mb-2 flex items-center justify-between"><b className="text-sm">{selectedRow.name} 구성 원본 품목명 <span className="font-normal text-slate-400">({selectedRow.items.length}개)</span></b><button onClick={()=>setSelected(null)} className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">닫기</button></div><div className="flex max-h-40 flex-wrap gap-1.5 overflow-auto">{selectedRow.items.map((itemName)=><span key={itemName} className="rounded-full bg-white px-2.5 py-1 text-xs dark:bg-[#101C2E]">{itemName}</span>)}</div></div>}</div></div><div className="card border-amber-200 p-6 dark:border-slate-600"><div className="flex items-center gap-2"><Sparkles className="text-amber-600 dark:text-orange-300" size={20}/><h2 className="text-lg font-bold">AI 품목 리포트</h2></div><div className="mt-5 grid gap-3">{data.aiReport.map((line,index)=><div key={index} className="rounded-xl bg-amber-50 p-4 text-sm leading-6 dark:bg-[#0B1B30]">{line}</div>)}</div></div></div>;
}

function ReviewGrid({ data, reload }: { data: ProductDashboardData; reload: () => Promise<void> }) {
  const api = useRef<GridApi<ReviewItem> | null>(null);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<ReviewItem[]>([]);
  const [main, setMain] = useState("");
  const [sub, setSub] = useState("");
  const [saving, setSaving] = useState(false);
  const categoryMap = useMemo(() => { const map = new Map<string, Set<string>>(); for (const row of data.categoryDetails) { if (row.main === "기타") continue; if (!map.has(row.main)) map.set(row.main, new Set()); map.get(row.main)?.add(row.sub); } return map; }, [data]);
  const columns = useMemo<ColDef<ReviewItem>[]>(() => [{ field: "itemName", headerName: "품목명", flex: 1, minWidth: 260 }, { field: "orderCount", headerName: "주문 건수", width: 120, valueFormatter: ({value}) => `${number(value)}건` }, { field: "lastOrderDate", headerName: "최근 주문일", width: 140 }], []);
  const save = async () => { if (!selected.length || !main || !sub) return; setSaving(true); const response = await fetch("/api/products/actions", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ action: "save_rules", itemNames: selected.map((row) => row.itemName), mainCategory: main, subcategory: sub }) }); if (response.ok) { setSelected([]); await reload(); } setSaving(false); };
  return <div className="space-y-5"><div className="card p-5"><div className="flex flex-col gap-3 lg:flex-row"><label className="relative flex-1"><Search className="absolute left-3 top-3 text-slate-400" size={17}/><input value={search} onChange={(event) => { setSearch(event.target.value); api.current?.setGridOption("quickFilterText", event.target.value); }} placeholder="품목명 검색" className="h-11 w-full rounded-xl border border-[#dfe4ea] bg-transparent pl-10 pr-4 text-sm outline-none focus:border-[#FA9C00] dark:border-slate-600"/></label><select value={main} onChange={(event) => {setMain(event.target.value);setSub("");}} className="h-11 rounded-xl border border-[#dfe4ea] bg-white px-4 text-sm dark:border-slate-600 dark:bg-slate-800"><option value="">대분류 선택</option>{[...categoryMap.keys()].map((value) => <option key={value}>{value}</option>)}</select><select value={sub} onChange={(event) => setSub(event.target.value)} disabled={!main} className="h-11 rounded-xl border border-[#dfe4ea] bg-white px-4 text-sm disabled:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:disabled:bg-slate-900"><option value="">중분류 선택</option>{[...(categoryMap.get(main) ?? [])].map((value) => <option key={value}>{value}</option>)}</select><button onClick={save} disabled={!selected.length || !main || !sub || saving} className="h-11 rounded-xl bg-[#E98200] px-5 text-sm font-semibold text-white transition hover:bg-[#C96F00] disabled:bg-slate-300 dark:disabled:bg-slate-700">{saving ? "저장 중" : `${selected.length}개 일괄 등록`}</button></div><p className="mt-3 text-xs text-slate-500 dark:text-slate-400">헤더 체크박스로 검색 결과 전체 선택 · Shift+체크로 연속 범위 선택</p></div><div className="card overflow-hidden p-3"><div className="h-[560px] ag-theme-itnew"><AgGridReact<ReviewItem> theme={gridTheme} rowData={data.reviewItems} columnDefs={columns} rowSelection={{ mode: "multiRow", selectAll: "filtered" }} pagination paginationPageSize={50} onGridReady={({api: gridApi}) => {api.current = gridApi; gridApi.setGridOption("quickFilterText", search);}} onSelectionChanged={({api: gridApi}) => setSelected(gridApi.getSelectedRows())}/></div></div></div>;
}
