import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/api";

export async function GET() {
  const data = await backendFetch("/api/library");
  return NextResponse.json(data);
}
