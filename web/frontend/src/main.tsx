import { StrictMode, useEffect, useMemo, useRef, useState } from "react";
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
  tickers: string[];
  themes: string[];
  dupeGroup: string;
  isLatestInGroup: boolean;
  snippet?: string;
};

type ReportGroup = {
  id: string;
  latest: Report;
  older: Report[];
};

type ReportEvent = {
  type: "added" | "updated" | "removed";
  report: Report;
};

type FacetOption = {
  value: string;
  count: number;
};

type Facets = {
  skills: FacetOption[];
  categories: FacetOption[];
  tickers: FacetOption[];
  themes: FacetOption[];
  dateRange: {
    min: string;
    max: string;
  };
};

const CATEGORY_ORDER = ["chain-alpha", "monitor", "research"];
const EMPTY_FACETS: Facets = {
  skills: [],
  categories: [],
  tickers: [],
  themes: [],
  dateRange: { min: "", max: "" },
};

function reportIdFromHash(): string {
  return decodeURIComponent(window.location.hash.slice(1));
}

function toggledValues(values: string[], value: string): string[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

async function fetchNoStore(
  endpoint: string,
  signal: AbortSignal,
  failureMessage: string,
): Promise<Response> {
  const response = await fetch(endpoint, {
    cache: "no-store",
    signal,
  });
  if (!response.ok) {
    throw new Error(`${failureMessage}（${response.status}）`);
  }
  return response;
}

function HighlightedSnippet({ snippet }: { snippet: string }) {
  return (
    <span className="search-snippet">
      {snippet.split("<mark>").map((section, index) => {
        const closingMarker = section.indexOf("</mark>");
        if (index === 0 || closingMarker === -1) {
          return <span key={index}>{section}</span>;
        }
        return (
          <span key={index}>
            <mark>{section.slice(0, closingMarker)}</mark>
            {section.slice(closingMarker + "</mark>".length)}
          </span>
        );
      })}
    </span>
  );
}

function ReportButton({
  report,
  selectedId,
  onSelect,
  highlightedId,
  versionLabel,
}: {
  report: Report;
  selectedId: string;
  onSelect: (id: string) => void;
  highlightedId: string;
  versionLabel?: string;
}) {
  return (
    <button
      className={[
        "report-item",
        report.id === selectedId ? "active" : "",
        report.id === highlightedId ? "recent" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      type="button"
      onClick={() => onSelect(report.id)}
      aria-current={report.id === selectedId ? "page" : undefined}
    >
      <span className="report-title">{report.title}</span>
      {report.snippet && <HighlightedSnippet snippet={report.snippet} />}
      <span className="report-meta">
        <span>{report.date || "无日期"}</span>
        <span>{report.skill}</span>
        {versionLabel && <span>{versionLabel}</span>}
      </span>
    </button>
  );
}

function FacetChips({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: FacetOption[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div className="facet-group">
      <p>{label}</p>
      <div className="facet-chips">
        {options.map((option) => {
          const isSelected = selected.includes(option.value);
          return (
            <button
              className={isSelected ? "active" : ""}
              type="button"
              key={option.value}
              onClick={() => onToggle(option.value)}
              aria-pressed={isSelected}
            >
              <span>{option.value}</span>
              <span>{option.count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [facets, setFacets] = useState<Facets>(EMPTY_FACETS);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedId, setSelectedId] = useState(reportIdFromHash);
  const [markdown, setMarkdown] = useState("");
  const [listError, setListError] = useState("");
  const [facetError, setFacetError] = useState("");
  const [readerError, setReaderError] = useState("");
  const [loadingReports, setLoadingReports] = useState(true);
  const [loadingMarkdown, setLoadingMarkdown] = useState(false);
  const [eventRevision, setEventRevision] = useState(0);
  const [readerRevision, setReaderRevision] = useState(0);
  const [highlightedId, setHighlightedId] = useState("");
  const [staleReportId, setStaleReportId] = useState("");
  const selectedIdRef = useRef(selectedId);
  const listIsScopedRef = useRef(false);
  const connectionInterruptedRef = useRef(false);
  const highlightTimer = useRef<number | undefined>(undefined);
  const normalizedSearchQuery = searchQuery.trim();
  const selectedReportExists = reports.some(
    (report) => report.id === selectedId,
  );

  const reportQuery = useMemo(() => {
    const params = new URLSearchParams();
    selectedCategories.forEach((value) => params.append("category", value));
    selectedSkills.forEach((value) => params.append("skill", value));
    selectedTickers.forEach((value) => params.append("ticker", value));
    selectedThemes.forEach((value) => params.append("theme", value));
    if (dateFrom) {
      params.set("date_from", dateFrom);
    }
    if (dateTo) {
      params.set("date_to", dateTo);
    }
    return params.toString();
  }, [
    dateFrom,
    dateTo,
    selectedCategories,
    selectedSkills,
    selectedThemes,
    selectedTickers,
  ]);

  useEffect(() => {
    const controller = new AbortController();
    const loadReports = async () => {
      setLoadingReports(true);
      setListError("");
      try {
        const params = new URLSearchParams(reportQuery);
        if (normalizedSearchQuery) {
          params.set("q", normalizedSearchQuery);
        }
        const endpoint = normalizedSearchQuery
          ? `/api/search?${params.toString()}`
          : reportQuery
            ? `/api/reports?${reportQuery}`
            : "/api/reports";
        const response = await fetchNoStore(
          endpoint,
          controller.signal,
          normalizedSearchQuery ? "全文搜索请求失败" : "报告列表请求失败",
        );
        setReports(await response.json());
      } catch (error) {
        if (isAbortError(error)) {
          return;
        }
        setListError(
          error instanceof Error ? error.message : "无法加载报告列表",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoadingReports(false);
        }
      }
    };

    void loadReports();
    return () => controller.abort();
  }, [eventRevision, normalizedSearchQuery, reportQuery]);

  useEffect(() => {
    const controller = new AbortController();
    const loadFacets = async () => {
      try {
        const response = await fetchNoStore(
          "/api/facets",
          controller.signal,
          "筛选项请求失败",
        );
        setFacets(await response.json());
      } catch (error) {
        if (isAbortError(error)) {
          return;
        }
        setFacetError(
          error instanceof Error ? error.message : "无法加载筛选项",
        );
      }
    };

    void loadFacets();
    return () => controller.abort();
  }, [eventRevision]);

  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);

  useEffect(() => {
    listIsScopedRef.current = Boolean(normalizedSearchQuery || reportQuery);
  }, [normalizedSearchQuery, reportQuery]);

  useEffect(() => {
    const source = new EventSource("/api/events");
    source.onopen = () => {
      if (connectionInterruptedRef.current && selectedIdRef.current) {
        setStaleReportId(selectedIdRef.current);
      }
      connectionInterruptedRef.current = false;
      setEventRevision((value) => value + 1);
    };
    source.onerror = () => {
      connectionInterruptedRef.current = true;
    };
    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as ReportEvent;
      if (!event.report?.id) {
        return;
      }

      setReports((current) => {
        const remaining = current.filter(
          (report) => report.id !== event.report.id,
        );
        if (event.type === "removed") {
          return remaining;
        }
        if (event.type === "added" && listIsScopedRef.current) {
          return current;
        }
        return [...remaining, event.report].sort((left, right) =>
          [right.date, right.title, right.id]
            .join("\0")
            .localeCompare([left.date, left.title, left.id].join("\0")),
        );
      });
      setEventRevision((value) => value + 1);

      if (event.type !== "removed") {
        setHighlightedId(event.report.id);
        if (highlightTimer.current !== undefined) {
          window.clearTimeout(highlightTimer.current);
        }
        highlightTimer.current = window.setTimeout(() => {
          setHighlightedId("");
        }, 2400);
      }
      if (
        event.type === "updated" &&
        event.report.id === selectedIdRef.current
      ) {
        setStaleReportId(event.report.id);
      }
    };

    return () => {
      source.close();
      if (highlightTimer.current !== undefined) {
        window.clearTimeout(highlightTimer.current);
      }
    };
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

    if (!selectedReportExists) {
      const firstReportId =
        reports.find((report) => report.isLatestInGroup)?.id ?? reports[0].id;
      setSelectedId(firstReportId);
      window.history.replaceState(
        null,
        "",
        `${window.location.pathname}${window.location.search}#${encodeURIComponent(firstReportId)}`,
      );
    }
  }, [reports, selectedId, selectedReportExists]);

  useEffect(() => {
    if (!selectedId || !selectedReportExists) {
      setMarkdown("");
      return;
    }

    const controller = new AbortController();
    const loadMarkdown = async () => {
      setLoadingMarkdown(true);
      setReaderError("");
      try {
        const response = await fetchNoStore(
          `/api/reports/${encodeURIComponent(selectedId)}/raw`,
          controller.signal,
          "报告正文请求失败",
        );
        setMarkdown(await response.text());
      } catch (error) {
        if (isAbortError(error)) {
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
  }, [readerRevision, selectedId, selectedReportExists]);

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
  const hasActiveFilters = reportQuery.length > 0;
  const hasSearchQuery = normalizedSearchQuery.length > 0;
  const activeFilterCount =
    selectedCategories.length +
    selectedSkills.length +
    selectedTickers.length +
    selectedThemes.length +
    Number(Boolean(dateFrom)) +
    Number(Boolean(dateTo));

  const selectReport = (id: string) => {
    setSelectedId(id);
    window.location.hash = encodeURIComponent(id);
  };

  const clearFilters = () => {
    setSelectedCategories([]);
    setSelectedSkills([]);
    setSelectedTickers([]);
    setSelectedThemes([]);
    setDateFrom("");
    setDateTo("");
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
              <h2>
                {hasSearchQuery
                  ? "搜索结果"
                  : hasActiveFilters
                    ? "筛选结果"
                    : "全部报告"}
              </h2>
            </div>
            <span>{reports.length}</span>
          </div>

          <div className="search-panel">
            <label htmlFor="report-search">全文搜索</label>
            <div>
              <input
                id="report-search"
                type="search"
                value={searchQuery}
                placeholder="搜索正文片段或 ticker"
                onChange={(event) => setSearchQuery(event.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  aria-label="清除搜索"
                >
                  ×
                </button>
              )}
            </div>
          </div>

          <section className="facet-panel" aria-label="报告筛选">
            <header>
              <div>
                <span>筛选</span>
                {activeFilterCount > 0 && <span>{activeFilterCount}</span>}
              </div>
              <button
                type="button"
                onClick={clearFilters}
                disabled={!hasActiveFilters}
              >
                清除
              </button>
            </header>

            <FacetChips
              label="主题类"
              options={facets.categories}
              selected={selectedCategories}
              onToggle={(value) =>
                setSelectedCategories(
                  toggledValues(selectedCategories, value),
                )
              }
            />
            <FacetChips
              label="Skill"
              options={facets.skills}
              selected={selectedSkills}
              onToggle={(value) =>
                setSelectedSkills(toggledValues(selectedSkills, value))
              }
            />
            <FacetChips
              label="标的 ticker"
              options={facets.tickers}
              selected={selectedTickers}
              onToggle={(value) =>
                setSelectedTickers(toggledValues(selectedTickers, value))
              }
            />
            <FacetChips
              label="产业链主题"
              options={facets.themes}
              selected={selectedThemes}
              onToggle={(value) =>
                setSelectedThemes(toggledValues(selectedThemes, value))
              }
            />

            <div className="facet-group">
              <p>日期区间</p>
              <div className="date-range">
                <label>
                  <span>从</span>
                  <input
                    type="date"
                    value={dateFrom}
                    min={facets.dateRange.min || undefined}
                    max={dateTo || facets.dateRange.max || undefined}
                    onChange={(event) => setDateFrom(event.target.value)}
                  />
                </label>
                <label>
                  <span>至</span>
                  <input
                    type="date"
                    value={dateTo}
                    min={dateFrom || facets.dateRange.min || undefined}
                    max={facets.dateRange.max || undefined}
                    onChange={(event) => setDateTo(event.target.value)}
                  />
                </label>
              </div>
            </div>

            {facetError && (
              <p className="facet-error" role="alert">
                {facetError}
              </p>
            )}
          </section>

          {loadingReports && (
            <p className="state-message">
              {hasSearchQuery ? "正在搜索报告…" : "正在扫描报告…"}
            </p>
          )}
          {listError && <p className="state-message error">{listError}</p>}
          {!loadingReports && !listError && reports.length === 0 && (
            <p className="state-message">
              {hasSearchQuery
                ? "没有匹配当前正文片段与筛选条件的报告。"
                : hasActiveFilters
                ? "没有符合当前筛选条件的报告。"
                : "当前没有 Markdown 报告。"}
            </p>
          )}

          <nav className="report-list">
            {hasSearchQuery
              ? reports.map((report) => (
                  <ReportButton
                    key={report.id}
                    report={report}
                    selectedId={selectedId}
                    onSelect={selectReport}
                    highlightedId={highlightedId}
                  />
                ))
              : reportsByCategory.map(([category, categoryGroups]) => (
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
                          highlightedId={highlightedId}
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
                                  highlightedId={highlightedId}
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

          {staleReportId === selectedId && (
            <div className="refresh-notice" role="status">
              <span>这篇报告已在磁盘上更新。</span>
              <button
                type="button"
                onClick={() => {
                  setStaleReportId("");
                  setReaderRevision((value) => value + 1);
                }}
              >
                刷新正文
              </button>
            </div>
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
