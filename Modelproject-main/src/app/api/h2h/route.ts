import { NextRequest, NextResponse } from "next/server";
import fs from "node:fs/promises";
import path from "node:path";
import { findPlayerByName } from "@/lib/historical";
import { H2HRecord } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const p1 = request.nextUrl.searchParams.get("p1") ?? "";
  const p2 = request.nextUrl.searchParams.get("p2") ?? "";

  const [player1, player2] = await Promise.all([findPlayerByName(p1), findPlayerByName(p2)]);

  if (!player1 || !player2) {
    return NextResponse.json({ error: "One or both players not found" }, { status: 404 });
  }

  // Try h2h.json (populated by import-sackmann)
  try {
    const raw = await fs.readFile(path.join(process.cwd(), "data", "h2h.json"), "utf8");
    const h2h = JSON.parse(raw) as Record<string, { p1Id: string; p2Id: string; p1Wins: number; p2Wins: number; meetings: Array<{ date: string; tournament: string; surface: string; winnerId: string; score: string }> }>;
    const key = [player1.playerId, player2.playerId].sort().join(":");
    const data = h2h[key];
    if (data) {
      const p1IsFirst = data.p1Id === player1.playerId;
      const meetings = data.meetings
        .map((m) => ({ ...m, winner: m.winnerId === player1.playerId ? player1.name : player2.name }))
        .sort((a, b) => b.date.localeCompare(a.date));
      const bySurface: Record<string, { player1Wins: number; player2Wins: number }> = {};
      for (const m of meetings) {
        bySurface[m.surface] ??= { player1Wins: 0, player2Wins: 0 };
        if (m.winner === player1.name) bySurface[m.surface].player1Wins++;
        else bySurface[m.surface].player2Wins++;
      }
      const record: H2HRecord = {
        player1Name: player1.name,
        player2Name: player2.name,
        player1Wins: p1IsFirst ? data.p1Wins : data.p2Wins,
        player2Wins: p1IsFirst ? data.p2Wins : data.p1Wins,
        totalMatches: data.p1Wins + data.p2Wins,
        meetings,
        bySurface
      };
      return NextResponse.json({ record, player1, player2 });
    }
  } catch {
    // h2h.json not yet generated — fall through to recentMatches
  }

  function nameMatches(opponentField: string, targetName: string): boolean {
    const oLow = opponentField.toLowerCase().trim();
    const tLow = targetName.toLowerCase().trim();
    if (oLow === tLow || oLow.includes(tLow) || tLow.includes(oLow)) return true;
    const lastName = tLow.split(" ").at(-1) ?? "";
    if (lastName.length < 4) return false;
    return oLow.split(/\s+/).some((w) => w === lastName);
  }

  // Fallback: derive from recentMatches
  const p1Matches = (player1.recentMatches ?? []).filter((m) => nameMatches(m.opponent, player2.name));
  const p2Matches = (player2.recentMatches ?? []).filter((m) => nameMatches(m.opponent, player1.name));

  const seen = new Set<string>();
  const meetings: H2HRecord["meetings"] = [];
  for (const m of [...p1Matches, ...p2Matches]) {
    if (seen.has(m.date)) continue;
    seen.add(m.date);
    const winner = p1Matches.find((x) => x.date === m.date)
      ? (m.result === "W" ? player1.name : player2.name)
      : (m.result === "W" ? player2.name : player1.name);
    meetings.push({ date: m.date, tournament: m.tournament, surface: m.surface, winner, score: m.score });
  }
  meetings.sort((a, b) => b.date.localeCompare(a.date));

  const bySurface: Record<string, { player1Wins: number; player2Wins: number }> = {};
  for (const m of meetings) {
    bySurface[m.surface] ??= { player1Wins: 0, player2Wins: 0 };
    if (m.winner === player1.name) bySurface[m.surface].player1Wins++;
    else bySurface[m.surface].player2Wins++;
  }

  const record: H2HRecord = {
    player1Name: player1.name,
    player2Name: player2.name,
    player1Wins: meetings.filter((m) => m.winner === player1.name).length,
    player2Wins: meetings.filter((m) => m.winner === player2.name).length,
    totalMatches: meetings.length,
    meetings,
    bySurface
  };

  return NextResponse.json({ record, player1, player2 });
}
