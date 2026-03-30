import { NextResponse } from "next/server";

const backendBaseUrl = process.env.BACKEND_API_URL || "http://127.0.0.1:8000";

export async function GET(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const response = await fetch(`${backendBaseUrl}/api/jobs/${id}/stream`, { cache: "no-store" });
  return new NextResponse(response.body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") ?? "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
