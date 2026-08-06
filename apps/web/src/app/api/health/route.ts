import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({ service: "civitas-web", status: "ok" });
}
