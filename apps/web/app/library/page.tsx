import Link from "next/link";

import { AppShell, Panel, StatusPill } from "@/components/shell";
import { backendFetch } from "@/lib/api";
import type { ReportRecord } from "@/lib/types";

export default async function LibraryPage() {
  const reports = await backendFetch<ReportRecord[]>("/api/library").catch(() => []);

  return (
    <AppShell>
      <Panel eyebrow="History" title="报告库">
        {reports.length === 0 ? (
          <p className="text-sm text-ink-500">还没有真实报告。先到 Workspace 发起一次分析。</p>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => (
              <Link
                key={report.id}
                href={`/report/${report.id}`}
                className="block rounded-2xl border border-white/10 bg-black/10 p-4 transition hover:border-white/20"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white">{report.title}</h3>
                    <p className="mt-1 text-xs text-ink-500">
                      Target: {report.target_value} · {report.analysis_mode}
                    </p>
                  </div>
                  <StatusPill tone={report.rating === "BUY" ? "positive" : report.rating === "WATCH" ? "warning" : "neutral"}>
                    {report.rating}
                  </StatusPill>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Panel>
    </AppShell>
  );
}
