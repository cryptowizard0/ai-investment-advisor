"use client";

import Link from "next/link";
import { useState } from "react";
import type { Dispatch, SetStateAction } from "react";

import { Panel, StatusPill } from "@/components/shell";
import type { JobEvent, JobRecord, ThreadSummary } from "@/lib/types";

type Message = {
  id: string;
  role: "user" | "system";
  content: string;
};

type ThreadWorkspaceState = {
  messages: Message[];
  events: JobEvent[];
  job: JobRecord | null;
  reportId: string | null;
};

export function WorkspaceClient({ initialThreads }: { initialThreads: ThreadSummary[] }) {
  const [threads, setThreads] = useState(initialThreads);
  const [activeThreadId, setActiveThreadId] = useState(initialThreads[0]?.id ?? "");
  const [prompt, setPrompt] = useState("请给我做一份 TSLA 的深度分析报告，偏平衡型风险。");
  const [threadStates, setThreadStates] = useState<Record<string, ThreadWorkspaceState>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formStatus, setFormStatus] = useState("");

  const activeState = activeThreadId ? threadStates[activeThreadId] ?? emptyThreadState() : emptyThreadState();

  async function handleSubmit() {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setFormStatus("");

    let threadId = activeThreadId;
    try {
      const targetValue = extractTargetValue(trimmedPrompt);
      threadId = activeThreadId || (await createThread(targetValue, setThreads, setActiveThreadId));

      updateThreadState(setThreadStates, threadId, (current) => ({
        ...current,
        messages: [
          ...current.messages,
          { id: crypto.randomUUID(), role: "user", content: trimmedPrompt },
          {
            id: crypto.randomUUID(),
            role: "system",
            content: "后端已接收请求，正在创建分析任务并调用 Agent service。",
          },
        ],
        events: [],
        job: null,
        reportId: null,
      }));

      const response = await fetch(`/api/threads/${threadId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmedPrompt,
          analysis_mode: inferAnalysisMode(trimmedPrompt),
          target_type: inferTargetType(trimmedPrompt),
          target_value: targetValue,
          selected_skill_profile: inferSkillProfile(trimmedPrompt),
          preferred_language: "zh-CN",
          risk_profile: "balanced",
          user_id: "demo-user",
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        updateThreadState(setThreadStates, threadId, (current) => ({
          ...current,
          messages: [
            ...current.messages,
            { id: crypto.randomUUID(), role: "system", content: `任务创建失败：${text}` },
          ],
        }));
        return;
      }

      const created = (await response.json()) as { job_id: string; status: string };
      await subscribeToJob(created.job_id, threadId, setThreadStates);
      const jobDetail = await fetch(`/api/jobs/${created.job_id}`, { cache: "no-store" }).then((res) => res.json());
      updateThreadState(setThreadStates, threadId, (current) => ({
        ...current,
        job: jobDetail.job as JobRecord,
        reportId: jobDetail.report_id,
        messages: [
          ...current.messages,
          {
            id: crypto.randomUUID(),
            role: "system",
            content: jobDetail.report_id
              ? "分析完成，报告已生成。右侧面板可以直接打开真实报告。"
              : "任务执行完成，但当前没有生成可用报告。",
          },
        ],
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      if (threadId) {
        updateThreadState(setThreadStates, threadId, (current) => ({
          ...current,
          messages: [
            ...current.messages,
            { id: crypto.randomUUID(), role: "system", content: `请求失败：${message}` },
          ],
        }));
      } else {
        setFormStatus(`请求失败：${message}`);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_360px]">
      <Panel eyebrow="Threads" title="研究会话">
        <div className="space-y-3">
          {threads.length === 0 ? (
            <p className="text-sm text-ink-500">还没有会话。提交第一条分析请求后会自动创建。</p>
          ) : (
            threads.map((thread) => (
              <button
                key={thread.id}
                type="button"
                onClick={() => setActiveThreadId(thread.id)}
                className={`block w-full rounded-2xl border p-4 text-left transition ${
                  activeThreadId === thread.id
                    ? "border-accent-500/40 bg-accent-500/10"
                    : "border-white/10 bg-black/10 hover:border-white/20"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-medium text-white">{thread.title}</h3>
                  <StatusPill tone={activeThreadId === thread.id ? "positive" : "neutral"}>
                    {activeThreadId === thread.id ? "active" : "idle"}
                  </StatusPill>
                </div>
                <p className="mt-2 text-xs text-ink-500">{formatTime(thread.created_at)}</p>
              </button>
            ))
          )}
        </div>
      </Panel>

      <Panel eyebrow="Conversation" title="Agent 对话">
        <div className="space-y-4">
          {activeState.messages.length === 0 ? (
            <div className="rounded-3xl border border-white/10 bg-black/10 p-4 text-sm leading-7 text-ink-200">
              前端现在会真实调用 Backend 创建 thread 和 message。你发出请求后，右侧会显示真实 job 事件和报告入口。
            </div>
          ) : (
            activeState.messages.map((message) => (
              <div
                key={message.id}
                className={`rounded-3xl p-4 ${
                  message.role === "user"
                    ? "border border-accent-500/20 bg-accent-500/8"
                    : "border border-white/10 bg-black/10"
                }`}
              >
                <p
                  className={`font-mono text-xs uppercase tracking-[0.28em] ${
                    message.role === "user" ? "text-accent-400" : "text-ink-500"
                  }`}
                >
                  {message.role === "user" ? "User" : "System"}
                </p>
                <p className="mt-2 text-sm leading-7 text-ink-200">{message.content}</p>
              </div>
            ))
          )}

          <form
            className="rounded-3xl border border-white/10 bg-white/5 p-4"
            onSubmit={(event) => {
              event.preventDefault();
              void handleSubmit();
            }}
          >
            <label htmlFor="prompt" className="text-sm text-ink-300">
              发起分析
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="mt-3 min-h-28 w-full rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white outline-none placeholder:text-ink-500 focus-visible:ring-2 focus-visible:ring-accent-400"
              placeholder="例如：请给我做一份 TSLA 的深度分析报告，偏平衡型风险。"
              spellCheck={false}
            />
            <div className="mt-3 flex items-center justify-between gap-3">
              <span aria-live="polite" className="text-xs text-ink-500">
                {formStatus || (isSubmitting ? "正在提交到真实后端..." : "Frontend 只走 Backend API。")}
              </span>
              <button
                type="submit"
                className="rounded-full bg-accent-500 px-4 py-2 text-sm font-medium text-ink-950 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isSubmitting}
              >
                {isSubmitting ? "处理中..." : "发送"}
              </button>
            </div>
          </form>
        </div>
      </Panel>

      <Panel eyebrow="Execution" title="任务与报告">
        <div className="space-y-5">
          <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
            <div className="flex items-center justify-between">
              <strong className="text-sm text-white">Agent 状态</strong>
              <StatusPill tone={jobTone(activeState.job?.status)}>{activeState.job?.status ?? "idle"}</StatusPill>
            </div>
            <ul className="mt-4 space-y-2 font-mono text-xs text-ink-300">
              {activeState.events.length === 0 ? (
                <li className="rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-ink-500">
                  等待任务开始。提交请求后，这里会显示真实 job 事件。
                </li>
              ) : (
                activeState.events.map((event) => (
                  <li key={event.id} className="rounded-xl border border-white/5 bg-white/5 px-3 py-2">
                    {event.event}: {event.message}
                  </li>
                ))
              )}
            </ul>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p className="font-mono text-xs uppercase tracking-[0.28em] text-ink-500">Artifacts</p>
            <h3 className="mt-2 text-sm font-semibold text-white">
              {activeState.job?.result?.report_summary?.title ?? "尚未生成报告"}
            </h3>
            <p className="mt-2 text-sm leading-7 text-ink-200">
              {activeState.job?.result?.report_summary?.summary ??
                "Agent 层会真实生成 Markdown 与 JSON，Backend 负责索引和分发。"}
            </p>
            <div className="mt-4 flex gap-3">
              {activeState.reportId ? (
                <Link
                  href={`/report/${activeState.reportId}`}
                  className="rounded-full border border-white/10 px-4 py-2 text-sm text-ink-200"
                >
                  打开报告
                </Link>
              ) : (
                <span className="rounded-full border border-white/10 px-4 py-2 text-sm text-ink-500">
                  等待报告
                </span>
              )}
              {activeState.reportId ? (
                <a
                  href={`/api/reports/${activeState.reportId}/export`}
                  className="rounded-full bg-white/10 px-4 py-2 text-sm text-white"
                >
                  导出 Markdown
                </a>
              ) : null}
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}

