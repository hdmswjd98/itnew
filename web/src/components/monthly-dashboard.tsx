"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CalendarDays, FileText, PackageCheck, RefreshCw, Users } from "lucide-react";
import type { MonthlyData } from "@/types/analytics";
import { PageHeading } from "@/components/customer-dashboard";

const number = (value:number)=>new Intl.NumberFormat("ko-KR").format(value);

export function MonthlyDashboard(){
  const [data,setData]=useState<MonthlyData|null>(null); const [error,setError]=useState("");
  useEffect(()=>{void fetch("/api/monthly",{cache:"no-store"}).then(async response=>{const result=await response.json();if(!response.ok)throw new Error(result.error);setData(result)}).catch(reason=>setError(reason instanceof Error?reason.message:"월간 데이터를 불러오지 못했습니다."))},[]);
  if(error)return <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">{error}</div>;
  if(!data)return <div className="grid min-h-[60vh] place-items-center"><RefreshCw className="animate-spin text-[#FA9C00]"/></div>;
  const latest=data.trends.at(-1); const previous=data.trends.at(-2); const change=latest&&previous?((latest.orders-previous.orders)/previous.orders*100):0;
  return <>
    <PageHeading eyebrow="MONTHLY REPORT" title="월간리포트" description="월별 주문·활성 고객·배송 수량 추이와 저장된 운영보고서를 확인합니다."/>
    <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Metric icon={CalendarDays} label="기준 월" value={latest?.month??"데이터 없음"} note="최근 주문 데이터"/>
      <Metric icon={FileText} label="월 주문 건수" value={`${number(latest?.orders??0)}건`} note={`${change>=0?"+":""}${change.toFixed(1)}% 전월 대비`}/>
      <Metric icon={Users} label="활성 고객" value={`${number(latest?.customers??0)}명`} note="해당 월 주문 고객"/>
      <Metric icon={PackageCheck} label="배송 수량" value={`${number(latest?.quantity??0)}개`} note="월 누적 수량"/>
    </div>
    <div className="card mb-6 p-6"><h2 className="text-lg font-bold">최근 12개월 운영 추이</h2><p className="mb-5 mt-1 text-sm text-slate-500 dark:text-slate-400">주문 건수와 활성 고객 변화를 비교합니다.</p><div className="h-[380px]"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data.trends}><defs><linearGradient id="orders" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="var(--chart-accent)" stopOpacity={.3}/><stop offset="95%" stopColor="var(--chart-accent)" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e9edf2"/><XAxis dataKey="month" axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip/><Legend/><Area type="monotone" dataKey="orders" name="주문 건수" stroke="var(--chart-accent)" fill="url(#orders)" strokeWidth={2}/><Area type="monotone" dataKey="customers" name="활성 고객" stroke="#4f7cff" fill="transparent" strokeWidth={2}/></AreaChart></ResponsiveContainer></div></div>
    <div className="card overflow-hidden"><div className="border-b border-slate-100 p-6 dark:border-slate-700"><h2 className="text-lg font-bold">저장된 운영보고서</h2><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">월별 이슈·조치·계획을 확인합니다.</p></div>{data.reports.length?<div className="divide-y divide-slate-100 dark:divide-slate-700">{data.reports.map(report=><details key={report.report_month} className="group p-6"><summary className="flex cursor-pointer list-none items-center justify-between"><div><b>{report.report_month} 운영보고서</b><span className="ml-3 text-xs text-slate-400">수정 {new Date(report.updated_at).toLocaleDateString("ko-KR")}</span></div><span className="text-sm text-[#E98200] group-open:rotate-180">⌄</span></summary><div className="mt-5 grid gap-4 md:grid-cols-3"><ReportBlock title="주요 이슈" rows={report.issues}/><ReportBlock title="조치 내역" rows={report.actions}/><ReportBlock title="성과" rows={report.results}/></div><div className="mt-4 grid gap-4 md:grid-cols-2"><ReportBlock title="다음 달 계획" rows={[report.next_month_plan]}/><ReportBlock title="협력 요청" rows={[report.partner_requests]}/></div></details>)}</div>:<div className="p-10 text-center text-sm text-slate-500">저장된 운영보고서가 없습니다.</div>}</div>
  </>;
}
function Metric({icon:Icon,label,value,note}:{icon:typeof Users;label:string;value:string;note:string}){return <div className="card p-5"><div className="flex items-center justify-between"><span className="text-sm text-slate-500 dark:text-slate-400">{label}</span><Icon className="text-[#E98200]" size={18}/></div><div className="mt-3 text-2xl font-bold">{value}</div><div className="mt-2 text-xs text-slate-400">{note}</div></div>}
function ReportBlock({title,rows}:{title:string;rows:string[]}){return <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800"><div className="mb-2 text-xs font-bold text-slate-500 dark:text-slate-400">{title}</div>{rows.filter(Boolean).length?<ul className="space-y-1 text-sm">{rows.filter(Boolean).map((row,index)=><li key={index}>• {row}</li>)}</ul>:<p className="text-sm text-slate-400">작성 내용 없음</p>}</div>}
