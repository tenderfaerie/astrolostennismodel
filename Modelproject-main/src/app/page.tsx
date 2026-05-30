"use client";

import { Activity, BarChart3, BookOpen, Calendar, CheckCircle, PlusCircle, Radio, Search, ShieldCheck, Trash2, TrendingUp } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BetRecord, H2HRecord, LiveMatch, PlayerSummary, PropProjection, Tour } from "@/lib/types";
import { propCategories } from "@/lib/prop-model";

type Tab = "live" | "upcoming" | "finished" | "props" | "players" | "tracker";
const SURFACES = ["All", "Hard", "Clay", "Grass", "Indoor"];
const TOUR_LABELS: Tour[] = ["ATP", "WTA", "ITF Women", "Challenger", "Futures"];

// ─── Formatters ──────────────────────────────────────────────────────────────

function pct(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${Math.round(value * 100)}%`;
}
function money(value?: number | null) {
  if (value == null) return "—";
  return value > 0 ? `+${value}` : String(value);
}
function formatTime(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}
function formatDate(ts?: number) {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleDateString([], { month: "short", day: "numeric" });
}
function americanToProbability(v?: number | null) {
  if (!v) return null;
  return v > 0 ? 100 / (v + 100) : Math.abs(v) / (Math.abs(v) + 100);
}
function uid() {
  return Math.random().toString(36).slice(2, 10);
}

// ─── Tour colours ────────────────────────────────────────────────────────────

function tourColor(tour: string): string {
  if (tour === "ATP") return "var(--blue)";
  if (tour === "WTA") return "#e87eff";
  if (tour === "ITF Men" || tour === "ITF Women") return "var(--gold)";
  if (tour === "Challenger") return "#56d4c0";
  return "var(--muted)";
}
function TourBadge({ tour }: { tour: string }) {
  return <span className="tourBadge" style={{ borderColor: tourColor(tour), color: tourColor(tour) }}>{tour}</span>;
}

// ─── Live match helpers ───────────────────────────────────────────────────────

function statNumber(match: LiveMatch, key: string, side: "home" | "away") {
  const stat = match.stats?.find((s) => s.key === key);
  const raw = stat?.[side];
  if (typeof raw === "number") return raw;
  if (typeof raw === "string") {
    const n = Number(raw.match(/-?\d+(\.\d+)?/)?.[0]);
    return Number.isFinite(n) ? n : 0;
  }
  return 0;
}
function estimateWinner(match: LiveMatch) {
  const hm = americanToProbability(match.moneyline?.home?.american);
  const am = americanToProbability(match.moneyline?.away?.american);
  const mt = (hm ?? 0) + (am ?? 0);
  const nhm = mt > 0 ? (hm ?? 0) / mt : null;
  let s = 0.5;
  s += ((match.homeScore ?? 0) - (match.awayScore ?? 0)) * 0.12;
  const ls = match.periodScores.at(-1);
  if (ls?.home != null && ls?.away != null) s += ((ls.home ?? 0) - (ls.away ?? 0)) * 0.018;
  if (match.server === "home") s += 0.025; else if (match.server === "away") s -= 0.025;
  s += (statNumber(match, "aces", "home") - statNumber(match, "aces", "away")) * 0.006;
  s -= (statNumber(match, "doubleFaults", "home") - statNumber(match, "doubleFaults", "away")) * 0.008;
  s += (statNumber(match, "breakPointsScored", "home") - statNumber(match, "breakPointsScored", "away")) * 0.018;
  if (nhm !== null) s = s * 0.42 + nhm * 0.58;
  const hProb = Math.max(0.05, Math.min(0.95, s));
  return { winner: hProb >= 0.5 ? match.homePlayer : match.awayPlayer, hProb, aProb: 1 - hProb, hMkt: nhm, aMkt: nhm == null ? null : 1 - nhm };
}

const STAT_KEYS = ["aces","doubleFaults","firstServeAccuracy","firstServePointsAccuracy","secondServePointsAccuracy","breakPointsSaved","breakPointsScored","servicePointsScored","receiverPointsScored","winnersTotal","unforcedErrorsTotal","tiebreaks"];

// ─── EV display ──────────────────────────────────────────────────────────────

function EVPanel({ proj }: { proj: PropProjection }) {
  if (proj.ev == null) return null;
  const positive = proj.ev > 0;
  return (
    <div className={`evPanel ${positive ? "evPositive" : "evNegative"}`}>
      <div className="evCell">
        <span className="muted">Expected Value</span>
        <strong className={positive ? "edgePositive" : "edgeNegative"}>{positive ? "+" : ""}{proj.ev}%</strong>
      </div>
      <div className="evCell">
        <span className="muted">Model Prob</span>
        <strong>{proj.modelProb}%</strong>
      </div>
      <div className="evCell">
        <span className="muted">Implied Prob</span>
        <strong>{proj.impliedProb}%</strong>
      </div>
      <div className="evCell">
        <span className="muted">Kelly Stake</span>
        <strong>{proj.kellyPct}% bankroll</strong>
      </div>
    </div>
  );
}

// ─── Parlay builder ───────────────────────────────────────────────────────────

function ParlayBuilder({ items, onRemove }: { items: PropProjection[]; onRemove: (i: number) => void }) {
  if (items.length === 0) return null;

  const combinedModelProb = items.reduce((acc, p) => acc * ((p.modelProb ?? p.confidence) / 100), 1);
  const decimalOdds = items.map((p) => {
    if (!p.americanOdds) return null;
    return p.americanOdds > 0 ? p.americanOdds / 100 + 1 : 100 / Math.abs(p.americanOdds) + 1;
  });
  const allHaveOdds = decimalOdds.every((o) => o !== null);
  const parlayDecimal = allHaveOdds ? decimalOdds.reduce((a, b) => a! * b!, 1)! : null;
  const parlayAmerican = parlayDecimal == null ? null : parlayDecimal >= 2 ? Math.round((parlayDecimal - 1) * 100) : Math.round(-100 / (parlayDecimal - 1));
  const parlayEV = parlayDecimal != null ? (combinedModelProb * (parlayDecimal - 1) - (1 - combinedModelProb)) * 100 : null;

  return (
    <div className="parlayBox">
      <div className="parlayHeader">
        <strong><TrendingUp size={14} /> Parlay Builder</strong>
        <span className="pill">{items.length} leg{items.length > 1 ? "s" : ""}</span>
      </div>
      {!allHaveOdds ? (
        <div className="parlayWarning">⚠ Add book odds to each leg to see parlay EV and combined payout.</div>
      ) : null}
      {items.map((p, i) => (
        <div className="parlayLeg" key={i}>
          <span>{p.player} · {p.market} {p.side} {p.line}</span>
          {p.americanOdds ? <span className="muted">{money(p.americanOdds)}</span> : <span className="muted oddsHint">no odds</span>}
          <button className="removeBtn" onClick={() => onRemove(i)}><Trash2 size={12} /></button>
        </div>
      ))}
      <div className="parlayStats">
        <div className="evCell">
          <span className="muted">Combined Prob</span>
          <strong>{Math.round(combinedModelProb * 100)}%</strong>
        </div>
        {parlayAmerican != null ? (
          <div className="evCell">
            <span className="muted">Parlay Odds</span>
            <strong>{money(parlayAmerican)}</strong>
          </div>
        ) : null}
        {parlayEV != null ? (
          <div className="evCell">
            <span className="muted">Parlay EV</span>
            <strong className={parlayEV > 0 ? "edgePositive" : "edgeNegative"}>{parlayEV > 0 ? "+" : ""}{parlayEV.toFixed(1)}%</strong>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// ─── Match card ───────────────────────────────────────────────────────────────

function PredictionStrip({ match }: { match: LiveMatch }) {
  const p = estimateWinner(match);
  const ws = p.hProb >= 0.5 ? "home" : "away";
  return (
    <div className="predictionStrip">
      <div><span className="muted">Projected Winner</span><strong>{p.winner}</strong></div>
      <div><span className="muted">Astro Model</span><strong>{Math.round(Math.max(p.hProb, p.aProb) * 100)}%</strong></div>
      <div><span className="muted">Market</span><strong>{p.hMkt == null ? "—" : `${Math.round(Math.max(p.hMkt, p.aMkt ?? 0) * 100)}%`}</strong></div>
      <div><span className="muted">Lean</span><strong className={ws === "home" ? "edgePositive" : "edgeNegative"}>{ws === "home" ? "Home" : "Away"}</strong></div>
    </div>
  );
}

function MatchCard({ match, showTime }: { match: LiveMatch; showTime?: boolean }) {
  return (
    <article className="match">
      <div className="matchTop">
        <div>
          <strong>{match.tournament}</strong>
          <div className="muted">{match.category}{match.round ? ` • ${match.round}` : ""}{match.surface && match.surface !== "Unknown" ? ` • ${match.surface}` : ""}</div>
        </div>
        {showTime && match.startTimestamp
          ? <span className="timeChip">{formatDate(match.startTimestamp)} {formatTime(match.startTimestamp)}</span>
          : <span className="pill">{match.status}</span>}
      </div>
      {match.statusType === "inprogress" ? <PredictionStrip match={match} /> : null}
      <div className="scoreline">
        <div>
          <div className={match.server === "home" ? "servingPlayer" : ""}>{match.homePlayer}{match.server === "home" ? <span className="serveDot" /> : null}</div>
          <div className={match.server === "away" ? "servingPlayer" : ""}>{match.awayPlayer}{match.server === "away" ? <span className="serveDot" /> : null}</div>
        </div>
        <div className="sets">
          {match.periodScores.length ? match.periodScores.map((s) => (
            <div className="setBox" key={s.period}><div>{s.home ?? "–"}</div><div>{s.away ?? "–"}</div></div>
          )) : match.homeScore !== undefined ? (
            <div className="setBox"><div>{match.homeScore ?? "–"}</div><div>{match.awayScore ?? "–"}</div></div>
          ) : null}
        </div>
      </div>
      {match.moneyline ? (
        <div className="oddsRow">
          <span className="muted">Moneyline</span>
          <strong>{money(match.moneyline.home?.american)}</strong>
          <strong>{money(match.moneyline.away?.american)}</strong>
          {match.moneyline.suspended ? <span className="muted">Suspended</span> : null}
        </div>
      ) : null}
      {match.stats?.length ? (
        <div className="liveStats">
          {match.stats.filter((s) => STAT_KEYS.includes(s.key ?? "")).slice(0, 12).map((s) => (
            <div className="liveStat" key={`${match.providerId}-${s.key ?? s.name}`}>
              <span>{s.home ?? "—"}</span><em>{s.name}</em><span>{s.away ?? "—"}</span>
            </div>
          ))}
        </div>
      ) : null}
      {match.currentGame?.points.length ? (
        <div className="pointPanel">
          <div className="pointHeader"><strong>Point by Point</strong><span className="muted">Set {match.currentGame.set}, Game {match.currentGame.game}</span></div>
          <div className="pointList">
            {match.currentGame.points.slice(-8).map((pt, i) => (
              <div className="pointRow" key={i}>
                <span className={pt.winner === "home" ? "pointWon" : ""}>{pt.homePoint}</span>
                <em>{i + 1}</em>
                <span className={pt.winner === "away" ? "pointWon" : ""}>{pt.awayPoint}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </article>
  );
}

function MatchList({ matches, emptyMessage, tourFilter, warning, showTime }: {
  matches: LiveMatch[]; emptyMessage: string; tourFilter: string; warning?: string; showTime?: boolean;
}) {
  const filtered = tourFilter ? matches.filter((m) => m.category?.toLowerCase().includes(tourFilter.toLowerCase())) : matches;
  return (
    <>
      {warning ? <div className="providerWarning">SofaScore blocked the server request — prototype placeholders shown.</div> : null}
      {filtered.length === 0
        ? <div className="match"><strong>{emptyMessage}</strong><p className="muted">{tourFilter ? `No ${tourFilter} matches. Clear the filter to see all.` : "Check back soon."}</p></div>
        : filtered.slice(0, 30).map((m) => <MatchCard key={m.providerId} match={m} showTime={showTime} />)}
    </>
  );
}

// ─── Player card ──────────────────────────────────────────────────────────────

function formWinPct(player: PlayerSummary) {
  const r = player.recentMatches?.slice(0, 10) ?? [];
  if (r.length < 3) return null;
  return r.filter((m) => m.result === "W").length / r.length;
}

function PlayerCard({ player, onSelect, selected }: { player: PlayerSummary; onSelect?: () => void; selected?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const surfaces = Object.entries(player.surfaces ?? {}).filter(([, v]) => v.matches > 0);
  const form = formWinPct(player);

  return (
    <article className={`player ${selected ? "playerSelected" : ""}`}>
      <div className="playerTop">
        <div>
          <strong>{player.name}</strong>
          <div className="playerMeta">
            <TourBadge tour={player.tour} />
            <span className="muted">{player.country ?? "—"}</span>
            {player.rank ? <span className="muted">Rank {player.rank}</span> : null}
            {form != null ? <span className="formBadge" style={{ color: form >= 0.6 ? "var(--green)" : form <= 0.4 ? "var(--red)" : "var(--gold)" }}>L10: {pct(form)}</span> : null}
          </div>
        </div>
        <div className="playerTopRight">
          <span className="pill">{pct(player.winPct)}</span>
          {onSelect ? <button className={`selectBtn ${selected ? "selectBtnActive" : ""}`} onClick={onSelect}>{selected ? "✓" : "Select"}</button> : null}
          <button className="expandBtn" onClick={() => setExpanded((v) => !v)}>{expanded ? "▲" : "▼"}</button>
        </div>
      </div>
      <div className="statGrid">
        <div className="stat"><span className="muted">Ace %</span><strong>{pct(player.aceRate)}</strong></div>
        <div className="stat"><span className="muted">DF %</span><strong>{pct(player.dfRate)}</strong></div>
        <div className="stat"><span className="muted">1st Srv %</span><strong>{pct(player.firstServePct)}</strong></div>
        <div className="stat"><span className="muted">1st Won</span><strong>{pct(player.firstServeWonPct)}</strong></div>
        <div className="stat"><span className="muted">2nd Won</span><strong>{pct(player.secondServeWonPct)}</strong></div>
        <div className="stat"><span className="muted">BP Saved</span><strong>{pct(player.bpSavedPct)}</strong></div>
      </div>
      {expanded ? (
        <>
          {surfaces.length > 0 ? (
            <div className="surfaceSection">
              <div className="surfaceHeader muted">Surface Breakdown</div>
              <div className="surfaceGrid">
                {surfaces.map(([surf, s]) => (
                  <div className="surfaceCell" key={surf}>
                    <span className="muted">{surf}</span>
                    <strong>{pct(s.winPct)}</strong>
                    <span className="muted">{s.wins}W {s.losses}L</span>
                    {s.aceRate != null ? <span className="muted">Ace {pct(s.aceRate)}</span> : null}
                    {s.dfRate != null ? <span className="muted">DF {pct(s.dfRate)}</span> : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {player.recentMatches?.length ? (
            <div className="recentSection">
              <div className="surfaceHeader muted">Recent Matches</div>
              {player.recentMatches.slice(0, 5).map((m, i) => (
                <div className="recentRow" key={i}>
                  <span className={m.result === "W" ? "resultW" : "resultL"}>{m.result}</span>
                  <span>{m.opponent}</span>
                  <span className="muted">{m.surface}</span>
                  <span className="muted recentScore">{m.score}</span>
                  <span className="muted">{m.date?.slice(0, 7)}</span>
                </div>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </article>
  );
}

// ─── H2H + Matchup panel ──────────────────────────────────────────────────────

function MatchupPanel({ data, p1, p2 }: { data: H2HRecord; p1: PlayerSummary; p2: PlayerSummary }) {
  const statRows: { label: string; key: keyof PlayerSummary }[] = [
    { label: "Win %", key: "winPct" },
    { label: "Ace %", key: "aceRate" },
    { label: "DF %", key: "dfRate" },
    { label: "1st Serve %", key: "firstServePct" },
    { label: "1st Srv Won", key: "firstServeWonPct" },
    { label: "2nd Srv Won", key: "secondServeWonPct" },
    { label: "BP Saved", key: "bpSavedPct" },
  ];

  return (
    <div className="matchupPanel">
      {/* H2H banner */}
      <div className="h2hBanner">
        <div className="h2hSide">
          <strong>{data.player1Name}</strong>
          <TourBadge tour={p1.tour} />
        </div>
        <div className="h2hScore">
          <span className="h2hNum">{data.player1Wins}</span>
          <span className="muted">–</span>
          <span className="h2hNum">{data.player2Wins}</span>
          <div className="muted" style={{ fontSize: 12 }}>{data.totalMatches} meetings</div>
        </div>
        <div className="h2hSide h2hRight">
          <strong>{data.player2Name}</strong>
          <TourBadge tour={p2.tour} />
        </div>
      </div>

      {/* Surface H2H */}
      {Object.keys(data.bySurface).length > 0 ? (
        <div className="h2hSurfaces">
          {Object.entries(data.bySurface).map(([surf, rec]) => (
            <div className="h2hSurfRow" key={surf}>
              <span className="muted">{surf}</span>
              <strong>{rec.player1Wins}</strong>
              <span className="muted">–</span>
              <strong>{rec.player2Wins}</strong>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted" style={{ padding: "12px 16px", fontSize: 13 }}>
          No H2H meeting data yet. Re-run <code>npm run import:sackmann</code> after downloading Sackmann CSVs to populate full history.
        </p>
      )}

      {/* Recent meetings */}
      {data.meetings.length > 0 ? (
        <div className="h2hMeetings">
          <div className="surfaceHeader muted" style={{ padding: "10px 16px 4px" }}>Recent Meetings</div>
          {data.meetings.slice(0, 6).map((m, i) => (
            <div className="h2hMeetingRow" key={i}>
              <span className="muted">{m.date?.slice(0, 7)}</span>
              <span>{m.tournament}</span>
              <span className="muted">{m.surface}</span>
              <strong>{m.winner}</strong>
              <span className="muted recentScore">{m.score}</span>
            </div>
          ))}
        </div>
      ) : null}

      {/* Side-by-side stats */}
      <div className="h2hStatTable">
        <div className="surfaceHeader muted" style={{ padding: "10px 16px 4px" }}>Head-to-Head Stats</div>
        <div className="h2hStatHeader">
          <span>{p1.name.split(" ").at(-1)}</span>
          <span className="muted">Stat</span>
          <span>{p2.name.split(" ").at(-1)}</span>
        </div>
        {statRows.map(({ label, key }) => {
          const v1 = p1[key] as number | null;
          const v2 = p2[key] as number | null;
          const better1 = v1 != null && v2 != null && v1 > v2;
          const better2 = v1 != null && v2 != null && v2 > v1;
          return (
            <div className="h2hStatRow" key={key}>
              <span className={better1 ? "edgePositive" : ""}>{pct(v1)}</span>
              <span className="muted">{label}</span>
              <span className={better2 ? "edgePositive" : ""}>{pct(v2)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Bet tracker ──────────────────────────────────────────────────────────────

function BetTrackerTab({ players }: { players: PlayerSummary[] }) {
  const [bets, setBets] = useState<BetRecord[]>([]);
  const [tab, setTab] = useState<"open" | "settled">("open");
  const [player, setPlayer] = useState("");
  const [opponent, setOpponent] = useState("");
  const [market, setMarket] = useState("aces");
  const [line, setLine] = useState("");
  const [side, setSide] = useState<"Over" | "Under">("Over");
  const [odds, setOdds] = useState("");
  const [stake, setStake] = useState("");

  useEffect(() => {
    try { setBets(JSON.parse(localStorage.getItem("astrotennis-bets") ?? "[]")); } catch {}
  }, []);
  useEffect(() => {
    try { localStorage.setItem("astrotennis-bets", JSON.stringify(bets)); } catch {}
  }, [bets]);

  function addBet() {
    if (!player || !line || !odds || !stake) return;
    const newBet: BetRecord = {
      id: uid(),
      placedAt: new Date().toISOString(),
      player, opponent: opponent || undefined,
      market: propCategories.find((c) => c.id === market)?.label ?? market,
      line: Number(line), side,
      americanOdds: Number(odds),
      stake: Number(stake),
      status: "open"
    };
    setBets((prev) => [newBet, ...prev]);
    setPlayer(""); setOpponent(""); setLine(""); setOdds(""); setStake("");
  }

  function settle(id: string, status: "won" | "lost" | "void") {
    setBets((prev) => prev.map((b) => b.id === id ? { ...b, status } : b));
  }
  function remove(id: string) {
    setBets((prev) => prev.filter((b) => b.id !== id));
  }

  function exportCsv() {
    const header = ["Date", "Player", "Opponent", "Market", "Line", "Side", "Odds", "Stake", "Status", "Projection", "EV"];
    const rows = bets.map((b) => [
      new Date(b.placedAt).toLocaleDateString(),
      b.player, b.opponent ?? "",
      b.market, b.line, b.side,
      b.americanOdds, b.stake, b.status,
      b.projection ?? "", b.ev ?? ""
    ]);
    const csv = [header, ...rows].map((r) => r.map((v) => `"${v}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "astrotennis-bets.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  const open = bets.filter((b) => b.status === "open");
  const settled = bets.filter((b) => b.status !== "open");

  const totalStaked = settled.reduce((a, b) => a + b.stake, 0);
  const totalReturn = settled.reduce((a, b) => {
    if (b.status === "void") return a + b.stake;
    if (b.status === "won") {
      const profit = b.americanOdds > 0 ? b.stake * b.americanOdds / 100 : b.stake * 100 / Math.abs(b.americanOdds);
      return a + b.stake + profit;
    }
    return a;
  }, 0);
  const profit = totalReturn - totalStaked;
  const roi = totalStaked > 0 ? (profit / totalStaked) * 100 : 0;
  const wins = settled.filter((b) => b.status === "won").length;
  const losses = settled.filter((b) => b.status === "lost").length;

  return (
    <section className="section fullWidth">
      <div className="sectionHeader">
        <h2><BookOpen size={16} /> Bet Tracker</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className="pill">{open.length} open</span>
          {bets.length > 0 ? <button className="secondaryButton" style={{ padding: "4px 10px", fontSize: 12 }} onClick={exportCsv}>Export CSV</button> : null}
        </div>
      </div>

      {/* P&L summary */}
      {settled.length > 0 ? (
        <div className="plSummary">
          <div className="plCell">
            <span className="muted">P&amp;L</span>
            <strong className={profit >= 0 ? "edgePositive" : "edgeNegative"}>{profit >= 0 ? "+" : ""}{profit.toFixed(2)}</strong>
          </div>
          <div className="plCell">
            <span className="muted">ROI</span>
            <strong className={roi >= 0 ? "edgePositive" : "edgeNegative"}>{roi >= 0 ? "+" : ""}{roi.toFixed(1)}%</strong>
          </div>
          <div className="plCell">
            <span className="muted">Record</span>
            <strong>{wins}W – {losses}L</strong>
          </div>
          <div className="plCell">
            <span className="muted">Staked</span>
            <strong>{totalStaked.toFixed(2)}</strong>
          </div>
        </div>
      ) : null}

      {/* Add bet form */}
      <div className="betForm">
        <div className="betFormTitle muted">Log a Bet</div>
        <div className="betFormGrid">
          <label>Player<input list="tracker-players" value={player} onChange={(e) => setPlayer(e.target.value)} placeholder="Player name" /></label>
          <label>Opponent<input list="tracker-players" value={opponent} onChange={(e) => setOpponent(e.target.value)} placeholder="Optional" /></label>
          <label>Market
            <select value={market} onChange={(e) => setMarket(e.target.value)}>
              {propCategories.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
            </select>
          </label>
          <label>Line<input value={line} inputMode="decimal" onChange={(e) => setLine(e.target.value)} placeholder="4.5" /></label>
          <label>Side
            <select value={side} onChange={(e) => setSide(e.target.value as "Over" | "Under")}>
              <option value="Over">Over</option>
              <option value="Under">Under</option>
            </select>
          </label>
          <label>Am. Odds<input value={odds} inputMode="numeric" onChange={(e) => setOdds(e.target.value)} placeholder="-110" /></label>
          <label>Stake ($)<input value={stake} inputMode="decimal" onChange={(e) => setStake(e.target.value)} placeholder="10" /></label>
          <button className="primaryButton betAddBtn" onClick={addBet}><PlusCircle size={14} /> Add Bet</button>
        </div>
        <datalist id="tracker-players">
          {players.slice(0, 200).map((p) => <option key={p.playerId} value={p.name} />)}
        </datalist>
      </div>

      {/* Tabs */}
      <div className="betTabs">
        <button className={tab === "open" ? "betTab active" : "betTab"} onClick={() => setTab("open")}>Open ({open.length})</button>
        <button className={tab === "settled" ? "betTab active" : "betTab"} onClick={() => setTab("settled")}>Settled ({settled.length})</button>
      </div>

      {/* Bet list */}
      {(tab === "open" ? open : settled).length === 0 ? (
        <div className="match"><strong>No {tab} bets</strong><p className="muted">Bets are saved in your browser.</p></div>
      ) : (
        (tab === "open" ? open : settled).map((b) => (
          <article className="betRow" key={b.id}>
            <div className="betRowTop">
              <div>
                <strong>{b.player}{b.opponent ? ` vs ${b.opponent}` : ""}</strong>
                <div className="muted">{b.market} {b.side} {b.line} · {money(b.americanOdds)} · ${b.stake}</div>
              </div>
              <div className="betRowStatus">
                {b.status === "open" ? (
                  <>
                    <button className="settleBtn won" onClick={() => settle(b.id, "won")}>W</button>
                    <button className="settleBtn lost" onClick={() => settle(b.id, "lost")}>L</button>
                    <button className="settleBtn void" onClick={() => settle(b.id, "void")}>V</button>
                  </>
                ) : (
                  <span className={`statusChip ${b.status}`}>{b.status.toUpperCase()}</span>
                )}
                <button className="removeBtn" onClick={() => remove(b.id)}><Trash2 size={12} /></button>
              </div>
            </div>
            <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>{new Date(b.placedAt).toLocaleDateString()}</div>
          </article>
        ))
      )}
    </section>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("live");

  // Matches
  const [liveMatches, setLiveMatches] = useState<LiveMatch[]>([]);
  const [upcomingMatches, setUpcomingMatches] = useState<LiveMatch[]>([]);
  const [finishedMatches, setFinishedMatches] = useState<LiveMatch[]>([]);
  const [finishedDaysBack, setFinishedDaysBack] = useState(14);
  const [liveWarning, setLiveWarning] = useState("");
  const [upcomingWarning, setUpcomingWarning] = useState("");
  const [finishedWarning, setFinishedWarning] = useState("");
  const [lastRefresh, setLastRefresh] = useState("");
  const [matchTourFilter, setMatchTourFilter] = useState("");

  // Players
  const [players, setPlayers] = useState<PlayerSummary[]>([]);
  const [query, setQuery] = useState("");
  const [playerTourFilter, setPlayerTourFilter] = useState("");
  const [compareMode, setCompareMode] = useState(false);
  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]);
  const [matchupData, setMatchupData] = useState<{ record: H2HRecord; player1: PlayerSummary; player2: PlayerSummary } | null>(null);
  const [matchupLoading, setMatchupLoading] = useState(false);

  // Props
  const [propPlayer, setPropPlayer] = useState("Carlos Alcaraz");
  const [propOpponent, setPropOpponent] = useState("Jannik Sinner");
  const [propMarket, setPropMarket] = useState("aces");
  const [propLine, setPropLine] = useState("4.5");
  const [propOdds, setPropOdds] = useState("");
  const [propSurface, setPropSurface] = useState("All");
  const [useForm, setUseForm] = useState(false);
  const [propText, setPropText] = useState("Carlos Alcaraz aces over 4.5\nIga Swiatek games won over 12.5");
  const [projections, setProjections] = useState<PropProjection[]>([]);
  const [parlayItems, setParlayItems] = useState<PropProjection[]>([]);
  const [minConfidence, setMinConfidence] = useState(0);
  const [propTourFilter, setPropTourFilter] = useState("");
  const [bankroll, setBankroll] = useState("");
  const [kellyFraction, setKellyFraction] = useState(0.25);

  // Reset compare mode when leaving players tab
  useEffect(() => {
    if (activeTab !== "players") {
      setCompareMode(false);
      setSelectedPlayers([]);
      setMatchupData(null);
    }
  }, [activeTab]);

  // Live auto-refresh
  const loadLive = useCallback(async () => {
    try {
      const d = await fetch("/api/live", { cache: "no-store" }).then((r) => r.json());
      setLiveMatches(d.matches ?? []);
      setLiveWarning(d.warning ?? "");
      setLastRefresh(new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" }));
    } catch {}
  }, []);

  useEffect(() => { loadLive(); const t = setInterval(loadLive, 15000); return () => clearInterval(t); }, [loadLive]);

  useEffect(() => {
    if (activeTab !== "upcoming") return;
    fetch("/api/live?type=upcoming", { cache: "no-store" }).then((r) => r.json()).then((d) => { setUpcomingMatches(d.matches ?? []); setUpcomingWarning(d.warning ?? ""); }).catch(() => {});
  }, [activeTab]);

  useEffect(() => {
    if (activeTab !== "finished") return;
    fetch(`/api/live?type=finished&daysBack=${finishedDaysBack}`, { cache: "no-store" }).then((r) => r.json()).then((d) => { setFinishedMatches(d.matches ?? []); setFinishedWarning(d.warning ?? ""); }).catch(() => {});
  }, [activeTab, finishedDaysBack]);

  useEffect(() => {
    fetch(`/api/players?q=${encodeURIComponent(query)}`).then((r) => r.json()).then((d) => setPlayers(d.players ?? [])).catch(() => {});
  }, [query]);

  // Matchup fetch
  useEffect(() => {
    if (selectedPlayers.length !== 2) { setMatchupData(null); return; }
    setMatchupLoading(true);
    fetch(`/api/h2h?p1=${encodeURIComponent(selectedPlayers[0])}&p2=${encodeURIComponent(selectedPlayers[1])}`)
      .then((r) => r.json())
      .then((d) => setMatchupData(d.record ? d : null))
      .catch(() => setMatchupData(null))
      .finally(() => setMatchupLoading(false));
  }, [selectedPlayers]);

  const filteredPlayers = useMemo(
    () => playerTourFilter ? players.filter((p) => p.tour === playerTourFilter) : players,
    [players, playerTourFilter]
  );

  const propPlayerOptions = useMemo(
    () => propTourFilter ? players.filter((p) => p.tour === propTourFilter) : players,
    [players, propTourFilter]
  );

  const filteredProjections = useMemo(
    () => minConfidence > 0 ? projections.filter((p) => p.confidence >= minConfidence) : projections,
    [projections, minConfidence]
  );

  function toggleSelectPlayer(name: string) {
    setSelectedPlayers((prev) => {
      if (prev.includes(name)) return prev.filter((n) => n !== name);
      if (prev.length >= 2) return [prev[1], name];
      return [...prev, name];
    });
  }

  async function analyzeStructuredProp() {
    const body: Record<string, unknown> = { player: propPlayer, opponent: propOpponent, market: propMarket, line: Number(propLine), surface: propSurface, useForm };
    if (propOdds && Number.isFinite(Number(propOdds))) body.americanOdds = Number(propOdds);
    const d = await fetch("/api/props", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }).then((r) => r.json());
    setProjections(d.projections ?? []);
  }

  async function analyzePasted() {
    const d = await fetch("/api/props", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: propText }) }).then((r) => r.json());
    setProjections(d.projections ?? []);
  }

  function addToParlay(proj: PropProjection) {
    setParlayItems((prev) => [...prev, proj]);
  }
  function removeFromParlay(i: number) {
    setParlayItems((prev) => prev.filter((_, idx) => idx !== i));
  }

  const tabLabel: Record<Tab, string> = { live: "Live Matches", upcoming: "Upcoming", finished: "Finished", props: "Prop Analyzer", players: "Players & Matchup", tracker: "Bet Tracker" };
  const matchTabs = activeTab === "live" || activeTab === "upcoming" || activeTab === "finished";

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="brandMark" aria-hidden="true"><span /></div>AstroTennis</div>
        <nav className="nav" aria-label="Primary">
          {(["live","upcoming","finished","props","players","tracker"] as Tab[]).map((t) => {
            const icons: Record<Tab, React.ReactNode> = { live: <Radio size={15} />, upcoming: <Calendar size={15} />, finished: <CheckCircle size={15} />, props: <ShieldCheck size={15} />, players: <Search size={15} />, tracker: <BookOpen size={15} /> };
            return <button key={t} className={activeTab === t ? "active" : ""} onClick={() => setActiveTab(t)}>{icons[t]} {tabLabel[t]}</button>;
          })}
        </nav>
      </aside>

      <main className="main">
        <div className="topbar">
          <div>
            <h1>{tabLabel[activeTab]}</h1>
            <p>ATP · WTA · ITF Men · ITF Women · Challenger · Futures</p>
          </div>
          {activeTab === "players" ? (
            <input className="search" placeholder="Search players" value={query} onChange={(e) => setQuery(e.target.value)} />
          ) : null}
        </div>

        {matchTabs ? (
          <div className="filterRow">
            <button className={matchTourFilter === "" ? "filterPill active" : "filterPill"} onClick={() => setMatchTourFilter("")}>All Tours</button>
            {["ATP","WTA","ITF","Challenger"].map((t) => (
              <button key={t} className={matchTourFilter === t ? "filterPill active" : "filterPill"} onClick={() => setMatchTourFilter(matchTourFilter === t ? "" : t)}>{t}</button>
            ))}
          </div>
        ) : null}

        {activeTab === "players" ? (
          <div className="filterRow">
            <button className={playerTourFilter === "" ? "filterPill active" : "filterPill"} onClick={() => setPlayerTourFilter("")}>All</button>
            {TOUR_LABELS.map((t) => (
              <button key={t} className={playerTourFilter === t ? "filterPill active" : "filterPill"} style={playerTourFilter === t ? { borderColor: tourColor(t), color: tourColor(t) } : {}} onClick={() => setPlayerTourFilter(playerTourFilter === t ? "" : t)}>{t}</button>
            ))}
            <button className={`filterPill ${compareMode ? "active" : ""}`} style={compareMode ? { borderColor: "var(--gold)", color: "var(--gold)" } : {}} onClick={() => { setCompareMode((v) => !v); setSelectedPlayers([]); setMatchupData(null); }}>
              {compareMode ? "✓ Compare Mode" : "Compare Players"}
            </button>
          </div>
        ) : null}

        <div className="grid">

          {/* ── Live ── */}
          {activeTab === "live" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><Activity size={16} /> Live</h2>
                <span className="pill">{lastRefresh ? `Updated ${lastRefresh}` : "Auto-refresh 15s"}</span>
              </div>
              <MatchList matches={liveMatches} emptyMessage="No live matches right now" tourFilter={matchTourFilter} warning={liveWarning || undefined} />
            </section>
          ) : null}

          {/* ── Upcoming ── */}
          {activeTab === "upcoming" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><Calendar size={16} /> Upcoming — Today &amp; Tomorrow</h2>
                <span className="pill">{upcomingMatches.length} scheduled</span>
              </div>
              <MatchList matches={upcomingMatches} emptyMessage="No upcoming matches loaded" tourFilter={matchTourFilter} warning={upcomingWarning || undefined} showTime />
            </section>
          ) : null}

          {/* ── Finished ── */}
          {activeTab === "finished" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><CheckCircle size={16} /> Finished Results</h2>
                <span className="pill">{finishedMatches.length} results · last {finishedDaysBack}d</span>
              </div>
              <div className="filterRow">
                <span className="muted" style={{ fontSize: 12, marginRight: 4 }}>Show last:</span>
                {[3, 7, 14, 21, 30].map((d) => (
                  <button key={d} className={finishedDaysBack === d ? "filterPill active" : "filterPill"} onClick={() => setFinishedDaysBack(d)}>{d}d</button>
                ))}
              </div>
              <MatchList matches={finishedMatches} emptyMessage="No finished matches loaded" tourFilter={matchTourFilter} warning={finishedWarning || undefined} />
            </section>
          ) : null}

          {/* ── Props ── */}
          {activeTab === "props" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><BarChart3 size={16} /> Prop Analyzer</h2>
                <span className="pill">EV · Kelly · Surface-adjusted</span>
              </div>

              {/* Surface + form controls */}
              <div className="propControls">
                <div className="propControlGroup">
                  <span className="muted">Surface</span>
                  <div className="filterRow" style={{ marginBottom: 0 }}>
                    {SURFACES.map((s) => (
                      <button key={s} className={propSurface === s ? "filterPill active" : "filterPill"} onClick={() => setPropSurface(s)}>{s}</button>
                    ))}
                  </div>
                </div>
                <label className="formToggle">
                  <input type="checkbox" checked={useForm} onChange={(e) => setUseForm(e.target.checked)} />
                  <span>Use recent form (last 10 matches)</span>
                </label>
              </div>

              <div className="propForm">
                <label>Player<input list="prop-players" value={propPlayer} onChange={(e) => setPropPlayer(e.target.value)} placeholder="Player name" /></label>
                <label>Opponent<input list="prop-players" value={propOpponent} onChange={(e) => setPropOpponent(e.target.value)} placeholder="Opponent (optional)" /></label>
                <label>Category
                  <select value={propMarket} onChange={(e) => setPropMarket(e.target.value)}>
                    {propCategories.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
                  </select>
                </label>
                <label>Line<input value={propLine} inputMode="decimal" onChange={(e) => setPropLine(e.target.value)} placeholder="4.5" /></label>
                <label className="oddsLabel">
                  Book Odds (Am.)
                  <input value={propOdds} inputMode="numeric" onChange={(e) => setPropOdds(e.target.value)} placeholder="-110 or +150" />
                  <span className="muted oddsHint">Enter odds → see EV %</span>
                </label>
                <datalist id="prop-players">{propPlayerOptions.slice(0, 200).map((p) => <option key={p.playerId} value={p.name} />)}</datalist>
                <button className="primaryButton" onClick={analyzeStructuredProp}>Analyze Prop</button>
              </div>

              {/* Tour filter for player autocomplete */}
              <div className="propControls">
                <div className="propControlGroup">
                  <span className="muted">Player Tour</span>
                  <div className="filterRow" style={{ marginBottom: 0 }}>
                    <button className={propTourFilter === "" ? "filterPill active" : "filterPill"} onClick={() => setPropTourFilter("")}>All</button>
                    {(["ATP","WTA","Challenger","ITF Men","ITF Women","Futures"] as Tour[]).map((t) => (
                      <button key={t} className={propTourFilter === t ? "filterPill active" : "filterPill"} style={propTourFilter === t ? { borderColor: tourColor(t), color: tourColor(t) } : {}} onClick={() => setPropTourFilter(propTourFilter === t ? "" : t)}>{t}</button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="propBox">
                <textarea value={propText} onChange={(e) => setPropText(e.target.value)} />
                <button className="secondaryButton" onClick={analyzePasted}>Analyze Pasted Lines</button>
              </div>

              {/* Stake calculator */}
              {projections.length > 0 ? (
                <div className="stakeCalc">
                  <div className="stakeCalcTitle muted">Stake Calculator</div>
                  <div className="stakeCalcRow">
                    <label>Bankroll ($)<input value={bankroll} inputMode="decimal" onChange={(e) => setBankroll(e.target.value)} placeholder="1000" /></label>
                    <label>Kelly Fraction
                      <select value={kellyFraction} onChange={(e) => setKellyFraction(Number(e.target.value))}>
                        <option value={1}>Full Kelly</option>
                        <option value={0.5}>Half Kelly</option>
                        <option value={0.25}>Quarter Kelly (Recommended)</option>
                        <option value={0.1}>1/10 Kelly</option>
                      </select>
                    </label>
                  </div>
                </div>
              ) : null}

              {/* Confidence filter */}
              {projections.length > 0 ? (
                <div className="filterRow" style={{ marginTop: 12 }}>
                  <span className="muted" style={{ marginRight: 4, fontSize: 12 }}>Min confidence:</span>
                  {[0, 60, 70, 80].map((v) => (
                    <button key={v} className={minConfidence === v ? "filterPill active" : "filterPill"} onClick={() => setMinConfidence(v)}>{v === 0 ? "Any" : `${v}%+`}</button>
                  ))}
                  <span className="muted" style={{ fontSize: 12 }}>{filteredProjections.length} / {projections.length} shown</span>
                </div>
              ) : null}

              {filteredProjections.map((proj) => {
                const bankrollNum = Number(bankroll);
                const kellyStake = bankrollNum > 0 && proj.kellyPct != null
                  ? (bankrollNum * (proj.kellyPct / 100) * kellyFraction).toFixed(2)
                  : null;
                return (
                  <article className="projection" key={`${proj.player}-${proj.market}-${proj.line}`}>
                    <div className="matchTop">
                      <div>
                        <strong>{proj.player}{proj.opponent ? ` vs ${proj.opponent}` : ""} · {proj.market} {proj.side} {proj.line}</strong>
                        {proj.surface && proj.surface !== "All" ? <span className="muted"> · {proj.surface}</span> : null}
                        {proj.sampleSize < 30 ? <span className="lowSampleBadge" title="Fewer than 30 matches — treat projection with caution">Low sample</span> : null}
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span className={proj.side === "Over" ? "edgePositive" : proj.side === "Under" ? "edgeNegative" : "muted"}>
                          {proj.edge >= 0 ? "+" : ""}{proj.edge}
                        </span>
                        <button className="addParlayBtn" onClick={() => addToParlay(proj)} title="Add to parlay">+Parlay</button>
                      </div>
                    </div>
                    <div className="statGrid">
                      <div className="stat"><span className="muted">Projection</span><strong>{proj.projection}</strong></div>
                      <div className="stat"><span className="muted">Confidence</span><strong>{proj.confidence}%</strong></div>
                      <div className="stat"><span className="muted">Sample</span><strong>{proj.sampleSize}</strong></div>
                      {kellyStake ? <div className="stat"><span className="muted">Kelly Stake</span><strong>${kellyStake}</strong></div> : null}
                    </div>
                    <EVPanel proj={proj} />
                    <p className="muted">{proj.note}</p>
                  </article>
                );
              })}

              <ParlayBuilder items={parlayItems} onRemove={removeFromParlay} />
            </section>
          ) : null}

          {/* ── Players & Matchup ── */}
          {activeTab === "players" ? (
            <>
              {compareMode && matchupData ? (
                <section className="section fullWidth">
                  <div className="sectionHeader">
                    <h2>Matchup &amp; H2H</h2>
                    <span className="pill">{matchupData.record.totalMatches} meetings found</span>
                  </div>
                  <MatchupPanel data={matchupData.record} p1={matchupData.player1} p2={matchupData.player2} />
                </section>
              ) : compareMode && selectedPlayers.length === 2 && matchupLoading ? (
                <section className="section fullWidth">
                  <div className="match"><strong>Loading matchup…</strong></div>
                </section>
              ) : compareMode && selectedPlayers.length < 2 ? (
                <section className="section fullWidth">
                  <div className="match">
                    <strong>Select 2 players below to compare</strong>
                    <p className="muted">{selectedPlayers.length === 1 ? `${selectedPlayers[0]} selected — pick one more.` : `Click "Select" on any two players.`}</p>
                  </div>
                </section>
              ) : null}

              <section className="section fullWidth">
                <div className="sectionHeader">
                  <h2><Search size={16} /> Player Database</h2>
                  <span className="pill">{filteredPlayers.length} players</span>
                </div>
                {filteredPlayers.length === 0 ? (
                  <div className="player"><strong>No players found</strong><p className="muted">Run <code>npm run import:sackmann</code> with Sackmann CSVs to build the database.</p></div>
                ) : filteredPlayers.slice(0, 50).map((p) => (
                  <PlayerCard
                    key={`${p.tour}-${p.playerId}`}
                    player={p}
                    onSelect={compareMode ? () => toggleSelectPlayer(p.name) : undefined}
                    selected={selectedPlayers.includes(p.name)}
                  />
                ))}
              </section>
            </>
          ) : null}

          {/* ── Tracker ── */}
          {activeTab === "tracker" ? <BetTrackerTab players={players} /> : null}

        </div>
      </main>
    </div>
  );
}
