#!/usr/bin/env node
/**
 * Downloads the latest Sackmann CSVs from GitHub and re-imports if anything changed.
 * Run manually: node scripts/update-sackmann.mjs
 * Or triggered via POST /api/update-data
 */
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import https from "node:https";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const downloads = path.join(os.homedir(), "Downloads");
const workspace = process.cwd();

const FILES = [
  { label: "ATP 2026",       dest: "atp_matches_2026.csv",          url: "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2026.csv" },
  { label: "Challenger 2026",dest: "atp_matches_qual_chall_2026.csv",url: "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_qual_chall_2026.csv" },
  { label: "Futures 2026",   dest: "atp_matches_futures_2026.csv",   url: "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_futures_2026.csv" },
  { label: "WTA 2026",       dest: "wta_matches_2026.csv",           url: "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2026.csv" },
  { label: "ITF Women 2026", dest: "wta_matches_qual_itf_2026.csv",  url: "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_qual_itf_2026.csv" },
  { label: "ATP Rankings",   dest: "atp_rankings_current.csv",       url: "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_rankings_current.csv" },
  { label: "WTA Rankings",   dest: "wta_rankings_current.csv",       url: "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_rankings_current.csv" },
];

function fetchText(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "AstroTennis/1.0" } }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return resolve(fetchText(res.headers.location));
      }
      if (res.statusCode !== 200) return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
      res.on("error", reject);
    }).on("error", reject);
  });
}

function rowCount(text) {
  return text.trim().split("\n").length - 1; // subtract header
}

function latestDate(text) {
  const lines = text.trim().split("\n");
  const header = lines[0].split(",");
  const di = header.indexOf("tourney_date");
  if (di < 0) return null;
  const dates = lines.slice(1).map((l) => l.split(",")[di]).filter(Boolean);
  return dates.length ? dates.sort().at(-1) : null;
}

fs.mkdirSync(downloads, { recursive: true });

let anyUpdated = false;
const results = [];

for (const { label, dest, url } of FILES) {
  const destPath = path.join(downloads, dest);
  let remote;
  try {
    remote = await fetchText(url);
  } catch (e) {
    results.push({ label, status: "fetch_failed", error: e.message });
    continue;
  }

  const remoteRows = rowCount(remote);
  const remoteDate = latestDate(remote);

  let localRows = 0;
  if (fs.existsSync(destPath)) {
    const local = fs.readFileSync(destPath, "utf8");
    localRows = rowCount(local);
  }

  if (remoteRows > localRows) {
    fs.writeFileSync(destPath, remote);
    anyUpdated = true;
    results.push({ label, status: "updated", localRows, remoteRows, latestDate: remoteDate });
  } else {
    results.push({ label, status: "current", rows: remoteRows, latestDate: remoteDate });
  }
}

let importResult = null;
if (anyUpdated) {
  try {
    const { stdout } = await execFileAsync("node", [path.join(workspace, "scripts", "import-sackmann.mjs")], {
      cwd: workspace, timeout: 120000
    });
    importResult = stdout.trim();
  } catch (e) {
    importResult = `Import error: ${e.message}`;
  }
}

console.log(JSON.stringify({ results, anyUpdated, importResult }));
