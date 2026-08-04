import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const execute = promisify(execFile);

export async function GET() {
  try {
    const repositoryRoot = path.resolve(process.cwd(), "..");
    const { stdout } = await execute("python3", ["-m", "services.monthly.web_api"], {
      cwd: repositoryRoot,
      maxBuffer: 5 * 1024 * 1024,
    });
    return NextResponse.json(JSON.parse(stdout));
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "월간 데이터를 불러오지 못했습니다." }, { status: 500 });
  }
}
