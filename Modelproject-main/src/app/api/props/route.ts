import { NextRequest, NextResponse } from "next/server";
import { findPlayerByName } from "@/lib/historical";
import { calcEV, formAdjustedPlayer, projectProp, propCategories, surfaceAdjustedPlayer } from "@/lib/prop-model";

const marketPattern = propCategories
  .flatMap((category) => [category.label, ...category.aliases])
  .sort((a, b) => b.length - a.length)
  .map((value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
  .join("|");
const linePattern = new RegExp(`(.+?)\\s+(${marketPattern})\\s+(over|under|o|u)?\\s*([0-9]+(?:\\.[0-9]+)?)`, "i");

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));

  if (body.player && body.market && body.line !== undefined) {
    let player = await findPlayerByName(String(body.player));
    const opponent = body.opponent ? await findPlayerByName(String(body.opponent)) : undefined;
    let opponentAdj = opponent ?? null;

    if (!player) {
      return NextResponse.json({ error: "Player not found", projections: [], unmatched: [String(body.player)] }, { status: 404 });
    }

    const surface = typeof body.surface === "string" ? body.surface : "";
    if (surface && surface !== "All") {
      player = surfaceAdjustedPlayer(player, surface);
      if (opponentAdj) opponentAdj = surfaceAdjustedPlayer(opponentAdj, surface);
    }
    if (body.useForm) {
      player = formAdjustedPlayer(player);
      if (opponentAdj) opponentAdj = formAdjustedPlayer(opponentAdj);
    }

    const projection = projectProp(
      player,
      String(body.market),
      Number(body.line),
      body.side === "Over" || body.side === "Under" ? body.side : undefined,
      opponentAdj
    );

    if (body.americanOdds && Number.isFinite(Number(body.americanOdds))) {
      const ev = calcEV(projection.confidence, Number(body.americanOdds));
      Object.assign(projection, { ...ev, americanOdds: Number(body.americanOdds), surface: surface || undefined });
    } else if (surface) {
      Object.assign(projection, { surface });
    }

    return NextResponse.json({ projection, projections: [projection], unmatched: opponent || !body.opponent ? [] : [String(body.opponent)] });
  }

  const text = String(body.text ?? "");
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const projections = [];
  const unmatched = [];

  for (const line of lines) {
    const match = line.match(linePattern);
    if (!match) {
      unmatched.push(line);
      continue;
    }

    const [, playerName, market, sideRaw, lineRaw] = match;
    const player = await findPlayerByName(playerName);

    if (!player) {
      unmatched.push(line);
      continue;
    }

    const side = sideRaw?.toLowerCase().startsWith("u") ? "Under" : sideRaw ? "Over" : undefined;
    projections.push(projectProp(player, market, Number(lineRaw), side));
  }

  return NextResponse.json({ projections, unmatched });
}
