import Link from "next/link";

import { AppShell, Panel, StatusPill } from "@/components/shell";

export default function HomePage() {
  return (
    <AppShell>
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Panel eyebrow="Codex-style layout" title="三层架构投资 Agent 工作台">
          <p className="max-w-2xl text-sm leading-7 text-ink-200">
            前端只负责交互和报告阅读，后端负责任务编排和产品能力，Agent 层负责 skill 执行与深度分析产物。
            这套骨架已经把三层边界切开，后续可以直接把真实 `opencode` runtime 接到 Agent service。
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/app"
              className="rounded-full bg-accent-500 px-5 py-3 text-sm font-semibold text-ink-950 transition hover:bg-accent-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400"
            >
              打开工作台
            </Link>
            <Link
              href="/library"
              className="rounded-full border border-white/10 px-5 py-3 text-sm text-ink-200 transition hover:border-white/20 hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400"
            >
              查看报告库
            </Link>
          </div>
        </Panel>
        <Panel eyebrow="Layer ownership" title="系统职责">
          <div className="space-y-4 text-sm text-ink-200">
            <div>
              <div className="flex items-center justify-between">
                <strong className="text-white">Frontend</strong>
                <StatusPill tone="neutral">UI only</StatusPill>
              </div>
              <p className="mt-2">聊天、状态流、报告阅读、历史搜索。</p>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <strong className="text-white">Backend</strong>
                <StatusPill tone="positive">API orchestration</StatusPill>
              </div>
              <p className="mt-2">线程、job 状态机、report 索引、SSE。</p>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <strong className="text-white">Agent</strong>
                <StatusPill tone="warning">Runtime sandbox</StatusPill>
              </div>
              <p className="mt-2">skill 路由、artifact 采集、opencode 适配。</p>
            </div>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
