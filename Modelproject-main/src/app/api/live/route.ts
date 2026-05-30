import { NextRequest, NextResponse } from "next/server";
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import {
  getPrototypeLiveTennis,
  getSofaScoreFinishedTennis,
  getSofaScoreLiveTennis,
  getSofaScoreUpcomingTennis
} from "@/lib/sofascore";
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

export async function GET(request: NextRequest) {
  const type = request.nextUrl.searchParams.get("type") ?? "live";

  if (type === "upcoming") {
    try {
      const matches = await getSofaScoreUpcomingTennis();
      return NextResponse.json({ provider: "sofascore", transport: "fetch", matches });
    } catch (error) {
      return NextResponse.json({
        provider: "sofascore",
        matches: [] as LiveMatch[],
        warning: error instanceof Error ? error.message : "Unable to fetch upcoming matches"
      });
    }
  }

  if (type === "finished") {
    try {
      const matches = await getSofaScoreFinishedTennis();
      return NextResponse.json({ provider: "sofascore", transport: "fetch", matches });
    } catch (error) {
      return NextResponse.json({
        provider: "sofascore",
        matches: [] as LiveMatch[],
        warning: error instanceof Error ? error.message : "Unable to fetch finished matches"
      });
    }
  }

  // Live (default)
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
      return NextResponse.json({
        provider: "sofascore",
        matches: getPrototypeLiveTennis(message),
        warning: message
      });
    }
  }
}
