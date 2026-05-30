import { NextRequest, NextResponse } from "next/server";
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

export const dynamic = "force-dynamic";

const execFileAsync = promisify(execFile);

// POST /api/update-data                     → update Sackmann CSVs + merge TennisLive
// POST /api/update-data?source=sackmann     → Sackmann only
// POST /api/update-data?source=tennislive   → TennisLive scrape + merge only
// POST /api/update-data?source=merge        → merge existing TennisLive data only

export async function POST(request: NextRequest) {
  const source = request.nextUrl.searchParams.get("source") ?? "all";
  const results: Record<string, unknown> = {};

  try {
    // 1. Sackmann CSV auto-update
    if (source === "all" || source === "sackmann") {
      const sackmannScript = path.join(process.cwd(), "scripts", "update-sackmann.mjs");
      try {
        const { stdout } = await execFileAsync("node", [sackmannScript], {
          cwd: process.cwd(), timeout: 180000,
        });
        results.sackmann = JSON.parse(stdout.trim());
      } catch (e) {
        results.sackmann = { ok: false, error: e instanceof Error ? e.message : String(e) };
      }
    }

    // 2. TennisLive live scrape (rankings + player profiles for today's match players)
    if (source === "all" || source === "tennislive") {
      const tlScript = path.join(process.cwd(), "scripts", "tennislive-full-scraper.py");
      try {
        // Scrape rankings first, then upcoming/live matches, then profiles for those players
        const { stdout: rankOut } = await execFileAsync(
          "python3", [tlScript, "rankings"], { cwd: process.cwd(), timeout: 120000 }
        );
        results.tlRankings = { ok: true, output: rankOut.trim().slice(0, 200) };
      } catch (e) {
        results.tlRankings = { ok: false, error: e instanceof Error ? e.message : String(e) };
      }
    }

    // 3. Merge TennisLive data into player-summaries.json
    if (source === "all" || source === "tennislive" || source === "merge") {
      const mergeScript = path.join(process.cwd(), "scripts", "tennislive-merge.mjs");
      try {
        const { stdout: mergeOut } = await execFileAsync("node", [mergeScript], {
          cwd: process.cwd(), timeout: 60000,
        });
        results.merge = { ok: true, output: mergeOut.trim().slice(0, 500) };
      } catch (e) {
        results.merge = { ok: false, error: e instanceof Error ? e.message : String(e) };
      }
    }

    return NextResponse.json({ ok: true, source, results });
  } catch (error) {
    return NextResponse.json(
      { ok: false, error: error instanceof Error ? error.message : "Update failed" },
      { status: 500 }
    );
  }
}