async function createThread(
  targetValue: string,
  setThreads: Dispatch<SetStateAction<ThreadSummary[]>>,
  setActiveThreadId: Dispatch<SetStateAction<string>>,
) {
  const response = await fetch("/api/threads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: `${targetValue} 分析`, user_id: "demo-user" }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const thread = (await response.json()) as ThreadSummary;
  setThreads((current) => [thread, ...current]);
  setActiveThreadId(thread.id);
  return thread.id;
}

async function subscribeToJob(
  jobId: string,
  threadId: string,
  setThreadStates: Dispatch<SetStateAction<Record<string, ThreadWorkspaceState>>>,
) {
  await new Promise<void>((resolve) => {
    const source = new EventSource(`/api/jobs/${jobId}/stream`);

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as JobEvent;
      updateThreadState(setThreadStates, threadId, (current) => {
        if (current.events.some((item) => item.id === payload.id)) {
          return current;
        }
        return { ...current, events: [...current.events, payload] };
      });
      if (
        payload.event === "run.completed" ||
        payload.event === "run.failed" ||
        payload.event === "job.canceled"
      ) {
        source.close();
        resolve();
      }
    };

    source.onerror = () => {
      source.close();
      resolve();
    };
  });
}

function extractTargetValue(prompt: string) {
  const match = prompt.match(/\b[A-Z]{1,5}\b/);
  return match?.[0] ?? prompt.slice(0, 24);
}

