import { AppShell, Panel } from "@/components/shell";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel eyebrow="Backend" title="产品层配置">
          <ul className="space-y-3 text-sm text-ink-200">
            <li>鉴权与订阅在 Backend 管理。</li>
            <li>Frontend 只通过公开 API 读取 job 与 report。</li>
            <li>Agent service 不直接暴露给浏览器。</li>
          </ul>
        </Panel>
        <Panel eyebrow="Agent" title="分析引擎配置">
          <ul className="space-y-3 text-sm text-ink-200">
            <li>Skill 根目录：`.agents/skills/`</li>
            <li>默认 profile：`chief-investment-advisor`</li>
            <li>输出目录：`output/web-agent-runs/`</li>
          </ul>
        </Panel>
      </div>
    </AppShell>
  );
}
