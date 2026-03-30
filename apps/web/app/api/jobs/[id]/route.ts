import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/api";

export async function GET(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const data = await backendFetch(`/api/jobs/${id}`);
  return NextResponse.json(data);
}
