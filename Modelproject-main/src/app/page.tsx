"use client";

import { Activity, BarChart3, Radio, Search, ShieldCheck, Swords } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { LiveMatch, PlayerSummary, PropProjection } from "@/lib/types";
import { propCategories } from "@/lib/prop-model";

function pct(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 100)}%`;
}

function money(value?: number | null) {
  if (value === null || value === undefined) return "—";
  return value > 0 ? `+${value}` : String(value);
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

  const homeAces = statNumber(match, "aces", "home");
  const awayAces = statNumber(match, "aces", "away");
  const homeDfs = statNumber(match, "doubleFaults", "home");
  const awayDfs = statNumber(match, "doubleFaults", "away");
  const homeBp = statNumber(match, "breakPointsScored", "home");
  const awayBp = statNumber(match, "breakPointsScored", "away");
  const homeService = statNumber(match, "servicePointsScored", "home");
  const awayService = statNumber(match, "servicePointsScored", "away");
  const homeReturn = statNumber(match, "receiverPointsScored", "home");
  const awayReturn = statNumber(match, "receiverPointsScored", "away");

  homeScore += (homeAces - awayAces) * 0.006;
  homeScore -= (homeDfs - awayDfs) * 0.008;
  homeScore += (homeBp - awayBp) * 0.018;
  homeScore += (homeService - awayService) * 0.002;
  homeScore += (homeReturn - awayReturn) * 0.002;

  if (normalizedHomeMarket !== null) {
    homeScore = homeScore * 0.42 + normalizedHomeMarket * 0.58;
  }

  const homeModel = Math.max(0.05, Math.min(0.95, homeScore));
  const winner = homeModel >= 0.5 ? match.homePlayer : match.awayPlayer;

  return {
    winner,
    homeModel,
    awayModel: 1 - homeModel,
    homeMarket: normalizedHomeMarket,
    awayMarket: normalizedHomeMarket === null ? null : 1 - normalizedHomeMarket
  };
}

const featuredStatKeys = [
  "aces",
  "doubleFaults",
  "firstServeAccuracy",
  "firstServePointsAccuracy",
  "secondServePointsAccuracy",
  "breakPointsSaved",
  "breakPointsScored",
  "servicePointsScored",
  "receiverPointsScored",
  "winnersTotal",
  "unforcedErrorsTotal",
  "tiebreaks"
];

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

export default function Home() {
  const [liveMatches, setLiveMatches] = useState<LiveMatch[]>([]);
  const [players, setPlayers] = useState<PlayerSummary[]>([]);
  const [query, setQuery] = useState("");
  const [propText, setPropText] = useState("Carlos Alcaraz aces over 4.5\nIga Swiatek games won over 12.5");
  const [propPlayer, setPropPlayer] = useState("Carlos Alcaraz");
  const [propOpponent, setPropOpponent] = useState("Jannik Sinner");
  const [propMarket, setPropMarket] = useState("aces");
  const [propLine, setPropLine] = useState("4.5");
  const [projections, setProjections] = useState<PropProjection[]>([]);
  const [liveError, setLiveError] = useState("");
  const [liveWarning, setLiveWarning] = useState("");
  const [lastLiveRefresh, setLastLiveRefresh] = useState("");

  useEffect(() => {
    let active = true;

    async function loadLive() {
      try {
        const response = await fetch("/api/live", { cache: "no-store" });
        const data = await response.json();
        if (!active) return;
        setLiveMatches(data.matches ?? []);
        setLiveError(data.error ?? "");
        setLiveWarning(data.warning ?? "");
        setLastLiveRefresh(new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" }));
      } catch (error) {
        if (active) setLiveError(String(error));
      }
    }

    loadLive();
    const interval = window.setInterval(loadLive, 15000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    fetch(`/api/players?q=${encodeURIComponent(query)}`)
      .then((response) => response.json())
      .then((data) => setPlayers(data.players ?? []))
      .catch(() => setPlayers([]));
  }, [query]);

  const topPlayers = useMemo(() => players.slice(0, 8), [players]);

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
      body: JSON.stringify({
        player: propPlayer,
        opponent: propOpponent,
        market: propMarket,
        line: Number(propLine)
      })
    });
    const data = await response.json();
    setProjections(data.projections ?? []);
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark" aria-hidden="true">
            <span />
          </div>
          AstroTennis
        </div>
        <nav className="nav" aria-label="Primary">
          <button className="active"><Radio size={16} /> Live</button>
          <button><BarChart3 size={16} /> Props</button>
          <button><Search size={16} /> Players</button>
          <button><Swords size={16} /> H2H</button>
        </nav>
      </aside>

      <main className="main">
        <div className="topbar">
          <div>
            <h1>Live tennis, player analytics, and prop edges</h1>
            <p>SofaScore prototype feed plus your imported Sackmann ATP/WTA database.</p>
          </div>
          <input
            className="search"
            placeholder="Search players"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        <div className="grid">
          <section className="section">
            <div className="sectionHeader">
              <h2><Activity size={16} /> Live Matches</h2>
              <span className="pill">{lastLiveRefresh ? `Updated ${lastLiveRefresh}` : "SofaScore prototype"}</span>
            </div>

            {liveWarning ? (
              <div className="providerWarning">
                SofaScore blocked the server request, so these rows are prototype placeholders while the provider access path is hardened.
              </div>
            ) : null}

            {liveError ? (
              <div className="match">
                <strong>Live feed unavailable</strong>
                <p className="muted">{liveError}</p>
              </div>
            ) : liveMatches.length === 0 ? (
              <div className="match">
                <strong>No live matches returned</strong>
                <p className="muted">The provider is wired. If tennis is quiet, this will show scheduled matches.</p>
              </div>
            ) : (
              liveMatches.slice(0, 12).map((match) => (
                <article className="match" key={match.providerId}>
                  <div className="matchTop">
                    <div>
                      <strong>{match.tournament}</strong>
                      <div className="muted">{match.category} {match.round ? `• ${match.round}` : ""}</div>
                    </div>
                    <span className="pill">{match.status}</span>
                  </div>
                  <PredictionStrip match={match} />
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
                      )) : (
                        <div className="setBox">
                          <div>{match.homeScore ?? "–"}</div>
                          <div>{match.awayScore ?? "–"}</div>
                        </div>
                      )}
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
              ))
            )}
          </section>

          <section className="section">
            <div className="sectionHeader">
              <h2><ShieldCheck size={16} /> Prop Analyzer</h2>
              <span className="pill">PrizePicks / Underdog</span>
            </div>
            <div className="propForm">
              <label>
                Player
                <input
                  list="prop-players"
                  value={propPlayer}
                  onChange={(event) => setPropPlayer(event.target.value)}
                  placeholder="Search player"
                />
              </label>
              <label>
                Opponent
                <input
                  list="prop-players"
                  value={propOpponent}
                  onChange={(event) => setPropOpponent(event.target.value)}
                  placeholder="Input opponent"
                />
              </label>
              <label>
                Category
                <select value={propMarket} onChange={(event) => setPropMarket(event.target.value)}>
                  {propCategories.map((category) => (
                    <option key={category.id} value={category.id}>{category.label}</option>
                  ))}
                </select>
              </label>
              <label>
                Line
                <input
                  value={propLine}
                  inputMode="decimal"
                  onChange={(event) => setPropLine(event.target.value)}
                  placeholder="4.5"
                />
              </label>
              <datalist id="prop-players">
                {players.slice(0, 200).map((player) => (
                  <option key={`${player.tour}-${player.playerId}`} value={player.name} />
                ))}
              </datalist>
              <button className="primaryButton" onClick={analyzeStructuredProp}>Get Over / Under</button>
            </div>
            <div className="propBox">
              <textarea value={propText} onChange={(event) => setPropText(event.target.value)} />
              <button className="secondaryButton" onClick={analyzeProps}>Analyze Pasted Lines</button>
            </div>
            {projections.map((projection) => (
              <article className="projection" key={`${projection.player}-${projection.market}-${projection.line}`}>
                <div className="matchTop">
                  <strong>{projection.player} {projection.opponent ? `vs ${projection.opponent}` : ""} · {projection.market} {projection.side} {projection.line}</strong>
                  <span className={projection.side === "Over" ? "edgePositive" : projection.side === "Under" ? "edgeNegative" : "muted"}>
                    {projection.edge >= 0 ? "+" : ""}{projection.edge}
                  </span>
                </div>
                <div className="statGrid">
                  <div className="stat"><span className="muted">Projection</span><strong>{projection.projection}</strong></div>
                  <div className="stat"><span className="muted">Confidence</span><strong>{projection.confidence}%</strong></div>
                  <div className="stat"><span className="muted">Sample</span><strong>{projection.sampleSize}</strong></div>
                </div>
                <p className="muted">{projection.note}</p>
              </article>
            ))}
          </section>

          <section className="section">
            <div className="sectionHeader">
              <h2>Player Database</h2>
              <span className="pill">{players.length} loaded</span>
            </div>
            {topPlayers.length === 0 ? (
              <div className="player">
                <strong>No imported players yet</strong>
                <p className="muted">Run the import to build player pages from your ATP/WTA CSVs.</p>
              </div>
            ) : topPlayers.map((player) => (
              <article className="player" key={`${player.tour}-${player.playerId}`}>
                <div className="playerTop">
                  <div>
                    <strong>{player.name}</strong>
                    <div className="muted">{player.tour} • {player.country ?? "—"} • Rank {player.rank ?? "—"}</div>
                  </div>
                  <span className="pill">{pct(player.winPct)}</span>
                </div>
                <div className="statGrid">
                  <div className="stat"><span className="muted">Aces</span><strong>{pct(player.aceRate)}</strong></div>
                  <div className="stat"><span className="muted">1st Won</span><strong>{pct(player.firstServeWonPct)}</strong></div>
                  <div className="stat"><span className="muted">BP Saved</span><strong>{pct(player.bpSavedPct)}</strong></div>
                </div>
              </article>
            ))}
          </section>

          <section className="section">
            <div className="sectionHeader">
              <h2>Development Notes</h2>
              <span className="pill">Not gambling advice</span>
            </div>
            <div className="match">
              <strong>Provider-safe architecture</strong>
              <p className="muted">SofaScore is isolated behind one provider file. A licensed feed can replace it later without touching the UI or model routes.</p>
            </div>
            <div className="match">
              <strong>Next build target</strong>
              <p className="muted">Add PostgreSQL, Redis, normalized match tables, and scheduled ingestion after this prototype proves the workflow.</p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
