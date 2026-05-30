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

async function getFlashscoreITF(mode: "live" | "upcoming" | "finished"): Promise<LiveMatch[]> {
  const script = path.join(process.cwd(), "scripts", "flashscore-itf.py");
  const { stdout } = await execFileAsync("python3", [script, mode], {
    timeout: 60000,
    maxBuffer: 1024 * 1024 * 4
  });
  return JSON.parse(stdout) as LiveMatch[];
}

function dedupeByPlayers(primary: LiveMatch[], secondary: LiveMatch[]): LiveMatch[] {
  const seen = new Set(primary.map((m) => `${m.homePlayer}|${m.awayPlayer}`));
  const novel = secondary.filter((m) => !seen.has(`${m.homePlayer}|${m.awayPlayer}`));
  return [...primary, ...novel];
}

export async function GET(request: NextRequest) {
  const type = request.nextUrl.searchParams.get("type") ?? "live";

  if (type === "upcoming") {
    const [sofaResult, flashResult] = await Promise.allSettled([
      getSofaScoreUpcomingTennis(),
      getFlashscoreITF("upcoming"),
    ]);
    const sofaMatches = sofaResult.status === "fulfilled" ? sofaResult.value : [];
    const flashMatches = flashResult.status === "fulfilled" ? flashResult.value : [];
    const matches = dedupeByPlayers(sofaMatches, flashMatches);
    const warning = sofaResult.status === "rejected"
      ? (sofaResult.reason instanceof Error ? sofaResult.reason.message : "Unable to fetch upcoming matches")
      : undefined;
    return NextResponse.json({ provider: "sofascore+flashscore", transport: "fetch", matches, warning });
  }

  if (type === "finished") {
    const daysBackParam = request.nextUrl.searchParams.get("daysBack");
    const daysBack = daysBackParam ? Math.min(Math.max(Number(daysBackParam) || 14, 1), 30) : 14;
    const [sofaResult, flashResult] = await Promise.allSettled([
      getSofaScoreFinishedTennis(daysBack),
      getFlashscoreITF("finished"),
    ]);
    const sofaMatches = sofaResult.status === "fulfilled" ? sofaResult.value : [];
    const flashMatches = flashResult.status === "fulfilled" ? flashResult.value : [];
    const matches = dedupeByPlayers(sofaMatches, flashMatches);
    const warning = sofaResult.status === "rejected"
      ? (sofaResult.reason instanceof Error ? sofaResult.reason.message : "Unable to fetch finished matches")
      : undefined;
    return NextResponse.json({ provider: "sofascore+flashscore", transport: "fetch", matches, daysBack, warning });
  }

  // Live (default) — SofaScore primary, Flashscore ITF supplement
  const [sofaResult, flashResult] = await Promise.allSettled([
    getSofaScoreViaPython().catch(() => getSofaScoreLiveTennis()),
    getFlashscoreITF("live"),
  ]);

  const sofaMatches = sofaResult.status === "fulfilled" ? sofaResult.value : [];
  const flashMatches = flashResult.status === "fulfilled" ? flashResult.value : [];

  if (sofaMatches.length === 0 && flashMatches.length === 0) {
    const message = sofaResult.status === "rejected"
      ? (sofaResult.reason instanceof Error ? sofaResult.reason.message : "Unable to fetch live tennis")
      : "No live matches found";
    return NextResponse.json({
      provider: "sofascore+flashscore",
      matches: getPrototypeLiveTennis(message),
      warning: message
    });
  }

  const matches = dedupeByPlayers(sofaMatches, flashMatches);
  return NextResponse.json({ provider: "sofascore+flashscore", transport: "combined", matches });
}
