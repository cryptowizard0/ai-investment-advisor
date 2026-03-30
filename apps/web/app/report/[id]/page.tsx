import ReactMarkdown from "react-markdown";

import { AppShell, Panel, StatusPill } from "@/components/shell";
import { backendFetch } from "@/lib/api";
import type { ReportRecord } from "@/lib/types";

export default async function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = await backendFetch<ReportRecord>(`/api/reports/${id}`);

  return (
    <AppShell>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <Panel eyebrow="Markdown viewer" title="报告详情">
          <article className="prose prose-invert max-w-none prose-headings:font-semibold prose-p:text-ink-200">
            <ReactMarkdown>{report.markdown}</ReactMarkdown>
          </article>
        </Panel>
        <Panel eyebrow="Meta" title="报告元数据">
          <div className="space-y-4 text-sm text-ink-200">
            <div className="flex items-center justify-between">
              <span>评级</span>
              <StatusPill tone={report.rating === "BUY" ? "positive" : report.rating === "WATCH" ? "warning" : "neutral"}>
                {report.rating}
              </StatusPill>
            </div>
            <div className="flex items-center justify-between">
              <span>目标</span>
              <span>{report.target_value}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>分析模式</span>
              <span>{report.analysis_mode}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>创建时间</span>
              <span>{new Intl.DateTimeFormat("zh-CN", { dateStyle: "short", timeStyle: "short" }).format(new Date(report.created_at))}</span>
            </div>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
