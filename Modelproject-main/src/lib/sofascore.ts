import { LiveMatch } from "./types";

const BASE_URL = "https://www.sofascore.com/api/v1";

type SofaEvent = {
  id: number | string;
  slug?: string;
  tournament?: {
    name?: string;
    slug?: string;
    category?: { name?: string };
    uniqueTournament?: { name?: string };
  };
  roundInfo?: { name?: string; round?: number };
  status?: { description?: string; type?: string };
  startTimestamp?: number;
  homeTeam?: { name?: string; shortName?: string };
  awayTeam?: { name?: string; shortName?: string };
  homeScore?: Record<string, number>;
  awayScore?: Record<string, number>;
  time?: { currentPeriodStartTimestamp?: number };
  pointByPoint?: unknown;
};

type SofaLiveResponse = {
  events?: SofaEvent[];
};

const TOURNAMENT_SURFACE_MAP: Record<string, LiveMatch["surface"]> = {
  "french open": "Clay", "roland garros": "Clay", "madrid": "Clay",
  "barcelona": "Clay", "monte carlo": "Clay", "monte-carlo": "Clay",
  "rome": "Clay", "hamburg": "Clay", "munich": "Clay", "geneva": "Clay",
  "lyon": "Clay", "estoril": "Clay", "bucharest": "Clay", "gstaad": "Clay",
  "wimbledon": "Grass", "queens": "Grass", "halle": "Grass",
  "eastbourne": "Grass", "nottingham": "Grass", "s-hertogenbosch": "Grass",
  "us open": "Hard", "australian open": "Hard", "flushing": "Hard",
  "masters": "Hard", "miami": "Hard", "indian wells": "Hard",
  "cincinnati": "Hard", "toronto": "Hard", "montreal": "Hard",
  "beijing": "Hard", "shanghai": "Hard", "dubai": "Hard", "doha": "Hard",
  "abu dhabi": "Hard", "brisbane": "Hard", "sydney": "Hard",
  "melbourne": "Hard", "washington": "Hard", "los angeles": "Hard",
  "winston-salem": "Hard", "new york": "Hard",
  "paris": "Indoor", "vienna": "Indoor", "basel": "Indoor",
  "rotterdam": "Indoor", "marseille": "Indoor", "dallas": "Indoor",
  "sofia": "Indoor", "stockholm": "Indoor", "moscow": "Indoor",
};

function normalizeSurface(value?: string): LiveMatch["surface"] {
  if (!value) return "Unknown";
  const lower = value.toLowerCase();
  if (lower.includes("clay")) return "Clay";
  if (lower.includes("grass")) return "Grass";
  if (lower.includes("hard")) return "Hard";
  if (lower.includes("carpet")) return "Carpet";
  if (lower.includes("indoor")) return "Indoor";
  for (const [name, surface] of Object.entries(TOURNAMENT_SURFACE_MAP)) {
    if (lower.includes(name)) return surface;
  }
  return "Unknown";
}

function normalizeEvent(event: SofaEvent): LiveMatch {
  const homeScore = event.homeScore ?? {};
  const awayScore = event.awayScore ?? {};
  const periods = ["period1", "period2", "period3", "period4", "period5"]
    .map((period, index) => ({
      period: `S${index + 1}`,
      home: typeof homeScore[period] === "number" ? homeScore[period] : null,
      away: typeof awayScore[period] === "number" ? awayScore[period] : null
    }))
    .filter((period) => period.home !== null || period.away !== null);

  return {
    provider: "sofascore",
    providerId: String(event.id),
    tournament: event.tournament?.uniqueTournament?.name ?? event.tournament?.name ?? "Unknown tournament",
    category: event.tournament?.category?.name ?? "Tennis",
    round: event.roundInfo?.name ?? (event.roundInfo?.round ? `Round ${event.roundInfo.round}` : undefined),
    status: event.status?.description ?? "Unknown",
    statusType: event.status?.type,
    surface: normalizeSurface(event.tournament?.name),
    startTimestamp: event.startTimestamp,
    homePlayer: event.homeTeam?.name ?? event.homeTeam?.shortName ?? "Player A",
    awayPlayer: event.awayTeam?.name ?? event.awayTeam?.shortName ?? "Player B",
    homeScore: homeScore.current,
    awayScore: awayScore.current,
    periodScores: periods,
    detailUrl: event.slug ? `https://www.sofascore.com/${event.slug}/${event.id}` : undefined,
    fetchedAt: new Date().toISOString()
  };
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    headers: {
      accept: "application/json,text/plain,*/*",
      "accept-language": "en-US,en;q=0.9",
      origin: "https://www.sofascore.com",
      referer: "https://www.sofascore.com/tennis",
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    },
    next: { revalidate: 15 }
  });

  if (!response.ok) {
    throw new Error(`SofaScore request failed ${response.status}: ${url}`);
  }

  return response.json() as Promise<T>;
}

