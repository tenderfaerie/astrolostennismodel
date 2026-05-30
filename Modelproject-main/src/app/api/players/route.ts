import { NextRequest, NextResponse } from "next/server";
import { searchPlayers } from "@/lib/historical";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q") ?? "";
  const players = await searchPlayers(query, 50);
  return NextResponse.json({ players });
}
