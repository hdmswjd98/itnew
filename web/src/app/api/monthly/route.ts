import { spawn } from "node:child_process";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function runWebApi(payload?: unknown) {
  return new Promise<string>((resolve, reject) => {
    const child = spawn("python3", ["-m", "services.monthly.web_api"], { cwd: path.resolve(process.cwd(), "..") });
    let output = "", error = "";
    child.stdout.on("data", (chunk) => output += chunk);
    child.stderr.on("data", (chunk) => error += chunk);
    child.on("error", reject);
    child.on("close", (code) => code === 0 ? resolve(output) : reject(new Error(error || output)));
    child.stdin.end(payload !== undefined ? JSON.stringify(payload) : "");
  });
}

export async function GET() {
  try {
    const stdout = await runWebApi();
    return NextResponse.json(JSON.parse(stdout));
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "월간 데이터를 불러오지 못했습니다." }, { status: 500 });
  }
}

export async function POST(request:NextRequest) {
  try {
    const payload=await request.json();
    const stdout=await runWebApi(payload);
    const result=JSON.parse(stdout); if(!result.ok)throw new Error(result.error); return NextResponse.json(result.data);
  } catch(error) { return NextResponse.json({error:error instanceof Error?error.message:"월간보고서 요청에 실패했습니다."},{status:500}); }
}
