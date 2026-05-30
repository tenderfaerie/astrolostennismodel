import { PlayerSummary, PropProjection } from "./types";

export type PropCategory = {
  id: string;
  label: string;
  aliases: string[];
};

export const propCategories: PropCategory[] = [
  { id: "fantasy_score", label: "Fantasy Score", aliases: ["fantasy", "fs", "fantasy points", "score"] },
  { id: "aces", label: "Aces", aliases: ["ace"] },
  { id: "double_faults", label: "Double Faults", aliases: ["df", "dfs", "double fault"] },
  { id: "bpw", label: "Break Points Won", aliases: ["bpw", "break points", "break points won", "breaks"] },
  { id: "total_games", label: "Total Games", aliases: ["games", "match games", "total games played"] },
  { id: "games_won", label: "Total Games Won", aliases: ["games won", "total games won", "player games won"] },
  { id: "games_lost", label: "Games Lost", aliases: ["total games lost", "player games lost"] },
  { id: "sets_won", label: "Sets Won", aliases: ["set wins", "total sets won"] },
  { id: "sets_lost", label: "Sets Lost", aliases: ["set losses", "total sets lost"] },
  { id: "tiebreaks", label: "Tiebreaks", aliases: ["tb", "tie breaks", "tiebreak"] },
  { id: "service_games_won", label: "Service Games Won", aliases: ["service games", "service games won", "sgw"] },
  { id: "return_games_won", label: "Return Games Won", aliases: ["return games", "return games won", "rgw"] },
  { id: "total_points_won", label: "Total Points Won", aliases: ["points won", "total points", "tpw"] },
  { id: "winners", label: "Winners", aliases: ["winner", "total winners"] },
  { id: "unforced_errors", label: "Unforced Errors", aliases: ["errors", "ufe", "unforced error"] }
];

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function normalize(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, " ");
}

function categoryFor(market: string) {
  const normalized = normalize(market);
  return propCategories.find((category) =>
    category.id === market ||
    normalize(category.label) === normalized ||
    category.aliases.some((alias) => normalize(alias) === normalized || normalized.includes(normalize(alias)))
  ) ?? propCategories[0];
}

function aceProjection(player: PlayerSummary) {
  const serviceGames = 12.2 + (player.winPct - 0.5) * 2.4;
  return (player.aceRate ?? 0.065) * serviceGames * 6.2;
}

function dfProjection(player: PlayerSummary) {
  const serviceGames = 12.2 + (player.winPct - 0.5) * 2.4;
  return (player.dfRate ?? 0.035) * serviceGames * 6.2;
}

function gamesWonProjection(player: PlayerSummary, opponent?: PlayerSummary | null) {
  const opponentResistance = opponent ? (opponent.winPct - 0.5) * 2.8 : 0;
  return 11.8 + (player.winPct - 0.5) * 7.5 - opponentResistance;
}

function setsWonProjection(player: PlayerSummary, opponent?: PlayerSummary | null) {
  const opponentResistance = opponent ? (opponent.winPct - 0.5) * 0.55 : 0;
  return clamp(1 + (player.winPct - 0.5) * 1.4 - opponentResistance, 0.15, 2.7);
}

function breakPointsWonProjection(player: PlayerSummary, opponent?: PlayerSummary | null) {
  const base = (player.bpCreatedPerReturnGame ?? 0.48) * 10.8;
  const opponentBoost = opponent ? (0.55 - opponent.winPct) * 1.6 : 0;
  return clamp(base + opponentBoost, 0.4, 8.5);
}

function fantasyProjection(player: PlayerSummary, opponent?: PlayerSummary | null) {
  const gamesWon = gamesWonProjection(player, opponent);
  const gamesLost = opponent ? gamesWonProjection(opponent, player) : 21.8 - gamesWon;
  const setsWon = setsWonProjection(player, opponent);
  const setsLost = opponent ? setsWonProjection(opponent, player) : 2.2 - setsWon;
  return 10 + gamesWon - gamesLost + 3 * (setsWon - setsLost) + 0.5 * (aceProjection(player) - dfProjection(player));
}

