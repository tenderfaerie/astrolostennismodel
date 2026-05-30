export type Tour = "ATP" | "WTA" | "Challenger" | "ITF Men" | "ITF Women" | "Futures";

export type Surface = "Hard" | "Clay" | "Grass" | "Carpet" | "Indoor" | "Unknown";

export type LiveMatch = {
  provider: "sofascore";
  providerId: string;
  tournament: string;
  category: string;
  round?: string;
  status: string;
  statusType?: string;
  surface?: Surface;
  startTimestamp?: number;
  homePlayer: string;
  awayPlayer: string;
  homeScore?: number;
  awayScore?: number;
  periodScores: Array<{
    period: string;
    home: number | null;
    away: number | null;
  }>;
  server?: "home" | "away";
  lastPoint?: string;
  currentGame?: {
    set: number;
    game: number;
    homeGames: number | null;
    awayGames: number | null;
    serving?: "home" | "away";
    scoring?: "home" | "away";
    points: Array<{
      homePoint: string;
      awayPoint: string;
      winner?: "home" | "away";
    }>;
  };
  stats?: Array<{
    group: string;
    name: string;
    home: string | number | null;
    away: string | number | null;
    key?: string;
  }>;
  moneyline?: {
    marketName: string;
    suspended: boolean;
    home: {
      fractional?: string;
      decimal?: number | null;
      american?: number | null;
    } | null;
    away: {
      fractional?: string;
      decimal?: number | null;
      american?: number | null;
    } | null;
  };
  detailUrl?: string;
  fetchedAt: string;
};

export type PlayerSummary = {
  playerId: string;
  name: string;
  tour: "ATP" | "WTA";
  hand?: string;
  height?: number | null;
  country?: string;
  rank?: number | null;
  points?: number | null;
  matches: number;
  wins: number;
  losses: number;
  winPct: number;
  aceRate: number | null;
  dfRate: number | null;
  firstServePct: number | null;
  firstServeWonPct: number | null;
  secondServeWonPct: number | null;
  holdProxyPct: number | null;
  bpSavedPct: number | null;
  bpCreatedPerReturnGame: number | null;
  surfaces: Record<string, { matches: number; wins: number; losses: number; winPct: number }>;
  recentMatches: Array<{
    date: string;
    tournament: string;
    surface: string;
    opponent: string;
    result: "W" | "L";
    score: string;
  }>;
};

export type PropProjection = {
  player: string;
  opponent?: string;
  market: string;
  side: "Over" | "Under" | "Pass";
  line: number;
  projection: number;
  edge: number;
  confidence: number;
  sampleSize: number;
  note: string;
  categoryId?: string;
};
