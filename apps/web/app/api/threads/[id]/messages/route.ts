import { NextResponse } from "next/server";
import { z } from "zod";

import { backendFetch } from "@/lib/api";

const schema = z.object({
  question: z.string().min(1),
  analysis_mode: z.enum(["deep_report", "quick_scan", "theme_research"]).default("deep_report"),
  target_type: z.enum(["ticker", "theme", "question"]).default("ticker"),
  target_value: z.string().min(1),
  risk_profile: z.enum(["conservative", "balanced", "aggressive"]).default("balanced"),
  preferred_language: z.enum(["zh-CN", "en-US"]).default("zh-CN"),
  selected_skill_profile: z.string().min(1).default("chief-investment-advisor"),
  user_id: z.string().min(1).default("demo-user"),
});

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const body = schema.parse(await request.json());
  const { id } = await context.params;
  const data = await backendFetch(`/api/threads/${id}/messages`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  return NextResponse.json(data);
}
