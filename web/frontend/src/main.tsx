import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import Markdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";

import "./styles.css";

type Report = {
  id: string;
  category: string;
  skill: string;
  date: string;
  title: string;
  dupeGroup: string;
  isLatestInGroup: boolean;
};

type ReportGroup = {
  id: string;
  latest: Report;
  older: Report[];
};

const CATEGORY_ORDER = ["chain-alpha", "monitor", "research"];

function reportIdFromHash(): string {
  return decodeURIComponent(window.location.hash.slice(1));
}

function ReportButton({
  report,
  selectedId,
  onSelect,
  versionLabel,
}: {
  report: Report;
  selectedId: string;
  onSelect: (id: string) => void;
  versionLabel?: string;
}) {
  return (
    <button
      className={`report-item${report.id === selectedId ? " active" : ""}`}
      type="button"
      onClick={() => onSelect(report.id)}
      aria-current={report.id === selectedId ? "page" : undefined}
    >
      <span className="report-title">{report.title}</span>
      <span className="report-meta">
        <span>{report.date || "无日期"}</span>
        <span>{report.skill}</span>
        {versionLabel && <span>{versionLabel}</span>}
      </span>
    </button>
  );
}

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedId, setSelectedId] = useState(reportIdFromHash);
  const [markdown, setMarkdown] = useState("");
  const [listError, setListError] = useState("");
  const [readerError, setReaderError] = useState("");
  const [loadingReports, setLoadingReports] = useState(true);
  const [loadingMarkdown, setLoadingMarkdown] = useState(false);

  useEffect(() => {
    const loadReports = async () => {
      try {
        const response = await fetch("/api/reports", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`报告列表请求失败（${response.status}）`);
        }
        setReports(await response.json());
      } catch (error) {
        setListError(
          error instanceof Error ? error.message : "无法加载报告列表",
        );
      } finally {
        setLoadingReports(false);
      }
    };

    void loadReports();
  }, []);

  useEffect(() => {
    const onHashChange = () => setSelectedId(reportIdFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    if (reports.length === 0) {
      return;
    }

    const selectedReportExists = reports.some(
      (report) => report.id === selectedId,
    );
    if (!selectedReportExists) {
      const firstReportId = reports[0].id;
      setSelectedId(firstReportId);
      window.history.replaceState(
        null,
        "",
        `${window.location.pathname}${window.location.search}#${encodeURIComponent(firstReportId)}`,
      );
    }
  }, [reports, selectedId]);

  useEffect(() => {
    if (!selectedId || !reports.some((report) => report.id === selectedId)) {
      setMarkdown("");
      return;
    }

    const controller = new AbortController();
    const loadMarkdown = async () => {
      setLoadingMarkdown(true);
      setReaderError("");
      try {
        const response = await fetch(
          `/api/reports/${encodeURIComponent(selectedId)}/raw`,
          { cache: "no-store", signal: controller.signal },
        );
        if (!response.ok) {
          throw new Error(`报告正文请求失败（${response.status}）`);
        }
        setMarkdown(await response.text());
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setReaderError(
          error instanceof Error ? error.message : "无法加载报告正文",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoadingMarkdown(false);
        }
      }
    };

    void loadMarkdown();
    return () => controller.abort();
  }, [reports, selectedId]);

  const reportsByCategory = useMemo(() => {
    const reportsByGroup = new Map<string, Report[]>();
    for (const report of reports) {
      const groupReports = reportsByGroup.get(report.dupeGroup) ?? [];
      groupReports.push(report);
      reportsByGroup.set(report.dupeGroup, groupReports);
    }

    const grouped = new Map<string, ReportGroup[]>();
    for (const [id, groupReports] of reportsByGroup) {
      const latest =
        groupReports.find((report) => report.isLatestInGroup) ?? groupReports[0];
      const reportGroup = {
        id,
        latest,
        older: groupReports.filter((report) => report.id !== latest.id),
      };
      const categoryGroups = grouped.get(latest.category) ?? [];
      categoryGroups.push(reportGroup);
      grouped.set(latest.category, categoryGroups);
    }

    return [...grouped.entries()].sort(
      ([left], [right]) =>
        CATEGORY_ORDER.indexOf(left) - CATEGORY_ORDER.indexOf(right),
    );
  }, [reports]);

  const selectedReport = reports.find((report) => report.id === selectedId);
  const latestReport =
    reports.find((report) => report.isLatestInGroup && report.date) ??
    reports.find((report) => report.isLatestInGroup);
  const latestDate = latestReport?.date || "—";

  const selectReport = (id: string) => {
    setSelectedId(id);
    window.location.hash = encodeURIComponent(id);
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            IA
          </span>
          <div>
            <p className="eyebrow">LOCAL RESEARCH LIBRARY</p>
            <h1>投资报告阅读器</h1>
          </div>
        </div>
        <dl className="overview" aria-label="报告概览">
          <div>
            <dt>报告总数</dt>
            <dd>{reports.length}</dd>
          </div>
          <div>
            <dt>分类数</dt>
            <dd>{new Set(reports.map((report) => report.category)).size}</dd>
          </div>
          <div>
            <dt>最新日期</dt>
            <dd>{latestDate}</dd>
          </div>
          <div className="latest-report">
            <dt>最新报告</dt>
            <dd>
              {latestReport ? (
                <button
                  type="button"
                  onClick={() => selectReport(latestReport.id)}
                >
                  {latestReport.title}
                </button>
              ) : (
                "—"
              )}
            </dd>
          </div>
        </dl>
      </header>

      <div className="workspace">
        <aside className="sidebar" aria-label="报告列表">
          <div className="sidebar-heading">
            <div>
              <p className="eyebrow">REPORTS</p>
              <h2>全部报告</h2>
            </div>
            <span>{reports.length}</span>
          </div>

          {loadingReports && <p className="state-message">正在扫描报告…</p>}
          {listError && <p className="state-message error">{listError}</p>}
          {!loadingReports && !listError && reports.length === 0 && (
            <p className="state-message">当前没有 Markdown 报告。</p>
          )}

          <nav className="report-list">
            {reportsByCategory.map(([category, categoryGroups]) => (
              <section className="category-group" key={category}>
                <div className="category-label">
                  <span>{category}</span>
                  <span>{categoryGroups.length}</span>
                </div>
                {categoryGroups.map((group) => (
                  <div className="report-group" key={group.id}>
                    <ReportButton
                      report={group.latest}
                      selectedId={selectedId}
                      onSelect={selectReport}
                    />
                    {group.older.length > 0 && (
                      <details className="revision-list">
                        <summary>
                          <span>旧版本</span>
                          <span>{group.older.length}</span>
                        </summary>
                        <div className="revision-items">
                          {group.older.map((report, index) => (
                            <ReportButton
                              key={report.id}
                              report={report}
                              selectedId={selectedId}
                              onSelect={selectReport}
                              versionLabel={`旧版 ${index + 1}`}
                            />
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                ))}
              </section>
            ))}
          </nav>
        </aside>

        <article className="reader">
          {selectedReport && (
            <header className="reader-header">
              <div className="document-path">
                <span>{selectedReport.category}</span>
                <span aria-hidden="true">/</span>
                <span>{selectedReport.skill}</span>
              </div>
              <div className="reader-date">
                {selectedReport.date || "无日期"}
              </div>
            </header>
          )}

          <div className="document">
            {loadingMarkdown && (
              <p className="state-message">正在打开报告…</p>
            )}
            {readerError && (
              <p className="state-message error">{readerError}</p>
            )}
            {!selectedReport && !loadingReports && (
              <div className="empty-reader">
                <span aria-hidden="true">⌘</span>
                <h2>选择一篇报告开始阅读</h2>
                <p>报告会在这里以完整的 GitHub Flavored Markdown 呈现。</p>
              </div>
            )}
            {!loadingMarkdown && !readerError && markdown && (
              <div className="markdown-body">
                <Markdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                >
                  {markdown}
                </Markdown>
              </div>
            )}
          </div>
        </article>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
