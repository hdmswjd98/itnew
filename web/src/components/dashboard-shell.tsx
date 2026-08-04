"use client";

import {
  BarChart3,
  Boxes,
  CalendarDays,
  ChevronRight,
  Home,
  RefreshCw,
  Search,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AgGridReact } from "ag-grid-react";
import { themeQuartz, type ColDef, type GridApi } from "ag-grid-community";
import type { ProductDashboardData, ReviewItem } from "@/types/products";

type View = "home" | "customer" | "monthly" | "product";
type ProductView = "status" | "review" | "rules";

const navigation = [
  { key: "home" as View, label: "홈", icon: Home },
  { key: "customer" as View, label: "고객분석", icon: Users },
  { key: "monthly" as View, label: "월간리포트", icon: CalendarDays },
  { key: "product" as View, label: "품목 자동분류", icon: Boxes },
];

const gridTheme = themeQuartz.withParams({
  accentColor: "#25b79f",
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
  const [productView, setProductView] = useState<ProductView>("status");
  const [data, setData] = useState<ProductDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/products", { cache: "no-store" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setData(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "데이터를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(loadData);
  }, [loadData]);

  return (
    <div className="min-h-screen bg-[#f6f8fb] lg:flex">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col bg-[#13263d] px-5 py-7 text-white lg:flex">
        <div className="mb-10 flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#25b79f] font-bold">잇</div>
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
          <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" />Python 분석 서비스 연결</div>
        </div>
      </aside>

      <main className="min-w-0 flex-1 lg:ml-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-[#e6eaf0] bg-white/90 px-6 backdrop-blur lg:px-10">
          <div className="text-sm text-slate-500">잇뉴 <span className="mx-2">/</span> <b className="text-[#17202a]">{navigation.find((item) => item.key === view)?.label}</b></div>
          <div className="text-xs text-slate-500">{data ? `마지막 갱신 ${new Date(data.updatedAt).toLocaleString("ko-KR")}` : "데이터 확인 중"}</div>
        </header>
        <div className="p-6 lg:p-10">
          {error && <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
          {loading && !data ? <Loading /> : view === "home" ? <HomeDashboard data={data} onNavigate={(next) => setView(next)} /> : view === "product" ? <ProductDashboard data={data} productView={productView} setProductView={setProductView} reload={loadData} /> : <MigrationPlaceholder view={view} />}
        </div>
      </main>
    </div>
  );
}

function Loading() {
  return <div className="grid min-h-[60vh] place-items-center"><RefreshCw className="animate-spin text-[#25b79f]" /></div>;
}

function HomeDashboard({ data, onNavigate }: { data: ProductDashboardData | null; onNavigate: (view: View) => void }) {
  if (!data) return null;
  const rate = data.total ? (data.classified / data.total) * 100 : 0;
  return <>
    <div className="mb-8"><p className="mb-2 text-sm font-semibold text-[#25a58f]">OVERVIEW</p><h1 className="text-3xl font-bold tracking-tight text-[#17202a]">오늘의 데이터 현황</h1><p className="mt-2 text-sm text-slate-500">고객과 품목 분석 상태를 한눈에 확인하세요.</p></div>
    <div className="mb-7 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Kpi label="전체 주문 품목" value={`${number(data.total)}건`} note="등록된 주문 기준" />
      <Kpi label="고유 품목명" value={`${number(data.uniqueItems)}개`} note="중복 품목 제외" />
      <Kpi label="자동분류율" value={`${rate.toFixed(1)}%`} note={`${number(data.classified)}건 분류 완료`} tone="mint" />
      <button onClick={() => onNavigate("product")} className="card p-5 text-left transition hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-lg"><div className="text-sm text-slate-500">검토 필요</div><div className="mt-3 flex items-end justify-between"><strong className="text-3xl text-amber-600">{number(data.reviewCount)}건</strong><ChevronRight className="text-amber-500" /></div><div className="mt-3 text-xs text-slate-400">클릭하여 품목 검토</div></button>
    </div>
    <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
      <CategoryChart data={data} />
      <div className="card p-6"><h2 className="text-lg font-bold">분석 바로가기</h2><p className="mt-1 text-sm text-slate-500">자주 사용하는 업무로 이동합니다.</p><div className="mt-5 space-y-3">{navigation.slice(1).map((item) => <button key={item.key} onClick={() => onNavigate(item.key)} className="flex w-full items-center rounded-xl border border-[#edf0f4] p-4 text-left text-sm font-semibold transition hover:border-[#25b79f] hover:bg-[#f4fbf9]"><item.icon className="mr-3 text-[#25a58f]" size={18}/>{item.label}<ChevronRight className="ml-auto text-slate-400" size={16}/></button>)}</div></div>
    </div>
  </>;
}

function Kpi({ label, value, note, tone }: { label: string; value: string; note: string; tone?: "mint" }) {
  return <div className={`card p-5 ${tone === "mint" ? "border-[#c9eee5] bg-[#f7fcfb]" : ""}`}><div className="text-sm text-slate-500">{label}</div><div className="mt-3 text-3xl font-bold">{value}</div><div className="mt-3 text-xs text-slate-400">{note}</div></div>;
}

function CategoryChart({ data }: { data: ProductDashboardData }) {
  return <div className="card p-6"><div className="mb-5"><h2 className="text-lg font-bold">대분류별 품목 현황</h2><p className="mt-1 text-sm text-slate-500">주문 건수를 기준으로 집계했습니다.</p></div><div className="h-[360px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.categories.slice(0, 10)} layout="vertical" margin={{ left: 15, right: 30 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#edf0f4"/><XAxis type="number" tick={{fontSize: 11}} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="name" width={80} tick={{fontSize: 12}} axisLine={false} tickLine={false}/><Tooltip formatter={(value) => `${number(Number(value))}건`}/><Bar dataKey="count" fill="#25b79f" radius={[0, 6, 6, 0]} barSize={18}/></BarChart></ResponsiveContainer></div></div>;
}

function ProductDashboard({ data, productView, setProductView, reload }: { data: ProductDashboardData | null; productView: ProductView; setProductView: (view: ProductView) => void; reload: () => Promise<void> }) {
  const [refreshing, setRefreshing] = useState(false);
  if (!data) return null;
  const refresh = async () => { setRefreshing(true); await fetch("/api/products/actions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "refresh" }) }); await reload(); setRefreshing(false); };
  return <>
    <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="mb-2 text-sm font-semibold text-[#25a58f]">PRODUCT ANALYTICS</p><h1 className="text-3xl font-bold">품목 자동분류</h1><p className="mt-2 text-sm text-slate-500">자동분류 현황을 확인하고 검토 품목을 일괄 수정합니다.</p></div><button onClick={refresh} disabled={refreshing} className="flex items-center justify-center gap-2 rounded-xl bg-[#13263d] px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"><RefreshCw size={16} className={refreshing ? "animate-spin" : ""}/>{refreshing ? "분류 중" : "데이터 새로고침"}</button></div>
    <div className="mb-6 grid gap-4 md:grid-cols-4"><Kpi label="전체 주문 품목" value={`${number(data.total)}건`} note="전체 행 기준"/><Kpi label="고유 품목" value={`${number(data.uniqueItems)}개`} note="중복 제외"/><Kpi label="자동분류" value={`${number(data.classified)}건`} note={`${((data.classified/data.total)*100).toFixed(1)}% 완료`} tone="mint"/><Kpi label="검토 필요" value={`${number(data.reviewCount)}건`} note={`${data.reviewItems.length}개 고유 품목`}/></div>
    <div className="mb-6 flex gap-2 border-b border-[#e6eaf0]">{(["status","review","rules"] as ProductView[]).map((tab) => <button key={tab} onClick={() => setProductView(tab)} className={`border-b-2 px-5 py-3 text-sm font-semibold ${productView === tab ? "border-[#25b79f] text-[#168f7c]" : "border-transparent text-slate-500"}`}>{tab === "status" ? "분류 현황" : tab === "review" ? `검토 필요 ${number(data.reviewCount)}` : "기업 규칙"}</button>)}</div>
    {productView === "status" ? <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]"><CategoryChart data={data}/><div className="card overflow-hidden"><div className="border-b border-[#edf0f4] p-5"><h2 className="font-bold">카테고리 상세</h2></div><div className="max-h-[410px] overflow-auto"><table className="w-full text-sm"><thead className="sticky top-0 bg-[#f7f9fb] text-left text-xs text-slate-500"><tr><th className="p-3">대분류</th><th className="p-3">중분류</th><th className="p-3 text-right">건수</th></tr></thead><tbody>{data.categoryDetails.map((row) => <tr key={`${row.main}-${row.sub}`} className="border-t border-[#f0f2f5]"><td className="p-3 font-medium">{row.main}</td><td className="p-3 text-slate-500">{row.sub}</td><td className="p-3 text-right">{number(row.count)}</td></tr>)}</tbody></table></div></div></div> : productView === "review" ? <ReviewGrid data={data} reload={reload}/> : <div className="card p-8"><h2 className="text-lg font-bold">기업 우선 분류 규칙</h2><p className="mt-2 text-sm text-slate-500">수기 분류로 등록한 규칙을 조회·수정하는 화면을 연결하고 있습니다.</p></div>}
  </>;
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
  return <div className="space-y-5"><div className="card p-5"><div className="flex flex-col gap-3 lg:flex-row"><label className="relative flex-1"><Search className="absolute left-3 top-3 text-slate-400" size={17}/><input value={search} onChange={(event) => { setSearch(event.target.value); api.current?.setGridOption("quickFilterText", event.target.value); }} placeholder="품목명 검색" className="h-11 w-full rounded-xl border border-[#dfe4ea] pl-10 pr-4 text-sm outline-none focus:border-[#25b79f]"/></label><select value={main} onChange={(event) => {setMain(event.target.value);setSub("");}} className="h-11 rounded-xl border border-[#dfe4ea] bg-white px-4 text-sm"><option value="">대분류 선택</option>{[...categoryMap.keys()].map((value) => <option key={value}>{value}</option>)}</select><select value={sub} onChange={(event) => setSub(event.target.value)} disabled={!main} className="h-11 rounded-xl border border-[#dfe4ea] bg-white px-4 text-sm disabled:bg-slate-50"><option value="">중분류 선택</option>{[...(categoryMap.get(main) ?? [])].map((value) => <option key={value}>{value}</option>)}</select><button onClick={save} disabled={!selected.length || !main || !sub || saving} className="h-11 rounded-xl bg-[#25a58f] px-5 text-sm font-semibold text-white disabled:bg-slate-300">{saving ? "저장 중" : `${selected.length}개 일괄 등록`}</button></div><p className="mt-3 text-xs text-slate-500">헤더 체크박스로 검색 결과 전체 선택 · Shift+체크로 연속 범위 선택</p></div><div className="card overflow-hidden p-3"><div className="h-[560px] ag-theme-itnew"><AgGridReact<ReviewItem> theme={gridTheme} rowData={data.reviewItems} columnDefs={columns} rowSelection={{ mode: "multiRow", selectAll: "filtered" }} pagination paginationPageSize={50} onGridReady={({api: gridApi}) => {api.current = gridApi; gridApi.setGridOption("quickFilterText", search);}} onSelectionChanged={({api: gridApi}) => setSelected(gridApi.getSelectedRows())}/></div></div></div>;
}

function MigrationPlaceholder({ view }: { view: View }) {
  const title = view === "customer" ? "고객분석" : "월간리포트";
  return <div><p className="mb-2 text-sm font-semibold text-[#25a58f]">NEXT.JS MIGRATION</p><h1 className="text-3xl font-bold">{title}</h1><div className="card mt-7 grid min-h-[420px] place-items-center p-10 text-center"><div><BarChart3 className="mx-auto mb-4 text-[#25b79f]" size={42}/><h2 className="text-xl font-bold">{title} 화면 이전 준비 완료</h2><p className="mt-2 text-sm text-slate-500">공통 레이아웃과 데이터 API를 기반으로 다음 순서에서 연결합니다.</p></div></div></div>;
}