export async function getSofaScoreLiveTennis(): Promise<LiveMatch[]> {
  const candidates = [
    `${BASE_URL}/sport/tennis/events/live`,
    `${BASE_URL}/sport/tennis/scheduled-events/${new Date().toISOString().slice(0, 10)}`
  ];

  const errors: string[] = [];

  for (const url of candidates) {
    try {
      const data = await fetchJson<SofaLiveResponse>(url);
      const events = data.events ?? [];
      const liveEvents = events.filter((event) => event.status?.type !== "notstarted");
      return (liveEvents.length ? liveEvents : events).map(normalizeEvent);
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
    }
  }

  throw new Error(errors.join(" | "));
}

export async function getSofaScoreUpcomingTennis(): Promise<LiveMatch[]> {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dates = [today, tomorrow].map((d) => d.toISOString().slice(0, 10));

  const all: LiveMatch[] = [];
  for (const date of dates) {
    try {
      const data = await fetchJson<SofaLiveResponse>(`${BASE_URL}/sport/tennis/scheduled-events/${date}`);
      const events = (data.events ?? []).filter((e) => e.status?.type === "notstarted");
      all.push(...events.map(normalizeEvent));
    } catch {
      // skip dates that fail
    }
  }
  return all;
}

export async function getSofaScoreFinishedTennis(): Promise<LiveMatch[]> {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const dates = [yesterday, today].map((d) => d.toISOString().slice(0, 10));

  const all: LiveMatch[] = [];
  for (const date of dates) {
    try {
      const data = await fetchJson<SofaLiveResponse>(`${BASE_URL}/sport/tennis/scheduled-events/${date}`);
      const events = (data.events ?? []).filter((e) => e.status?.type === "finished");
      all.push(...events.map(normalizeEvent));
    } catch {
      // skip dates that fail
    }
  }
  return all;
}

export function getPrototypeLiveTennis(reason: string): LiveMatch[] {
  const fetchedAt = new Date().toISOString();

  return [
    {
      provider: "sofascore",
      providerId: "prototype-1",
      tournament: "Prototype Live Feed",
      category: "SofaScore blocked server fetch",
      round: "Integration check",
      status: reason.includes("403") ? "Provider blocked" : "Fallback",
      statusType: "interrupted",
      surface: "Hard",
      homePlayer: "Jannik Sinner",
      awayPlayer: "Carlos Alcaraz",
      homeScore: 1,
      awayScore: 1,
      periodScores: [
        { period: "S1", home: 6, away: 4 },
        { period: "S2", home: 3, away: 6 },
        { period: "S3", home: 2, away: 1 }
      ],
      server: "home",
      lastPoint: "SofaScore returned an access block from the server environment.",
      fetchedAt
    },
    {
      provider: "sofascore",
      providerId: "prototype-2",
      tournament: "Prototype Live Feed",
      category: "Historical model ready",
      round: "Prop analyzer",
      status: "Model live",
      statusType: "inprogress",
      surface: "Clay",
      homePlayer: "Aryna Sabalenka",
      awayPlayer: "Iga Swiatek",
      homeScore: 0,
      awayScore: 0,
      periodScores: [{ period: "S1", home: 4, away: 5 }],
      server: "away",
      fetchedAt
    }
  ];
}
