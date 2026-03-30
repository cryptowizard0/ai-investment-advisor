import { NextResponse } from "next/server";

const backendBaseUrl = process.env.BACKEND_API_URL || "http://127.0.0.1:8000";

async function proxyExport(context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const response = await fetch(`${backendBaseUrl}/api/reports/${id}/export`, {
    method: "POST",
  });
  const body = await response.text();
  return new NextResponse(body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") ?? "text/plain; charset=utf-8",
    },
  });
}

export async function GET(_: Request, context: { params: Promise<{ id: string }> }) {
  return proxyExport(context);
}

export async function POST(_: Request, context: { params: Promise<{ id: string }> }) {
  return proxyExport(context);
}
