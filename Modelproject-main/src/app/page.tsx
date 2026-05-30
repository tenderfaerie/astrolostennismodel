"use client";

import { Activity, BarChart3, Calendar, CheckCircle, Radio, Search, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { LiveMatch, PlayerSummary, PropProjection, Tour } from "@/lib/types";
import { propCategories } from "@/lib/prop-model";

type Tab = "live" | "upcoming" | "finished" | "props" | "players";

const TOUR_LABELS: Tour[] = ["ATP", "WTA", "ITF Men", "ITF Women", "Challenger", "Futures"];

function pct(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 100)}%`;
}

function money(value?: number | null) {
  if (value === null || value === undefined) return "—";
  return value > 0 ? `+${value}` : String(value);
}

function formatTime(timestamp?: number) {
  if (!timestamp) return "—";
  return new Date(timestamp * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function formatDate(timestamp?: number) {
  if (!timestamp) return "";
  return new Date(timestamp * 1000).toLocaleDateString([], { month: "short", day: "numeric" });
}

function americanToProbability(value?: number | null) {
  if (value === null || value === undefined || value === 0) return null;
  return value > 0 ? 100 / (value + 100) : Math.abs(value) / (Math.abs(value) + 100);
}

function statNumber(match: LiveMatch, key: string, side: "home" | "away") {
  const stat = match.stats?.find((item) => item.key === key);
  const raw = stat?.[side];
  if (typeof raw === "number") return raw;
  if (typeof raw === "string") {
    const parsed = Number(raw.match(/-?\d+(\.\d+)?/)?.[0]);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function estimateWinner(match: LiveMatch) {
  const homeMarket = americanToProbability(match.moneyline?.home?.american);
  const awayMarket = americanToProbability(match.moneyline?.away?.american);
  const marketTotal = (homeMarket ?? 0) + (awayMarket ?? 0);
  const normalizedHomeMarket = marketTotal > 0 ? (homeMarket ?? 0) / marketTotal : null;

  let homeScore = 0.5;
  homeScore += ((match.homeScore ?? 0) - (match.awayScore ?? 0)) * 0.12;

  const latestSet = match.periodScores.at(-1);
  if (latestSet && latestSet.home !== null && latestSet.away !== null) {
    homeScore += ((latestSet.home ?? 0) - (latestSet.away ?? 0)) * 0.018;
  }

  if (match.server === "home") homeScore += 0.025;
  if (match.server === "away") homeScore -= 0.025;

  homeScore += (statNumber(match, "aces", "home") - statNumber(match, "aces", "away")) * 0.006;
  homeScore -= (statNumber(match, "doubleFaults", "home") - statNumber(match, "doubleFaults", "away")) * 0.008;
  homeScore += (statNumber(match, "breakPointsScored", "home") - statNumber(match, "breakPointsScored", "away")) * 0.018;
  homeScore += (statNumber(match, "servicePointsScored", "home") - statNumber(match, "servicePointsScored", "away")) * 0.002;
  homeScore += (statNumber(match, "receiverPointsScored", "home") - statNumber(match, "receiverPointsScored", "away")) * 0.002;

  if (normalizedHomeMarket !== null) {
    homeScore = homeScore * 0.42 + normalizedHomeMarket * 0.58;
  }

  const homeModel = Math.max(0.05, Math.min(0.95, homeScore));
  return {
    winner: homeModel >= 0.5 ? match.homePlayer : match.awayPlayer,
    homeModel,
    awayModel: 1 - homeModel,
    homeMarket: normalizedHomeMarket,
    awayMarket: normalizedHomeMarket === null ? null : 1 - normalizedHomeMarket
  };
}

const featuredStatKeys = [
  "aces", "doubleFaults", "firstServeAccuracy", "firstServePointsAccuracy",
  "secondServePointsAccuracy", "breakPointsSaved", "breakPointsScored",
  "servicePointsScored", "receiverPointsScored", "winnersTotal",
  "unforcedErrorsTotal", "tiebreaks"
];

function tourColor(tour: string): string {
  if (tour === "ATP") return "var(--blue)";
  if (tour === "WTA") return "#e87eff";
  if (tour === "ITF Men" || tour === "ITF Women") return "var(--gold)";
  if (tour === "Challenger") return "#56d4c0";
  return "var(--muted)";
}

function TourBadge({ tour }: { tour: string }) {
  return (
    <span className="tourBadge" style={{ borderColor: tourColor(tour), color: tourColor(tour) }}>
      {tour}
    </span>
  );
}

function PredictionStrip({ match }: { match: LiveMatch }) {
  const prediction = estimateWinner(match);
  const winnerSide = prediction.homeModel >= 0.5 ? "home" : "away";
  const modelPct = Math.round(Math.max(prediction.homeModel, prediction.awayModel) * 100);
  const marketPct = prediction.homeMarket === null
    ? null
    : Math.round(Math.max(prediction.homeMarket, prediction.awayMarket ?? 0) * 100);

  return (
    <div className="predictionStrip">
      <div>
        <span className="muted">Projected Winner</span>
        <strong>{prediction.winner}</strong>
      </div>
      <div>
        <span className="muted">Astro Model</span>
        <strong>{modelPct}%</strong>
      </div>
      <div>
        <span className="muted">Market</span>
        <strong>{marketPct === null ? "—" : `${marketPct}%`}</strong>
      </div>
      <div>
        <span className="muted">Lean</span>
        <strong className={winnerSide === "home" ? "edgePositive" : "edgeNegative"}>
          {winnerSide === "home" ? "Home" : "Away"}
        </strong>
      </div>
    </div>
  );
}

function MatchCard({ match, showTime }: { match: LiveMatch; showTime?: boolean }) {
  return (
    <article className="match">
      <div className="matchTop">
        <div>
          <strong>{match.tournament}</strong>
          <div className="muted">
            {match.category}
            {match.round ? ` • ${match.round}` : ""}
            {match.surface && match.surface !== "Unknown" ? ` • ${match.surface}` : ""}
          </div>
        </div>
        {showTime && match.startTimestamp ? (
          <span className="timeChip">{formatDate(match.startTimestamp)} {formatTime(match.startTimestamp)}</span>
        ) : (
          <span className="pill">{match.status}</span>
        )}
      </div>

      {match.statusType === "inprogress" ? <PredictionStrip match={match} /> : null}

      <div className="scoreline">
        <div>
          <div className={match.server === "home" ? "servingPlayer" : ""}>
            {match.homePlayer}
            {match.server === "home" ? <span className="serveDot" title="Serving" /> : null}
          </div>
          <div className={match.server === "away" ? "servingPlayer" : ""}>
            {match.awayPlayer}
            {match.server === "away" ? <span className="serveDot" title="Serving" /> : null}
          </div>
        </div>
        <div className="sets">
          {match.periodScores.length ? match.periodScores.map((set) => (
            <div className="setBox" key={set.period}>
              <div>{set.home ?? "–"}</div>
              <div>{set.away ?? "–"}</div>
            </div>
          )) : match.homeScore !== undefined ? (
            <div className="setBox">
              <div>{match.homeScore ?? "–"}</div>
              <div>{match.awayScore ?? "–"}</div>
            </div>
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
          {match.stats
            .filter((stat) => featuredStatKeys.includes(stat.key ?? ""))
            .slice(0, 12)
            .map((stat) => (
              <div className="liveStat" key={`${match.providerId}-${stat.key ?? stat.name}`}>
                <span>{stat.home ?? "—"}</span>
                <em>{stat.name}</em>
                <span>{stat.away ?? "—"}</span>
              </div>
            ))}
        </div>
      ) : null}

      {match.currentGame?.points.length ? (
        <div className="pointPanel">
          <div className="pointHeader">
            <strong>Point by Point</strong>
            <span className="muted">Set {match.currentGame.set}, Game {match.currentGame.game}</span>
          </div>
          <div className="pointList">
            {match.currentGame.points.slice(-8).map((point, index) => (
              <div className="pointRow" key={`${match.providerId}-point-${index}`}>
                <span className={point.winner === "home" ? "pointWon" : ""}>{point.homePoint}</span>
                <em>{index + 1}</em>
                <span className={point.winner === "away" ? "pointWon" : ""}>{point.awayPoint}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </article>
  );
}

function MatchList({
  matches, emptyMessage, tourFilter, warning, showTime
}: {
  matches: LiveMatch[];
  emptyMessage: string;
  tourFilter: string;
  warning?: string;
  showTime?: boolean;
}) {
  const filtered = tourFilter
    ? matches.filter((m) => m.category?.toLowerCase().includes(tourFilter.toLowerCase()))
    : matches;

  return (
    <>
      {warning ? (
        <div className="providerWarning">
          SofaScore blocked the server request — prototype placeholders shown while provider access is hardened.
        </div>
      ) : null}
      {filtered.length === 0 ? (
        <div className="match">
          <strong>{emptyMessage}</strong>
          <p className="muted">
            {tourFilter ? `No ${tourFilter} matches found. Try clearing the tour filter.` : "Check back soon."}
          </p>
        </div>
      ) : (
        filtered.slice(0, 30).map((match) => (
          <MatchCard key={match.providerId} match={match} showTime={showTime} />
        ))
      )}
    </>
  );
}

function PlayerCard({ player }: { player: PlayerSummary }) {
  const [expanded, setExpanded] = useState(false);
  const surfaces = Object.entries(player.surfaces ?? {}).filter(([, v]) => v.matches > 0);

  return (
    <article className="player">
      <div className="playerTop">
        <div>
          <strong>{player.name}</strong>
          <div className="playerMeta">
            <TourBadge tour={player.tour} />
            <span className="muted">{player.country ?? "—"}</span>
            {player.rank ? <span className="muted">Rank {player.rank}</span> : null}
          </div>
        </div>
        <div className="playerTopRight">
          <span className="pill">{pct(player.winPct)}</span>
          <button className="expandBtn" onClick={() => setExpanded((v) => !v)} aria-label="Toggle details">
            {expanded ? "▲" : "▼"}
          </button>
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
                {surfaces.map(([surface, stats]) => (
                  <div className="surfaceCell" key={surface}>
                    <span className="muted">{surface}</span>
                    <strong>{pct(stats.winPct)}</strong>
                    <span className="muted">{stats.wins}W {stats.losses}L</span>
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

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("live");
  const [liveMatches, setLiveMatches] = useState<LiveMatch[]>([]);
  const [upcomingMatches, setUpcomingMatches] = useState<LiveMatch[]>([]);
  const [finishedMatches, setFinishedMatches] = useState<LiveMatch[]>([]);
  const [players, setPlayers] = useState<PlayerSummary[]>([]);
  const [query, setQuery] = useState("");
  const [tourFilter, setTourFilter] = useState("");
  const [propText, setPropText] = useState("Carlos Alcaraz aces over 4.5\nIga Swiatek games won over 12.5");
  const [propPlayer, setPropPlayer] = useState("Carlos Alcaraz");
  const [propOpponent, setPropOpponent] = useState("Jannik Sinner");
  const [propMarket, setPropMarket] = useState("aces");
  const [propLine, setPropLine] = useState("4.5");
  const [projections, setProjections] = useState<PropProjection[]>([]);
  const [liveWarning, setLiveWarning] = useState("");
  const [upcomingWarning, setUpcomingWarning] = useState("");
  const [finishedWarning, setFinishedWarning] = useState("");
  const [lastLiveRefresh, setLastLiveRefresh] = useState("");

  const loadLive = useCallback(async () => {
    try {
      const response = await fetch("/api/live", { cache: "no-store" });
      const data = await response.json();
      setLiveMatches(data.matches ?? []);
      setLiveWarning(data.warning ?? "");
      setLastLiveRefresh(new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" }));
    } catch {
      // keep stale data on network error
    }
  }, []);

  useEffect(() => {
    loadLive();
    const interval = window.setInterval(loadLive, 15000);
    return () => window.clearInterval(interval);
  }, [loadLive]);

  useEffect(() => {
    if (activeTab !== "upcoming") return;
    fetch("/api/live?type=upcoming", { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => { setUpcomingMatches(data.matches ?? []); setUpcomingWarning(data.warning ?? ""); })
      .catch(() => {});
  }, [activeTab]);

  useEffect(() => {
    if (activeTab !== "finished") return;
    fetch("/api/live?type=finished", { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => { setFinishedMatches(data.matches ?? []); setFinishedWarning(data.warning ?? ""); })
      .catch(() => {});
  }, [activeTab]);

  useEffect(() => {
    fetch(`/api/players?q=${encodeURIComponent(query)}`)
      .then((r) => r.json())
      .then((data) => setPlayers(data.players ?? []))
      .catch(() => setPlayers([]));
  }, [query]);

  const filteredPlayers = useMemo(
    () => tourFilter ? players.filter((p) => p.tour === tourFilter) : players,
    [players, tourFilter]
  );

  async function analyzeProps() {
    const response = await fetch("/api/props", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: propText })
    });
    const data = await response.json();
    setProjections(data.projections ?? []);
  }

  async function analyzeStructuredProp() {
    const response = await fetch("/api/props", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ player: propPlayer, opponent: propOpponent, market: propMarket, line: Number(propLine) })
    });
    const data = await response.json();
    setProjections(data.projections ?? []);
  }

  const tabTitle: Record<Tab, string> = {
    live: "Live Matches",
    upcoming: "Upcoming Matches",
    finished: "Finished Matches",
    props: "Prop Analyzer",
    players: "Player Database"
  };

  const matchTabs = activeTab === "live" || activeTab === "upcoming" || activeTab === "finished";

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark" aria-hidden="true"><span /></div>
          AstroTennis
        </div>
        <nav className="nav" aria-label="Primary">
          <button className={activeTab === "live" ? "active" : ""} onClick={() => setActiveTab("live")}>
            <Radio size={16} /> Live
          </button>
          <button className={activeTab === "upcoming" ? "active" : ""} onClick={() => setActiveTab("upcoming")}>
            <Calendar size={16} /> Upcoming
          </button>
          <button className={activeTab === "finished" ? "active" : ""} onClick={() => setActiveTab("finished")}>
            <CheckCircle size={16} /> Finished
          </button>
          <button className={activeTab === "props" ? "active" : ""} onClick={() => setActiveTab("props")}>
            <ShieldCheck size={16} /> Props
          </button>
          <button className={activeTab === "players" ? "active" : ""} onClick={() => setActiveTab("players")}>
            <Search size={16} /> Players
          </button>
        </nav>
      </aside>

      <main className="main">
        <div className="topbar">
          <div>
            <h1>{tabTitle[activeTab]}</h1>
            <p>ATP · WTA · ITF Men · ITF Women · Challenger · Futures</p>
          </div>
          {activeTab === "players" ? (
            <input
              className="search"
              placeholder="Search players"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          ) : null}
        </div>

        {matchTabs ? (
          <div className="filterRow">
            <button className={tourFilter === "" ? "filterPill active" : "filterPill"} onClick={() => setTourFilter("")}>All Tours</button>
            {["ATP", "WTA", "ITF", "Challenger"].map((t) => (
              <button
                key={t}
                className={tourFilter === t ? "filterPill active" : "filterPill"}
                onClick={() => setTourFilter(tourFilter === t ? "" : t)}
              >{t}</button>
            ))}
          </div>
        ) : null}

        {activeTab === "players" ? (
          <div className="filterRow">
            <button className={tourFilter === "" ? "filterPill active" : "filterPill"} onClick={() => setTourFilter("")}>All</button>
            {TOUR_LABELS.map((t) => (
              <button
                key={t}
                className={tourFilter === t ? "filterPill active" : "filterPill"}
                style={tourFilter === t ? { borderColor: tourColor(t), color: tourColor(t) } : {}}
                onClick={() => setTourFilter(tourFilter === t ? "" : t)}
              >{t}</button>
            ))}
          </div>
        ) : null}

        <div className="grid">
          {activeTab === "live" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><Activity size={16} /> Live</h2>
                <span className="pill">{lastLiveRefresh ? `Updated ${lastLiveRefresh}` : "Auto-refresh 15s"}</span>
              </div>
              <MatchList
                matches={liveMatches}
                emptyMessage="No live matches right now"
                tourFilter={tourFilter}
                warning={liveWarning || undefined}
              />
            </section>
          ) : null}

          {activeTab === "upcoming" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><Calendar size={16} /> Upcoming — Today &amp; Tomorrow</h2>
                <span className="pill">{upcomingMatches.length} scheduled</span>
              </div>
              <MatchList
                matches={upcomingMatches}
                emptyMessage="No upcoming matches loaded yet"
                tourFilter={tourFilter}
                warning={upcomingWarning || undefined}
                showTime
              />
            </section>
          ) : null}

          {activeTab === "finished" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><CheckCircle size={16} /> Finished — Yesterday &amp; Today</h2>
                <span className="pill">{finishedMatches.length} results</span>
              </div>
              <MatchList
                matches={finishedMatches}
                emptyMessage="No finished matches loaded yet"
                tourFilter={tourFilter}
                warning={finishedWarning || undefined}
              />
            </section>
          ) : null}

          {activeTab === "props" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><BarChart3 size={16} /> Prop Analyzer</h2>
                <span className="pill">PrizePicks / Underdog</span>
              </div>
              <div className="propForm">
                <label>
                  Player
                  <input list="prop-players" value={propPlayer} onChange={(e) => setPropPlayer(e.target.value)} placeholder="Search player" />
                </label>
                <label>
                  Opponent
                  <input list="prop-players" value={propOpponent} onChange={(e) => setPropOpponent(e.target.value)} placeholder="Opponent (optional)" />
                </label>
                <label>
                  Category
                  <select value={propMarket} onChange={(e) => setPropMarket(e.target.value)}>
                    {propCategories.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
                  </select>
                </label>
                <label>
                  Line
                  <input value={propLine} inputMode="decimal" onChange={(e) => setPropLine(e.target.value)} placeholder="4.5" />
                </label>
                <datalist id="prop-players">
                  {players.slice(0, 200).map((p) => <option key={`${p.tour}-${p.playerId}`} value={p.name} />)}
                </datalist>
                <button className="primaryButton" onClick={analyzeStructuredProp}>Get Over / Under</button>
              </div>
              <div className="propBox">
                <textarea value={propText} onChange={(e) => setPropText(e.target.value)} />
                <button className="secondaryButton" onClick={analyzeProps}>Analyze Pasted Lines</button>
              </div>
              {projections.map((proj) => (
                <article className="projection" key={`${proj.player}-${proj.market}-${proj.line}`}>
                  <div className="matchTop">
                    <strong>{proj.player} {proj.opponent ? `vs ${proj.opponent}` : ""} · {proj.market} {proj.side} {proj.line}</strong>
                    <span className={proj.side === "Over" ? "edgePositive" : proj.side === "Under" ? "edgeNegative" : "muted"}>
                      {proj.edge >= 0 ? "+" : ""}{proj.edge}
                    </span>
                  </div>
                  <div className="statGrid">
                    <div className="stat"><span className="muted">Projection</span><strong>{proj.projection}</strong></div>
                    <div className="stat"><span className="muted">Confidence</span><strong>{proj.confidence}%</strong></div>
                    <div className="stat"><span className="muted">Sample</span><strong>{proj.sampleSize}</strong></div>
                  </div>
                  <p className="muted">{proj.note}</p>
                </article>
              ))}
            </section>
          ) : null}

          {activeTab === "players" ? (
            <section className="section fullWidth">
              <div className="sectionHeader">
                <h2><Search size={16} /> Player Database</h2>
                <span className="pill">{filteredPlayers.length} players</span>
              </div>
              {filteredPlayers.length === 0 ? (
                <div className="player">
                  <strong>No players found</strong>
                  <p className="muted">Run <code>npm run import:sackmann</code> with your Sackmann CSVs to build the database.</p>
                </div>
              ) : filteredPlayers.slice(0, 50).map((player) => (
                <PlayerCard key={`${player.tour}-${player.playerId}`} player={player} />
              ))}
            </section>
          ) : null}
        </div>
      </main>
    </div>
  );
}
