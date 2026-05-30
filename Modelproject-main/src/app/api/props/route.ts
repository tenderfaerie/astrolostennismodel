import { NextRequest, NextResponse } from "next/server";
import { findPlayerByName } from "@/lib/historical";
import { projectProp, propCategories } from "@/lib/prop-model";

const marketPattern = propCategories
  .flatMap((category) => [category.label, ...category.aliases])
  .sort((a, b) => b.length - a.length)
  .map((value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
  .join("|");
const linePattern = new RegExp(`(.+?)\\s+(${marketPattern})\\s+(over|under|o|u)?\\s*([0-9]+(?:\\.[0-9]+)?)`, "i");

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));

  if (body.player && body.market && body.line !== undefined) {
    const player = await findPlayerByName(String(body.player));
    const opponent = body.opponent ? await findPlayerByName(String(body.opponent)) : undefined;

    if (!player) {
      return NextResponse.json({ error: "Player not found", projections: [], unmatched: [String(body.player)] }, { status: 404 });
    }

    const projection = projectProp(
      player,
      String(body.market),
      Number(body.line),
      body.side === "Over" || body.side === "Under" ? body.side : undefined,
      opponent
    );
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
