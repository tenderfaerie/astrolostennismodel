import { NextResponse } from "next/server";
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import { getPrototypeLiveTennis, getSofaScoreLiveTennis } from "@/lib/sofascore";
import { LiveMatch } from "@/lib/types";

export const dynamic = "force-dynamic";

const execFileAsync = promisify(execFile);

async function getSofaScoreViaPython(): Promise<LiveMatch[]> {
  const today = new Date().toISOString().slice(0, 10);
  const script = path.join(process.cwd(), "scripts", "sofascore-live.py");
  const { stdout } = await execFileAsync("python", [script, today], {
    timeout: 90000,
    maxBuffer: 1024 * 1024 * 4
  });
  return JSON.parse(stdout) as LiveMatch[];
}

export async function GET() {
  try {
    const matches = await getSofaScoreViaPython();
    return NextResponse.json({ provider: "sofascore", transport: "python_tls_client", matches });
  } catch (error) {
    try {
      const matches = await getSofaScoreLiveTennis();
      return NextResponse.json({ provider: "sofascore", transport: "fetch", matches });
    } catch (fallbackError) {
      const message = fallbackError instanceof Error
        ? fallbackError.message
        : error instanceof Error
          ? error.message
          : "Unable to fetch SofaScore live tennis";
      return NextResponse.json(
        {
          provider: "sofascore",
          matches: getPrototypeLiveTennis(message),
          warning: message
        }
      );
    }
  }
}
