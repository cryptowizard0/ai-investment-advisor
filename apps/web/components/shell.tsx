import Link from "next/link";
import { BarChart3, FileText, MessageSquare, Settings } from "lucide-react";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-transparent">
      <header className="border-b border-white/10 bg-black/10 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.32em] text-accent-400">
              Investment Agent Workspace
            </p>
            <h1 className="mt-1 text-lg font-semibold text-white">Three-Layer Research Console</h1>
          </div>
          <nav className="flex items-center gap-2 text-sm text-ink-300">
            <ShellLink href="/app" icon={<MessageSquare className="h-4 w-4" />} label="Workspace" />
            <ShellLink href="/library" icon={<FileText className="h-4 w-4" />} label="Library" />
            <ShellLink href="/settings" icon={<Settings className="h-4 w-4" />} label="Settings" />
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">{children}</main>
    </div>
  );
}

function ShellLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 transition-colors hover:border-accent-400/50 hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400"
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
}

export function Panel({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
      {eyebrow ? (
        <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-500">{eyebrow}</p>
      ) : null}
      <h2 className="mt-2 text-base font-semibold text-white">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function StatusPill({ tone, children }: { tone: "neutral" | "positive" | "warning"; children: React.ReactNode }) {
  const styles = {
    neutral: "border-white/10 bg-white/5 text-ink-300",
    positive: "border-accent-500/30 bg-accent-500/10 text-accent-400",
    warning: "border-alert-500/30 bg-alert-500/10 text-alert-500",
  }[tone];

  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs ${styles}`}>{children}</span>;
}
