import { spawn } from "node:child_process";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

function run(moduleName: string) {
  return new Promise<void>((resolve, reject) => {
    const child = spawn("python3", ["-m", moduleName], {
      cwd: path.resolve(process.cwd(), ".."),
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });
    let output = "";
    child.stdout.on("data", (chunk) => (output += chunk.toString()));
    child.stderr.on("data", (chunk) => (output += chunk.toString()));
    child.on("error", reject);
    child.on("close", (code) => code === 0 ? resolve() : reject(new Error(output || `${moduleName} 실행 실패`)));
  });
}

export async function POST() {
  try {
    await run("services.customer.pipeline");
    await run("services.product.classifier");
    return NextResponse.json({ ok: true, refreshedAt: new Date().toISOString() });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "데이터 새로고침에 실패했습니다." }, { status: 500 });
  }
}
