import { spawn } from "node:child_process";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

function runPython(payload: unknown) {
  return new Promise<Record<string, unknown>>((resolve, reject) => {
    const repositoryRoot = path.resolve(process.cwd(), "..");
    const childProcess = spawn("python3", ["-m", "services.product.web_api"], {
      cwd: repositoryRoot,
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });
    let stdout = "";
    let stderr = "";
    childProcess.stdout.on("data", (chunk) => (stdout += chunk.toString()));
    childProcess.stderr.on("data", (chunk) => (stderr += chunk.toString()));
    childProcess.on("error", reject);
    childProcess.on("close", (code) => {
      try {
        const result = JSON.parse(stdout);
        if (code === 0 && result.ok) resolve(result.data);
        else reject(new Error(result.error || stderr || "Python 분석 실행에 실패했습니다."));
      } catch {
        reject(new Error(stderr || stdout || "Python 응답을 해석하지 못했습니다."));
      }
    });
    childProcess.stdin.end(JSON.stringify(payload));
  });
}

export async function POST(request: NextRequest) {
  try {
    const result = await runPython(await request.json());
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "요청을 처리하지 못했습니다." },
      { status: 500 },
    );
  }
}
