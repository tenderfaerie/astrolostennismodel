/**
 * Merges TennisLive scraped data into data/player-summaries.json
 *
 * Strategy:
 *  - TennisLive surface W/L data is more current (includes 2026 RG matches)
 *    → overrides Sackmann surfaces winPct for each year where TL has data
 *  - Sackmann data is authoritative for: aceRate, dfRate, firstServePct,
 *    firstServeWonPct, secondServeWonPct, bpSaved, bpCreated
 *    → we never overwrite these from TennisLive
 *  - Recent matches list: prefer TennisLive if it has newer entries
 *  - Ranking: TennisLive ranking is live, prefer it over Sackmann static rank
 *
 * Usage:
 *   node scripts/tennislive-merge.mjs
 *   node scripts/tennislive-merge.mjs --dry-run    (preview without writing)
 */

import fs from "node:fs";
import path from "node:path";

const DRY_RUN = process.argv.includes("--dry-run");
const workspace = process.cwd();
const dataDir = path.join(workspace, "data");
const tlDir = path.join(dataDir, "tennislive", "players");

const summariesPath = path.join(dataDir, "player-summaries.json");
const summaries = JSON.parse(fs.readFileSync(summariesPath, "utf8"));

// Build lookup map: normalized name → player summary index
function normName(name) {
  return name.toLowerCase()
    .normalize("NFD").replace(/[̀-ͯ]/g, "")  // strip accents
    .replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
}

const nameIndex = new Map();
for (let i = 0; i < summaries.length; i++) {
  nameIndex.set(normName(summaries[i].name), i);
}

// Also index by slug: "juan-manuel-cerundolo" → "juan manuel cerundolo"
function slugToName(slug) {
  return slug.replace(/-/g, " ");
}

let updated = 0;
let notFound = 0;

function processTourDir(tourPath, tour) {
  if (!fs.existsSync(tourPath)) return;
  const files = fs.readdirSync(tourPath).filter(f => f.endsWith(".json"));

  for (const file of files) {
    const slug = file.replace(".json", "");
    const tlData = JSON.parse(fs.readFileSync(path.join(tourPath, file), "utf8"));

    // Find matching player in summaries
    const tlName = tlData.name || slugToName(slug);
    let idx = nameIndex.get(normName(tlName));

    // Fallback: try slug-based name match
    if (idx === undefined) {
      idx = nameIndex.get(normName(slugToName(slug)));
    }

    // Fallback: partial last-name match
    if (idx === undefined) {
      const parts = normName(tlName).split(" ");
      const lastName = parts[parts.length - 1];
      for (const [k, v] of nameIndex) {
        if (k.endsWith(" " + lastName) || k === lastName) {
          // Verify first initial matches
          const first = parts[0]?.[0];
          const matchFirst = k.split(" ")[0]?.[0];
          if (!first || !matchFirst || first === matchFirst) {
            idx = v;
            break;
          }
        }
      }
    }

    if (idx === undefined) {
      notFound++;
      if (notFound <= 20) console.log(`  [not found] ${tlName} (${slug})`);
      continue;
    }

    const player = summaries[idx];
    let changed = false;

    // 1. Update ranking if TL has a fresher one
    if (tlData.ranking && (!player.rank || tlData.ranking !== player.rank)) {
      if (!DRY_RUN) player.rank = tlData.ranking;
      changed = true;
    }

    // 2. Update points if available
    if (tlData.points && tlData.points !== player.points) {
      if (!DRY_RUN) player.points = tlData.points;
    }

    // 3. Merge surface win rates from TennisLive byYear data
    // TL surface data is win/loss counts — we update winPct only, not serve stats
    if (tlData.byYear) {
      // Compute blended surface winPct using TL 2024-2026 data
      const surfaceAccum = {};
      const relevantYears = ["2024", "2025", "2026"];

      for (const year of relevantYears) {
        const yearData = tlData.byYear[year];
        if (!yearData) continue;
        for (const [surface, stats] of Object.entries(yearData)) {
          if (!surfaceAccum[surface]) {
            surfaceAccum[surface] = { wins: 0, losses: 0, matches: 0 };
          }
          surfaceAccum[surface].wins += stats.wins;
          surfaceAccum[surface].losses += stats.losses;
          surfaceAccum[surface].matches += stats.matches;
        }
      }

      for (const [surface, stats] of Object.entries(surfaceAccum)) {
        if (stats.matches < 5) continue; // not enough data
        const newWinPct = stats.wins / stats.matches;

        if (!player.surfaces) player.surfaces = {};
        if (!player.surfaces[surface]) {
          // TL has surface data Sackmann doesn't — add it
          if (!DRY_RUN) {
            player.surfaces[surface] = {
              matches: stats.matches,
              wins: stats.wins,
              losses: stats.losses,
              winPct: Math.round(newWinPct * 10000) / 10000,
            };
          }
          changed = true;
        } else {
          const existing = player.surfaces[surface];
          const existingWinPct = existing.winPct || 0;

          // Blend: TL recent (2024-2026) gets 60% weight, Sackmann career gets 40%
          // But only update winPct — never touch aceRate/dfRate/serve stats
          const blended = newWinPct * 0.6 + existingWinPct * 0.4;
          const rounded = Math.round(blended * 10000) / 10000;

          if (Math.abs(rounded - existingWinPct) > 0.005) {
            if (!DRY_RUN) {
              existing.winPct = rounded;
              // Update match counts to reflect TL recent data (additive)
              existing.wins = (existing.wins || 0) + stats.wins;
              existing.losses = (existing.losses || 0) + stats.losses;
              existing.matches = (existing.matches || 0) + stats.matches;
            }
            changed = true;
          }
        }
      }
    }

    // 4. Update overall winPct using TL 2026 current season if better sample
    if (tlData.careerWinPct && tlData.careerMatches > (player.matches || 0)) {
      if (!DRY_RUN) player.winPct = tlData.careerWinPct;
      changed = true;
    }

    if (changed) {
      updated++;
      if (DRY_RUN) {
        console.log(`  [would update] ${player.name} (${tour})`);
      }
    }
  }
}

console.log(`Merging TennisLive data into ${summaries.length} player summaries...`);
processTourDir(path.join(tlDir, "atp"), "ATP");
processTourDir(path.join(tlDir, "wta"), "WTA");

console.log(`\nResults: ${updated} players updated, ${notFound} TL profiles not matched`);

if (!DRY_RUN) {
  fs.writeFileSync(summariesPath, JSON.stringify(summaries, null, 2));
  console.log(`Saved updated player-summaries.json`);
} else {
  console.log(`(dry run — no files written)`);
}
