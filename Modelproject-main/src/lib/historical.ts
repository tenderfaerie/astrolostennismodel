import fs from "node:fs/promises";
import path from "node:path";
import { PlayerSummary } from "./types";

const dataDir = path.join(process.cwd(), "data");

export async function getPlayerSummaries(): Promise<PlayerSummary[]> {
  try {
    const raw = await fs.readFile(path.join(dataDir, "player-summaries.json"), "utf8");
    return JSON.parse(raw) as PlayerSummary[];
  } catch {
    return [];
  }
}

export async function searchPlayers(query: string, limit = 25): Promise<PlayerSummary[]> {
  const players = await getPlayerSummaries();
  const normalized = query.trim().toLowerCase();

  if (!normalized) {
    return players
      .slice()
      .sort((a, b) => (a.rank ?? 9999) - (b.rank ?? 9999))
      .slice(0, limit);
  }

  return players
    .filter((player) => player.name.toLowerCase().includes(normalized))
    .sort((a, b) => (a.rank ?? 9999) - (b.rank ?? 9999))
    .slice(0, limit);
}

export async function findPlayerByName(name: string): Promise<PlayerSummary | undefined> {
  const players = await getPlayerSummaries();
  const needle = name.trim().toLowerCase();
  return players.find((player) => player.name.toLowerCase() === needle)
    ?? players.find((player) => player.name.toLowerCase().includes(needle));
}