function projectCategory(player: PlayerSummary, categoryId: string, opponent?: PlayerSummary | null) {
  switch (categoryId) {
    case "aces":
      return { value: aceProjection(player), note: "Aces use player ace rate with adjusted service-game expectation." };
    case "double_faults":
      return { value: dfProjection(player), note: "Double faults use player DF rate over projected service points." };
    case "bpw":
      return { value: breakPointsWonProjection(player, opponent), note: "BPW uses break-point creation with opponent-strength adjustment." };
    case "total_games": {
      const playerGames = gamesWonProjection(player, opponent);
      const opponentGames = opponent ? gamesWonProjection(opponent, player) : 10.9;
      return { value: playerGames + opponentGames, note: "Total games combines both players' projected games won." };
    }
    case "games_won":
      return { value: gamesWonProjection(player, opponent), note: "Games won uses historical win rate adjusted by opponent strength." };
    case "games_lost":
      return { value: opponent ? gamesWonProjection(opponent, player) : 10.9, note: "Games lost estimates the opponent's game-winning expectation." };
    case "sets_won":
      return { value: setsWonProjection(player, opponent), note: "Sets won uses historical win rate adjusted by opponent strength." };
    case "sets_lost":
      return { value: opponent ? setsWonProjection(opponent, player) : 1.1, note: "Sets lost estimates the opponent's set-winning expectation." };
    case "tiebreaks": {
      const totalGames = gamesWonProjection(player, opponent) + (opponent ? gamesWonProjection(opponent, player) : 10.9);
      const closeness = opponent ? 1 - Math.min(0.5, Math.abs(player.winPct - opponent.winPct)) : 0.75;
      return { value: clamp((totalGames - 20) * 0.08 * closeness, 0.05, 1.8), note: "Tiebreaks are estimated from projected match length and matchup closeness." };
    }
    case "service_games_won":
      return { value: clamp(gamesWonProjection(player, opponent) * 0.54 + aceProjection(player) * 0.05 - dfProjection(player) * 0.03, 0, 16), note: "Service games won are estimated from games won plus serve quality." };
    case "return_games_won":
      return { value: clamp(gamesWonProjection(player, opponent) * 0.46 - aceProjection(player) * 0.02, 0, 12), note: "Return games won are estimated as the return share of projected games won." };
    case "total_points_won":
      return { value: gamesWonProjection(player, opponent) * 4.25 + setsWonProjection(player, opponent) * 2.5, note: "Total points won are estimated from game volume and set share." };
    case "winners":
      return { value: clamp(10 + aceProjection(player) * 1.35 + gamesWonProjection(player, opponent) * 0.75, 5, 55), note: "Winners are estimated from ace production and offensive game volume." };
    case "unforced_errors":
      return { value: clamp(8 + dfProjection(player) * 1.55 + (opponent ? gamesWonProjection(opponent, player) : 10.9) * 0.65, 4, 55), note: "Unforced errors are estimated from double faults and defensive pressure." };
    case "fantasy_score":
    default:
      return { value: fantasyProjection(player, opponent), note: "Fantasy score uses match played, games, sets, aces, and double faults." };
  }
}

export function projectProp(
  player: PlayerSummary,
  market: string,
  line: number,
  requestedSide?: "Over" | "Under",
  opponent?: PlayerSummary | null
): PropProjection {
  const category = categoryFor(market);
  const projected = projectCategory(player, category.id, opponent);
  const projection = Number(projected.value.toFixed(2));
  const rawEdge = projection - line;
  const side: "Over" | "Under" | "Pass" = requestedSide ?? (rawEdge >= 0.5 ? "Over" : rawEdge <= -0.5 ? "Under" : "Pass");
  const edge = side === "Under" ? line - projection : rawEdge;
  const stability = clamp(Math.sqrt(player.matches) / 12, 0.1, 1);
  const distance = clamp(Math.abs(rawEdge) / Math.max(1, Math.abs(line)), 0, 0.35);
  const confidence = Math.round(clamp(50 + distance * 95 + stability * 16, 1, 92));

  return {
    player: player.name,
    opponent: opponent?.name,
    market: category.label,
    categoryId: category.id,
    side,
    line,
    projection,
    edge: Number(edge.toFixed(2)),
    confidence,
    sampleSize: player.matches,
    note: projected.note
  };
}
