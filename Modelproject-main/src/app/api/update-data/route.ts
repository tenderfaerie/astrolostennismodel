import { NextResponse } from "next/server";
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

export const dynamic = "force-dynamic";

const execFileAsync = promisify(execFile);

export async function POST() {
  try {
    const script = path.join(process.cwd(), "scripts", "update-sackmann.mjs");
    const { stdout } = await execFileAsync("node", [script], {
      cwd: process.cwd(),
      timeout: 180000,
    });
    const result = JSON.parse(stdout.trim());
    return NextResponse.json({ ok: true, ...result });
  } catch (error) {
    return NextResponse.json(
      { ok: false, error: error instanceof Error ? error.message : "Update failed" },
      { status: 500 }
    );
  }
}
