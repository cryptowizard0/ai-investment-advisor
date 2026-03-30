import { AppShell } from "@/components/shell";
import { WorkspaceClient } from "@/components/workspace-client";
import { backendFetch } from "@/lib/api";
import type { ThreadSummary } from "@/lib/types";

export default async function WorkspacePage() {
  const initialThreads = await backendFetch<ThreadSummary[]>("/api/threads").catch(() => []);

  return (
    <AppShell>
      <WorkspaceClient initialThreads={initialThreads} />
    </AppShell>
  );
}