function inferAnalysisMode(prompt: string) {
  if (prompt.includes("快速") || prompt.toLowerCase().includes("quick")) {
    return "quick_scan";
  }
  if (prompt.includes("主题")) {
    return "theme_research";
  }
  return "deep_report";
}

function inferTargetType(prompt: string) {
  if (prompt.includes("主题")) {
    return "theme";
  }
  const hasTicker = /\b[A-Z]{1,5}\b/.test(prompt);
  return hasTicker ? "ticker" : "question";
}

function inferSkillProfile(prompt: string) {
  if (prompt.toLowerCase().includes("gold")) {
    return "gold-trend-analysis";
  }
  if (prompt.includes("快速")) {
    return "reflexivity-quick-scan";
  }
  return "chief-investment-advisor";
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function jobTone(status: JobRecord["status"] | undefined) {
  if (status === "completed") {
    return "positive";
  }
  if (status === "failed" || status === "canceled") {
    return "warning";
  }
  return "neutral";
}

function emptyThreadState(): ThreadWorkspaceState {
  return {
    messages: [],
    events: [],
    job: null,
    reportId: null,
  };
}

function updateThreadState(
  setThreadStates: Dispatch<SetStateAction<Record<string, ThreadWorkspaceState>>>,
  threadId: string,
  updater: (current: ThreadWorkspaceState) => ThreadWorkspaceState,
) {
  setThreadStates((current) => ({
    ...current,
    [threadId]: updater(current[threadId] ?? emptyThreadState()),
  }));
}
