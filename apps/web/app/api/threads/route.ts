import { NextResponse } from "next/server";
import { z } from "zod";

import { backendFetch } from "@/lib/api";

const schema = z.object({
  title: z.string().min(1),
  user_id: z.string().min(1).default("demo-user"),
});

export async function GET() {
  const data = await backendFetch("/api/threads");
  return NextResponse.json(data);
}

export async function POST(request: Request) {
  const body = schema.parse(await request.json());
  const data = await backendFetch("/api/threads", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return NextResponse.json(data);
}
