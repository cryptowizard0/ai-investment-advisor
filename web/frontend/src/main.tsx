import { StrictMode, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import Markdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";
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

type StreamState = "connecting" | "live" | "offline";

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
  try {
    return decodeURIComponent(window.location.hash.slice(1));
  } catch {
    return "";
  }
}

function reportPathFromId(id: string): string | null {
  try {
    const base64 = id.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    const bytes = Uint8Array.from(atob(padded), (character) =>
      character.charCodeAt(0),
    );
    return new TextDecoder().decode(bytes);
  } catch {
    return null;
  }
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

function StatePanel({
  symbol,
  title,
  detail,
  tone = "neutral",
  actionLabel,
  onAction,
}: {
  symbol: string;
  title: string;
  detail: string;
  tone?: "neutral" | "error";
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <section
      className={`state-panel ${tone}`}
      role={tone === "error" ? "alert" : "status"}
    >
      <span className="state-symbol" aria-hidden="true">
        {symbol}
      </span>
      <div>
        <h3>{title}</h3>
        <p>{detail}</p>
      </div>
      {actionLabel && onAction && (
        <button type="button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </section>
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
  const [catalogReports, setCatalogReports] = useState<Report[]>([]);
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
  const [loadingFacets, setLoadingFacets] = useState(true);
  const [loadingMarkdown, setLoadingMarkdown] = useState(false);
  const [eventRevision, setEventRevision] = useState(0);
  const [readerRevision, setReaderRevision] = useState(0);
  const [streamRevision, setStreamRevision] = useState(0);
  const [streamState, setStreamState] =
    useState<StreamState>("connecting");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [highlightedId, setHighlightedId] = useState("");
  const [staleReportId, setStaleReportId] = useState("");
  const selectedIdRef = useRef(selectedId);
  const listIsScopedRef = useRef(false);
  const connectionInterruptedRef = useRef(false);
  const highlightTimer = useRef<number | undefined>(undefined);
  const normalizedSearchQuery = searchQuery.trim();
  const selectedReportExists = [...catalogReports, ...reports].some(
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
    const loadCatalog = async () => {
      try {
        const response = await fetchNoStore(
          "/api/reports",
          controller.signal,
          "完整报告目录请求失败",
        );
        setCatalogReports(await response.json());
      } catch (error) {
        if (!isAbortError(error)) {
          setCatalogReports([]);
        }
      }
    };

    void loadCatalog();
    return () => controller.abort();
  }, [eventRevision]);

  useEffect(() => {
    const controller = new AbortController();
    const loadFacets = async () => {
      setLoadingFacets(true);
      setFacetError("");
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
      } finally {
        if (!controller.signal.aborted) {
          setLoadingFacets(false);
        }
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
    setStreamState("connecting");
    const source = new EventSource("/api/events");
    source.onopen = () => {
      if (connectionInterruptedRef.current && selectedIdRef.current) {
        setStaleReportId(selectedIdRef.current);
      }
      connectionInterruptedRef.current = false;
      setStreamState("live");
      setEventRevision((value) => value + 1);
    };
    source.onerror = () => {
      connectionInterruptedRef.current = true;
      setStreamState("offline");
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
  }, [streamRevision]);

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

  const reportIdByPath = useMemo(() => {
    const idsByPath = new Map<string, string>();
    for (const report of catalogReports.length ? catalogReports : reports) {
      const path = reportPathFromId(report.id);
      if (path) {
        idsByPath.set(path, report.id);
      }
    }
    return idsByPath;
  }, [catalogReports, reports]);

  const selectedReport =
    catalogReports.find((report) => report.id === selectedId) ??
    reports.find((report) => report.id === selectedId);
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

  const linkedReportId = (href: string | undefined): string | undefined => {
    if (!href || !selectedReport || href.startsWith("#")) {
      return undefined;
    }
    if (/^[a-z][a-z\d+.-]*:/i.test(href) || href.startsWith("//")) {
      return undefined;
    }

    const selectedPath = reportPathFromId(selectedReport.id);
    if (!selectedPath) {
      return undefined;
    }

    try {
      const target = new URL(href, `https://reader.local/${selectedPath}`);
      return reportIdByPath.get(decodeURIComponent(target.pathname.slice(1)));
    } catch {
      return undefined;
    }
  };

  const clearFilters = () => {
    setSelectedCategories([]);
    setSelectedSkills([]);
    setSelectedTickers([]);
    setSelectedThemes([]);
    setDateFrom("");
    setDateTo("");
  };

  const resetDiscovery = () => {
    setSearchQuery("");
    clearFilters();
  };

  const facetsAreEmpty =
    facets.skills.length === 0 &&
    facets.categories.length === 0 &&
    facets.tickers.length === 0 &&
    facets.themes.length === 0;
  const streamLabel = {
    connecting: "正在连接",
    live: "实时同步",
    offline: "同步已断开",
  }[streamState];

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
        <div className={`sync-status ${streamState}`} role="status">
          <span aria-hidden="true" />
          <span>{streamLabel}</span>
          {streamState === "offline" && (
            <button
              type="button"
              onClick={() => setStreamRevision((value) => value + 1)}
            >
              重连
            </button>
          )}
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
            <div className="sidebar-actions">
              <button
                className="filter-toggle"
                type="button"
                onClick={() => setFiltersOpen((value) => !value)}
                aria-expanded={filtersOpen}
                aria-controls="report-filters"
              >
                <span>
                  筛选{activeFilterCount > 0 ? ` ${activeFilterCount}` : ""}
                </span>
                <span
                  className={`filter-chevron${filtersOpen ? " open" : ""}`}
                  aria-hidden="true"
                />
              </button>
              <span>{reports.length}</span>
            </div>
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

          <section
            className={`facet-panel${filtersOpen ? " open" : ""}`}
            id="report-filters"
            aria-label="报告筛选"
          >
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

            {loadingFacets && facetsAreEmpty ? (
              <div className="facet-loading" role="status">
                <span />
                <span />
                <span />
              </div>
            ) : (
              <>
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
              </>
            )}

            {facetError && (
              <div className="inline-error" role="alert">
                <span>{facetError}</span>
                <button
                  type="button"
                  onClick={() => setEventRevision((value) => value + 1)}
                >
                  重试
                </button>
              </div>
            )}
          </section>

          {loadingReports && (
            <div className="list-loading" role="status">
              <p>{hasSearchQuery ? "正在搜索报告…" : "正在载入报告库…"}</p>
              {[0, 1, 2, 3].map((item) => (
                <div className="report-skeleton" key={item}>
                  <span />
                  <span />
                </div>
              ))}
            </div>
          )}
          {!loadingReports && listError && (
            <StatePanel
              symbol="!"
              title="报告列表暂时不可用"
              detail={listError}
              tone="error"
              actionLabel="重新加载"
              onAction={() => setEventRevision((value) => value + 1)}
            />
          )}
          {!loadingReports && !listError && reports.length === 0 && (
            <StatePanel
              symbol={hasSearchQuery ? "⌕" : "—"}
              title={
                hasSearchQuery
                  ? "没有搜索结果"
                  : hasActiveFilters
                    ? "没有符合筛选条件的报告"
                    : "报告库还是空的"
              }
              detail={
                hasSearchQuery
                  ? "试试更短的关键词、ticker，或清除筛选条件。"
                  : hasActiveFilters
                    ? "放宽日期或分面条件，查看其他报告。"
                    : "将 Markdown 报告写入 output/ 后会自动出现在这里。"
              }
              actionLabel={
                hasSearchQuery || hasActiveFilters ? "清除搜索与筛选" : undefined
              }
              onAction={
                hasSearchQuery || hasActiveFilters
                  ? resetDiscovery
                  : undefined
              }
            />
          )}

          <nav
            className="report-list"
            aria-busy={loadingReports}
            hidden={loadingReports || Boolean(listError)}
          >
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
              <div className="reader-context">
                <button
                  className="reader-back"
                  type="button"
                  onClick={() => window.history.back()}
                  aria-label="返回上一页"
                >
                  <span aria-hidden="true">←</span>
                  返回
                </button>
                <div className="document-path">
                  <span>{selectedReport.category}</span>
                  <span aria-hidden="true">/</span>
                  <span>{selectedReport.skill}</span>
                </div>
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
              <div className="document-loading" role="status">
                <span className="loading-kicker">正在打开报告</span>
                <span className="loading-title" />
                <span className="loading-title short" />
                {[0, 1, 2, 3, 4].map((item) => (
                  <span className="loading-line" key={item} />
                ))}
              </div>
            )}
            {!loadingMarkdown && readerError && (
              <StatePanel
                symbol="!"
                title="报告打开失败"
                detail={readerError}
                tone="error"
                actionLabel="重新读取"
                onAction={() => setReaderRevision((value) => value + 1)}
              />
            )}
            {!selectedReport && !loadingReports && (
              <StatePanel
                symbol="↗"
                title="选择一篇报告开始阅读"
                detail="报告正文会在这里以舒适的长文版式呈现。"
              />
            )}
            {!loadingMarkdown && !readerError && markdown && (
              <div className="markdown-body">
                <Markdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw, rehypeSanitize]}
                  components={{
                    a: ({ href, ...props }) => {
                      const reportId = linkedReportId(href);
                      return (
                        <a
                          {...props}
                          href={
                            reportId
                              ? `#${encodeURIComponent(reportId)}`
                              : href
                          }
                        />
                      );
                    },
                  }}
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
