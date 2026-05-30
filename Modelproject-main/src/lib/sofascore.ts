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

function normalizeSurface(value?: string): LiveMatch["surface"] {
  if (!value) return "Unknown";
  const lower = value.toLowerCase();
  if (lower.includes("clay")) return "Clay";
  if (lower.includes("grass")) return "Grass";
  if (lower.includes("hard")) return "Hard";
  if (lower.includes("carpet")) return "Carpet";
  if (lower.includes("indoor")) return "Indoor";
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
