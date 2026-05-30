import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const workspace = process.cwd();
const dataDir = path.join(workspace, "data");
const downloads = path.join(os.homedir(), "Downloads");

const matchFiles = [
  ["ATP", "atp_matches_2024.csv"],
  ["ATP", "atp_matches_2025.csv"],
  ["ATP", "atp_matches_2026.csv"],
  ["Challenger", "atp_matches_qual_chall_2024.csv"],
  ["Challenger", "atp_matches_qual_chall_2025.csv"],
  ["Challenger", "atp_matches_qual_chall_2026.csv"],
  ["Futures", "atp_matches_futures_2024.csv"],
  ["Futures", "atp_matches_futures_2025.csv"],
  ["Futures", "atp_matches_futures_2026.csv"],
  ["ITF Men", "atp_matches_itf_2024.csv"],
  ["ITF Men", "atp_matches_itf_2025.csv"],
  ["ITF Men", "atp_matches_itf_2026.csv"],
  ["WTA", "wta_matches_2024.csv"],
  ["WTA", "wta_matches_2025.csv"],
  ["WTA", "wta_matches_2026.csv"],
  ["ITF Women", "wta_matches_qual_itf_2024.csv"],
  ["ITF Women", "wta_matches_qual_itf_2025.csv"],
  ["ITF Women", "wta_matches_qual_itf_2026.csv"]
];

const rankingFiles = [
  ["ATP", "atp_rankings_current.csv"],
  ["WTA", "wta_rankings_current.csv"]
];

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];

    if (char === '"' && quoted && next === '"') {
      cell += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(cell);
      if (row.some((value) => value.length)) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }

  if (cell.length || row.length) {
    row.push(cell);
    rows.push(row);
  }

  const headers = rows.shift() ?? [];
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

function number(value) {
  if (value === undefined || value === null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function pct(numerator, denominator) {
  return denominator > 0 ? numerator / denominator : null;
}

function playerKey(tour, id) {
  return `${tour}:${id}`;
}

const rankings = new Map();

for (const [tour, file] of rankingFiles) {
  const target = path.join(downloads, file);
  if (!fs.existsSync(target)) continue;
  for (const row of parseCsv(fs.readFileSync(target, "utf8"))) {
    rankings.set(playerKey(tour, row.player), {
      rank: number(row.rank),
      points: number(row.points)
    });
  }
}

// Lower number = more prestigious; used to pick the best tour label per player
const tourPriority = { ATP: 0, WTA: 0, Challenger: 1, Futures: 2, "ITF Men": 3, "ITF Women": 3 };

const players = new Map();

function ensurePlayer(tour, row, side) {
  const id = row[`${side}_id`];
  const rankingTour = (tour === "WTA" || tour === "ITF Women") ? "WTA" : "ATP";
  const key = playerKey(rankingTour, id);
  if (!players.has(key)) {
    const ranking = rankings.get(key) ?? {};
    players.set(key, {
      playerId: id,
      name: row[`${side}_name`],
      tour,
      hand: row[`${side}_hand`] || undefined,
      height: number(row[`${side}_ht`]),
      country: row[`${side}_ioc`] || undefined,
      rank: ranking.rank ?? number(row[`${side}_rank`]),
      points: ranking.points ?? number(row[`${side}_rank_points`]),
      matches: 0,
      wins: 0,
      losses: 0,
      svpt: 0,
      aces: 0,
      dfs: 0,
      firstIn: 0,
      firstWon: 0,
      secondWon: 0,
      serviceGames: 0,
      bpSaved: 0,
      bpFaced: 0,
      returnGames: 0,
      bpCreated: 0,
      surfaces: {},
      recentMatches: []
    });
  }
  } else {
    // Upgrade tour to most prestigious level seen across all files
    const player = players.get(key);
    if ((tourPriority[tour] ?? 99) < (tourPriority[player.tour] ?? 99)) {
      player.tour = tour;
    }
  }
  return players.get(key);
}

function addSurface(player, surface, won) {
  const key = surface || "Unknown";
  player.surfaces[key] ??= { matches: 0, wins: 0, losses: 0, winPct: 0 };
  player.surfaces[key].matches += 1;
  if (won) player.surfaces[key].wins += 1;
  else player.surfaces[key].losses += 1;
}

function addMatchStats(player, row, side, opponentName, won) {
  player.matches += 1;
  if (won) player.wins += 1;
  else player.losses += 1;
  player.svpt += number(row[`${side}_svpt`]) ?? 0;
  player.aces += number(row[`${side}_ace`]) ?? 0;
  player.dfs += number(row[`${side}_df`]) ?? 0;
  player.firstIn += number(row[`${side}_1stIn`]) ?? 0;
  player.firstWon += number(row[`${side}_1stWon`]) ?? 0;
  player.secondWon += number(row[`${side}_2ndWon`]) ?? 0;
  player.serviceGames += number(row[`${side}_SvGms`]) ?? 0;
  player.bpSaved += number(row[`${side}_bpSaved`]) ?? 0;
  player.bpFaced += number(row[`${side}_bpFaced`]) ?? 0;
  addSurface(player, row.surface, won);

  player.recentMatches.push({
    date: row.tourney_date,
    tournament: row.tourney_name,
    surface: row.surface || "Unknown",
    opponent: opponentName,
    result: won ? "W" : "L",
    score: row.score
  });
}

for (const [tour, file] of matchFiles) {
  const target = path.join(downloads, file);
  if (!fs.existsSync(target)) continue;
  const rows = parseCsv(fs.readFileSync(target, "utf8"));

  for (const row of rows) {
    const winner = ensurePlayer(tour, row, "winner");
    const loser = ensurePlayer(tour, row, "loser");

    addMatchStats(winner, row, "w", row.loser_name, true);
    addMatchStats(loser, row, "l", row.winner_name, false);

    winner.returnGames += number(row.l_SvGms) ?? 0;
    winner.bpCreated += number(row.l_bpFaced) ?? 0;
    loser.returnGames += number(row.w_SvGms) ?? 0;
    loser.bpCreated += number(row.w_bpFaced) ?? 0;
  }
}

const summaries = [...players.values()].map((player) => {
  for (const surface of Object.values(player.surfaces)) {
    surface.winPct = pct(surface.wins, surface.matches) ?? 0;
  }

  player.recentMatches.sort((a, b) => b.date.localeCompare(a.date));

  return {
    playerId: player.playerId,
    name: player.name,
    tour: player.tour,
    hand: player.hand,
    height: player.height,
    country: player.country,
    rank: player.rank,
    points: player.points,
    matches: player.matches,
    wins: player.wins,
    losses: player.losses,
    winPct: pct(player.wins, player.matches) ?? 0,
    aceRate: pct(player.aces, player.svpt),
    dfRate: pct(player.dfs, player.svpt),
    firstServePct: pct(player.firstIn, player.svpt),
    firstServeWonPct: pct(player.firstWon, player.firstIn),
    secondServeWonPct: pct(player.secondWon, player.svpt - player.firstIn),
    holdProxyPct: null,
    bpSavedPct: pct(player.bpSaved, player.bpFaced),
    bpCreatedPerReturnGame: pct(player.bpCreated, player.returnGames),
    surfaces: player.surfaces,
    recentMatches: player.recentMatches.slice(0, 10)
  };
}).sort((a, b) => (a.rank ?? 9999) - (b.rank ?? 9999));

fs.mkdirSync(dataDir, { recursive: true });
fs.writeFileSync(path.join(dataDir, "player-summaries.json"), JSON.stringify(summaries, null, 2));

console.log(`Imported ${summaries.length} player summaries into data/player-summaries.json`);
