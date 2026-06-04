#!/usr/bin/env python3
"""Generate an index page for Markdown reports under output/."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output"
INDEX_FILENAME = "index.md"
HTML_INDEX_FILENAME = "index.html"
ISO_DATE_RE = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")
COMPACT_DATE_RE = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")


class ReportEntry(NamedTuple):
    category: str
    date_text: str
    title: str
    relative_link: str
    relative_path: str


def parse_report_date(path: Path) -> str:
    stem = path.stem

    iso_matches = list(ISO_DATE_RE.finditer(stem))
    if iso_matches:
        return iso_matches[-1].group(1)

    compact_matches = list(COMPACT_DATE_RE.finditer(stem))
    if compact_matches:
        match = compact_matches[-1]
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    return ""


def extract_title(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if stripped.startswith("# ") and len(stripped) > 2:
                    return stripped[2:].strip()
    except UnicodeDecodeError:
        return path.stem

    return path.stem


def markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def markdown_link_path(path: Path) -> str:
    return "./" + path.as_posix().replace(" ", "%20")


def html_attr(value: str) -> str:
    return html.escape(value, quote=True)


def html_text(value: str) -> str:
    return html.escape(value, quote=False)


def collect_reports(output_dir: Path) -> list[ReportEntry]:
    reports: list[ReportEntry] = []
    index_path = (output_dir / INDEX_FILENAME).resolve()

    for path in sorted(output_dir.rglob("*.md")):
        if path.resolve() == index_path:
            continue
        if not path.is_file():
            continue

        relative_path = path.relative_to(output_dir)
        parts = relative_path.parts
        category = parts[0] if len(parts) > 1 else "root"
        reports.append(
            ReportEntry(
                category=category,
                date_text=parse_report_date(path),
                title=extract_title(path),
                relative_link=markdown_link_path(relative_path),
                relative_path=relative_path.as_posix(),
            )
        )

    return reports


def render_index(reports: list[ReportEntry]) -> str:
    lines = [
        "# Output 报告索引",
        "",
        "按 `output/` 一级目录分类，分类内按报告日期升序排列。",
        "",
    ]

    if not reports:
        lines.extend(["暂无 Markdown 报告。", ""])
        return "\n".join(lines)

    categories = sorted({report.category for report in reports})
    for category in categories:
        category_reports = sorted(
            (report for report in reports if report.category == category),
            key=lambda report: (report.date_text, report.relative_path),
        )
        lines.extend(
            [
                f"## {category}",
                "",
                "| 日期 | 标题 | 原文链接 |",
                "|---|---|---|",
            ]
        )
        for report in category_reports:
            lines.append(
                "| {date} | {title} | [原文]({link}) |".format(
                    date=markdown_table_cell(report.date_text),
                    title=markdown_table_cell(report.title),
                    link=report.relative_link,
                )
            )
        lines.append("")

    return "\n".join(lines)


def report_sort_key(report: ReportEntry) -> tuple[str, str]:
    return (report.date_text, report.relative_path)


def report_manifest(reports: list[ReportEntry]) -> list[dict[str, str]]:
    return [
        {
            "category": report.category,
            "date": report.date_text,
            "title": report.title,
            "path": report.relative_link.removeprefix("./"),
            "source": report.relative_link,
        }
        for report in reports
    ]


def latest_report(reports: list[ReportEntry]) -> ReportEntry | None:
    dated_reports = [report for report in reports if report.date_text]
    if dated_reports:
        return sorted(dated_reports, key=report_sort_key)[-1]
    if reports:
        return sorted(reports, key=lambda report: report.relative_path)[-1]
    return None


def render_report_nav(reports: list[ReportEntry]) -> str:
    if not reports:
        return '<p class="empty-state">暂无 Markdown 报告。</p>'

    sections: list[str] = []
    categories = sorted({report.category for report in reports})
    for category in categories:
        category_reports = sorted(
            (report for report in reports if report.category == category),
            key=report_sort_key,
        )
        items = []
        for report in category_reports:
            hash_path = report.relative_link.removeprefix("./")
            items.append(
                "\n".join(
                    [
                        '<article class="report-item" data-category="{category}" data-title="{title}" data-date="{date}" data-path="{path}">'.format(
                            category=html_attr(report.category),
                            title=html_attr(report.title),
                            date=html_attr(report.date_text),
                            path=html_attr(hash_path),
                        ),
                        '  <a class="report-title" href="#{path}">{title}</a>'.format(
                            path=html_attr(hash_path),
                            title=html_text(report.title),
                        ),
                        '  <div class="report-meta">',
                        '    <span>{date}</span>'.format(
                            date=html_text(report.date_text or "无日期")
                        ),
                        '    <a class="source-link" href="{source}">原文</a>'.format(
                            source=html_attr(report.relative_link)
                        ),
                        "  </div>",
                        "</article>",
                    ]
                )
            )
        sections.append(
            "\n".join(
                [
                    '<section class="category-section" data-category="{category}">'.format(
                        category=html_attr(category)
                    ),
                    '  <button class="category-heading" type="button" data-category-toggle="{category}" aria-expanded="true">'.format(
                        category=html_attr(category)
                    ),
                    "    <span>{category}</span>".format(category=html_text(category)),
                    "    <span>",
                    '      <span class="category-count">{count}</span>'.format(
                        count=len(category_reports)
                    ),
                    '      <span class="category-caret" aria-hidden="true">▾</span>',
                    "    </span>",
                    "  </button>",
                    '  <div class="category-items">',
                    "\n".join(items),
                    "  </div>",
                    "</section>",
                ]
            )
        )
    return "\n".join(sections)


def render_html_index(reports: list[ReportEntry]) -> str:
    categories = sorted({report.category for report in reports})
    newest = latest_report(reports)
    latest_date = newest.date_text if newest and newest.date_text else "暂无"
    latest_title = newest.title if newest else "暂无报告"
    latest_category = newest.category if newest else "暂无"
    latest_hash = newest.relative_link.removeprefix("./") if newest else ""
    latest_report_metric = (
        '<a class="metric-value metric-link" href="#{path}">{title}</a>'.format(
            path=html_attr(latest_hash),
            title=html_text(latest_title),
        )
        if newest
        else '<span class="metric-value">暂无报告</span>'
    )
    reports_json = json.dumps(report_manifest(reports), ensure_ascii=False, indent=2)
    nav_html = render_report_nav(reports)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reports by AI Investment Advisor</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --panel-subtle: #f1f4f8;
      --text: #172033;
      --muted: #657084;
      --border: #dbe1ea;
      --accent: #2563eb;
      --accent-strong: #1d4ed8;
      --accent-soft: #e8f0ff;
      --green: #0f766e;
      --shadow: 0 10px 30px rgba(22, 32, 51, 0.08);
      --radius: 8px;
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      --sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      line-height: 1.55;
      overflow: hidden;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ color: var(--accent-strong); text-decoration: underline; }}
    .app-shell {{
      height: 100vh;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      overflow: hidden;
    }}
    .topbar {{
      padding: 22px 28px 18px;
      border-bottom: 1px solid var(--border);
      background: var(--panel);
      z-index: 10;
    }}
    .title-row {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin: 0;
      font-size: 24px;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .open-source {{
      flex: 0 0 auto;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 8px 10px;
      background: var(--panel-subtle);
      font-size: 13px;
    }}
    .sidebar-toggle {{
      width: 38px;
      height: 38px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--panel-subtle);
      color: var(--text);
      cursor: pointer;
      font-size: 18px;
      line-height: 1;
    }}
    .sidebar-toggle:hover {{
      border-color: var(--accent);
      background: var(--accent-soft);
      color: var(--accent-strong);
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .metric-card {{
      min-width: 0;
      padding: 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--panel-subtle);
    }}
    .metric-label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .metric-value {{
      display: block;
      color: var(--text);
      font-size: 19px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }}
    .metric-link {{
      color: var(--text);
      text-decoration: none;
    }}
    .metric-link:hover {{
      color: var(--accent-strong);
      text-decoration: underline;
    }}
    .workspace {{
      display: grid;
      grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
      min-height: 0;
      overflow: hidden;
      transition: grid-template-columns 160ms ease;
    }}
    .app-shell.sidebar-collapsed .workspace {{
      grid-template-columns: 52px minmax(0, 1fr);
    }}
    .sidebar {{
      min-height: 0;
      overflow: auto;
      border-right: 1px solid var(--border);
      background: var(--panel);
      padding: 18px;
      transition: padding 160ms ease, border-color 160ms ease;
    }}
    .app-shell.sidebar-collapsed .sidebar {{
      overflow: hidden;
      padding: 14px 7px;
    }}
    .sidebar-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 14px;
    }}
    .sidebar-title {{
      font-weight: 700;
      color: var(--text);
      font-size: 14px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .app-shell.sidebar-collapsed .sidebar-header {{
      justify-content: center;
      margin-bottom: 0;
    }}
    .app-shell.sidebar-collapsed .sidebar-title,
    .app-shell.sidebar-collapsed .sidebar-content {{
      display: none;
    }}
    .app-shell.sidebar-collapsed .reader {{
      min-width: 0;
    }}
    .search {{
      width: 100%;
      height: 38px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 0 11px;
      font-size: 14px;
      outline: none;
      background: #ffffff;
    }}
    .search:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }}
    .filter-row {{
      display: flex;
      gap: 8px;
      margin: 12px 0 16px;
      flex-wrap: wrap;
    }}
    .filter-chip {{
      border: 1px solid var(--border);
      border-radius: 999px;
      background: #ffffff;
      color: var(--muted);
      padding: 6px 10px;
      cursor: pointer;
      font-size: 12px;
    }}
    .filter-chip.active {{
      border-color: var(--accent);
      background: var(--accent-soft);
      color: var(--accent-strong);
    }}
    .category-section {{ margin-bottom: 18px; }}
    .category-items {{
      display: block;
    }}
    .category-section.collapsed .category-items {{
      display: none;
    }}
    .category-caret {{
      display: inline-block;
      color: var(--muted);
      font-size: 12px;
      margin-left: 6px;
      transition: transform 120ms ease;
    }}
    .category-section.collapsed .category-caret {{
      transform: rotate(-90deg);
    }}
    .category-heading {{
      width: 100%;
      border: 0;
      padding: 0 0 8px;
      background: transparent;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--text);
      font-weight: 700;
      cursor: pointer;
      letter-spacing: 0;
    }}
    .category-count {{
      min-width: 26px;
      border-radius: 999px;
      padding: 2px 8px;
      background: var(--panel-subtle);
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }}
    .report-item {{
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 11px;
      margin-bottom: 8px;
      background: #ffffff;
    }}
    .report-item.active {{
      border-color: var(--accent);
      background: var(--accent-soft);
    }}
    .report-title {{
      display: block;
      font-weight: 650;
      color: var(--text);
      overflow-wrap: anywhere;
      font-size: 14px;
      line-height: 1.35;
    }}
    .report-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
    }}
    .source-link {{ font-size: 12px; flex: 0 0 auto; }}
    .reader {{
      min-width: 0;
      padding: 26px;
      overflow: auto;
    }}
    .reader-card {{
      max-width: 1040px;
      min-height: calc(100vh - 196px);
      margin: 0 auto;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 30px;
    }}
    .reader-header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      padding-bottom: 18px;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
    }}
    .reader-title {{
      margin: 0;
      font-size: 22px;
      letter-spacing: 0;
    }}
    .reader-meta {{
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .status {{
      color: var(--muted);
      background: var(--panel-subtle);
      border-radius: var(--radius);
      padding: 16px;
    }}
    .markdown-body {{
      font-size: 15px;
    }}
    .markdown-body h1, .markdown-body h2, .markdown-body h3 {{
      line-height: 1.28;
      letter-spacing: 0;
      margin: 1.4em 0 0.65em;
    }}
    .markdown-body h1 {{ font-size: 26px; }}
    .markdown-body h2 {{ font-size: 21px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
    .markdown-body h3 {{ font-size: 17px; }}
    .markdown-body p {{ margin: 0 0 13px; }}
    .markdown-body table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      display: block;
      overflow-x: auto;
    }}
    .markdown-body th, .markdown-body td {{
      border: 1px solid var(--border);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }}
    .markdown-body th {{ background: var(--panel-subtle); }}
    .markdown-body blockquote {{
      margin: 14px 0;
      padding: 10px 14px;
      border-left: 4px solid var(--accent);
      background: var(--panel-subtle);
      color: var(--muted);
    }}
    .markdown-body pre {{
      overflow-x: auto;
      padding: 14px;
      background: #101827;
      color: #e5edf7;
      border-radius: var(--radius);
    }}
    .markdown-body code {{
      font-family: var(--mono);
      font-size: 0.92em;
    }}
    .markdown-body :not(pre) > code {{
      background: var(--panel-subtle);
      border: 1px solid var(--border);
      border-radius: 5px;
      padding: 1px 5px;
    }}
    .empty-state {{ color: var(--muted); font-size: 14px; }}
    @media (max-width: 920px) {{
      .topbar {{ position: static; padding: 18px; }}
      .title-row {{ align-items: flex-start; flex-direction: column; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .workspace {{ grid-template-columns: 1fr; }}
      .app-shell.sidebar-collapsed .workspace {{ grid-template-columns: 52px minmax(0, 1fr); }}
      .sidebar {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .app-shell.sidebar-collapsed .sidebar {{ border-bottom: 0; }}
      .reader {{ padding: 16px; }}
      .reader-card {{ padding: 20px; }}
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <header class="topbar">
      <div class="title-row">
        <div>
          <h1>Reports by AI Investment Advisor</h1>
          <p class="subtitle">点击报告后按需加载 Markdown 并在本页渲染。建议通过本地 HTTP 服务访问。</p>
        </div>
        <a class="open-source" href="./index.md">打开 Markdown 索引</a>
      </div>
      <section class="metrics" aria-label="报告指标">
        <div class="metric-card">
          <span class="metric-label">报告总数</span>
          <span class="metric-value">{len(reports)}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">分类总数</span>
          <span class="metric-value">{len(categories)}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">最新日期</span>
          <span class="metric-value">{html_text(latest_date)}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">最新报告</span>
          {latest_report_metric}
        </div>
      </section>
    </header>
    <main class="workspace">
      <aside class="sidebar" aria-label="报告列表">
        <div class="sidebar-header">
          <span class="sidebar-title">报告导航</span>
          <button class="sidebar-toggle" id="sidebarToggle" type="button" aria-label="收起侧边栏" title="收起侧边栏">‹</button>
        </div>
        <div class="sidebar-content">
          <input class="search" id="searchInput" type="search" placeholder="搜索标题、分类或日期" autocomplete="off">
          <div class="filter-row" id="filterRow">
            <button class="filter-chip active" type="button" data-category="all">全部</button>
          </div>
          <div id="reportList">
{nav_html}
          </div>
        </div>
      </aside>
      <section class="reader" aria-label="Markdown 阅读器">
        <article class="reader-card">
          <div class="reader-header">
            <div>
              <h2 class="reader-title" id="readerTitle">选择一篇报告</h2>
              <p class="reader-meta" id="readerMeta">共 {len(reports)} 篇报告，最新分类：{html_text(latest_category)}</p>
            </div>
            <a class="open-source" id="readerSource" href="#" hidden>原文</a>
          </div>
          <div class="status" id="readerStatus">从左侧选择报告，正文会在这里渲染。</div>
          <div class="markdown-body" id="markdownBody"></div>
        </article>
      </section>
    </main>
  </div>
  <script>
    const REPORTS = {reports_json};

    const searchInput = document.getElementById('searchInput');
    const filterRow = document.getElementById('filterRow');
    const reportList = document.getElementById('reportList');
    const appShell = document.querySelector('.app-shell');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const readerTitle = document.getElementById('readerTitle');
    const readerMeta = document.getElementById('readerMeta');
    const readerSource = document.getElementById('readerSource');
    const readerStatus = document.getElementById('readerStatus');
    const markdownBody = document.getElementById('markdownBody');
    let activeCategory = 'all';

    function toggleSidebar() {{
      const isCollapsed = appShell.classList.toggle('sidebar-collapsed');
      sidebarToggle.setAttribute('aria-label', isCollapsed ? '打开侧边栏' : '收起侧边栏');
      sidebarToggle.setAttribute('title', isCollapsed ? '打开侧边栏' : '收起侧边栏');
      sidebarToggle.textContent = isCollapsed ? '›' : '‹';
    }}

    function escapeHtml(value) {{
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }}

    function applyInlineMarkdown(value) {{
      return escapeHtml(value)
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\*([^*]+)\\*/g, '<em>$1</em>')
        .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, function(_, text, url) {{
          const safeUrl = escapeHtml(url);
          return '<a href="' + safeUrl + '" target="_blank" rel="noopener noreferrer">' + text + '</a>';
        }});
    }}

    function isTableDivider(line) {{
      return /^\\s*\\|?\\s*:?-{{3,}}:?\\s*(\\|\\s*:?-{{3,}}:?\\s*)+\\|?\\s*$/.test(line);
    }}

    function splitTableRow(line) {{
      let trimmed = line.trim();
      if (trimmed.startsWith('|')) trimmed = trimmed.slice(1);
      if (trimmed.endsWith('|')) trimmed = trimmed.slice(0, -1);
      return trimmed.split('|').map(cell => cell.trim());
    }}

    function renderTable(lines, startIndex) {{
      const header = splitTableRow(lines[startIndex]);
      let index = startIndex + 2;
      const rows = [];
      while (index < lines.length && lines[index].includes('|') && lines[index].trim() !== '') {{
        rows.push(splitTableRow(lines[index]));
        index += 1;
      }}
      const headHtml = '<thead><tr>' + header.map(cell => '<th>' + applyInlineMarkdown(cell) + '</th>').join('') + '</tr></thead>';
      const bodyHtml = '<tbody>' + rows.map(row => '<tr>' + row.map(cell => '<td>' + applyInlineMarkdown(cell) + '</td>').join('') + '</tr>').join('') + '</tbody>';
      return {{ html: '<table>' + headHtml + bodyHtml + '</table>', nextIndex: index }};
    }}

    function flushParagraph(blocks, paragraph) {{
      if (paragraph.length) {{
        blocks.push('<p>' + applyInlineMarkdown(paragraph.join(' ')) + '</p>');
        paragraph.length = 0;
      }}
    }}

    function renderMarkdown(markdown) {{
      const lines = markdown.replace(/\\r\\n/g, '\\n').split('\\n');
      const blocks = [];
      const paragraph = [];
      let inCode = false;
      let codeLines = [];

      for (let i = 0; i < lines.length; i += 1) {{
        const line = lines[i];
        const trimmed = line.trim();

        if (trimmed.startsWith('```')) {{
          if (inCode) {{
            blocks.push('<pre><code>' + escapeHtml(codeLines.join('\\n')) + '</code></pre>');
            codeLines = [];
            inCode = false;
          }} else {{
            flushParagraph(blocks, paragraph);
            inCode = true;
          }}
          continue;
        }}

        if (inCode) {{
          codeLines.push(line);
          continue;
        }}

        if (trimmed === '') {{
          flushParagraph(blocks, paragraph);
          continue;
        }}

        if (i + 1 < lines.length && line.includes('|') && isTableDivider(lines[i + 1])) {{
          flushParagraph(blocks, paragraph);
          const table = renderTable(lines, i);
          blocks.push(table.html);
          i = table.nextIndex - 1;
          continue;
        }}

        const heading = /^(#{{1,6}})\\s+(.+)$/.exec(trimmed);
        if (heading) {{
          flushParagraph(blocks, paragraph);
          const level = Math.min(heading[1].length, 3);
          blocks.push('<h' + level + '>' + applyInlineMarkdown(heading[2]) + '</h' + level + '>');
          continue;
        }}

        if (/^---+$/.test(trimmed)) {{
          flushParagraph(blocks, paragraph);
          blocks.push('<hr>');
          continue;
        }}

        if (trimmed.startsWith('>')) {{
          flushParagraph(blocks, paragraph);
          blocks.push('<blockquote>' + applyInlineMarkdown(trimmed.replace(/^>\\s?/, '')) + '</blockquote>');
          continue;
        }}

        const unordered = /^[-*]\\s+(.+)$/.exec(trimmed);
        if (unordered) {{
          flushParagraph(blocks, paragraph);
          const items = [];
          while (i < lines.length) {{
            const item = /^[-*]\\s+(.+)$/.exec(lines[i].trim());
            if (!item) break;
            items.push('<li>' + applyInlineMarkdown(item[1]) + '</li>');
            i += 1;
          }}
          i -= 1;
          blocks.push('<ul>' + items.join('') + '</ul>');
          continue;
        }}

        const ordered = /^\\d+\\.\\s+(.+)$/.exec(trimmed);
        if (ordered) {{
          flushParagraph(blocks, paragraph);
          const items = [];
          while (i < lines.length) {{
            const item = /^\\d+\\.\\s+(.+)$/.exec(lines[i].trim());
            if (!item) break;
            items.push('<li>' + applyInlineMarkdown(item[1]) + '</li>');
            i += 1;
          }}
          i -= 1;
          blocks.push('<ol>' + items.join('') + '</ol>');
          continue;
        }}

        paragraph.push(trimmed);
      }}

      flushParagraph(blocks, paragraph);
      if (inCode) {{
        blocks.push('<pre><code>' + escapeHtml(codeLines.join('\\n')) + '</code></pre>');
      }}
      return blocks.join('\\n');
    }}

    function setStatus(message) {{
      readerStatus.hidden = false;
      readerStatus.textContent = message;
      markdownBody.innerHTML = '';
    }}

    function findReportFromHash() {{
      const rawHash = location.hash.replace(/^#/, '');
      if (!rawHash) return null;
      const decodedHash = decodeURIComponent(rawHash);
      return REPORTS.find(report => report.path === rawHash || decodeURIComponent(report.path) === decodedHash) || null;
    }}

    async function loadReportFromHash() {{
      const report = findReportFromHash();
      document.querySelectorAll('.report-item').forEach(item => {{
        const isActive = report && item.dataset.path === report.path;
        item.classList.toggle('active', Boolean(isActive));
      }});

      if (!report) {{
        setStatus(REPORTS.length ? '从左侧选择报告，正文会在这里渲染。' : '暂无 Markdown 报告。');
        readerTitle.textContent = REPORTS.length ? '选择一篇报告' : '暂无报告';
        readerMeta.textContent = '通过本地 HTTP 服务打开本页后，可按需加载 Markdown。';
        readerSource.hidden = true;
        return;
      }}

      readerTitle.textContent = report.title;
      readerMeta.textContent = [report.category, report.date || '无日期'].join(' / ');
      readerSource.href = report.source;
      readerSource.hidden = false;
      setStatus('正在加载 Markdown...');

      try {{
        const response = await fetch(report.path);
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const markdown = await response.text();
        readerStatus.hidden = true;
        markdownBody.innerHTML = renderMarkdown(markdown);
      }} catch (error) {{
        setStatus('无法加载 Markdown。请通过本地 HTTP 服务访问本页，例如在仓库根目录运行 python -m http.server 后打开 /output/index.html。错误：' + error.message);
      }}
    }}

    function applyFilters() {{
      const query = searchInput.value.trim().toLowerCase();
      document.querySelectorAll('.category-section').forEach(section => {{
        let visibleCount = 0;
        section.querySelectorAll('.report-item').forEach(item => {{
          const matchesCategory = activeCategory === 'all' || item.dataset.category === activeCategory;
          const haystack = [item.dataset.title, item.dataset.category, item.dataset.date].join(' ').toLowerCase();
          const matchesQuery = !query || haystack.includes(query);
          const visible = matchesCategory && matchesQuery;
          item.hidden = !visible;
          if (visible) visibleCount += 1;
        }});
        section.hidden = visibleCount === 0;
      }});
    }}

    function setupCategoryFilters() {{
      const categories = Array.from(new Set(REPORTS.map(report => report.category))).sort();
      for (const category of categories) {{
        const button = document.createElement('button');
        button.className = 'filter-chip';
        button.type = 'button';
        button.dataset.category = category;
        button.textContent = category;
        filterRow.appendChild(button);
      }}
      filterRow.addEventListener('click', event => {{
        const button = event.target.closest('button[data-category]');
        if (!button) return;
        activeCategory = button.dataset.category;
        filterRow.querySelectorAll('.filter-chip').forEach(chip => chip.classList.toggle('active', chip === button));
        applyFilters();
      }});
      reportList.addEventListener('click', event => {{
        const button = event.target.closest('button[data-category-toggle]');
        if (!button) return;
        toggleCategorySection(button);
      }});
    }}

    function toggleCategorySection(button) {{
      const section = button.closest('.category-section');
      if (!section) return;
      const isCollapsed = section.classList.toggle('collapsed');
      button.setAttribute('aria-expanded', String(!isCollapsed));
    }}

    sidebarToggle.addEventListener('click', toggleSidebar);
    searchInput.addEventListener('input', applyFilters);
    window.addEventListener('hashchange', loadReportFromHash);
    setupCategoryFilters();
    applyFilters();
    loadReportFromHash();
  </script>
</body>
</html>
"""


def generate_index(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir = Path(output_dir)
    if not output_dir.exists():
        raise SystemExit(f"Output directory not found: {output_dir}")
    if not output_dir.is_dir():
        raise SystemExit(f"Output path is not a directory: {output_dir}")

    reports = collect_reports(output_dir)
    index_path = output_dir / INDEX_FILENAME
    html_index_path = output_dir / HTML_INDEX_FILENAME
    index_path.write_text(render_index(reports), encoding="utf-8-sig")
    html_index_path.write_text(render_html_index(reports), encoding="utf-8")
    return index_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or update output/index.md and output/index.html from Markdown reports."
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory to scan for Markdown reports.",
    )
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Print only the generated index path after writing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index_path = generate_index(output_dir=Path(args.output_dir))
    if args.print_path:
        print(index_path)
    else:
        print(f"Updated report index: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
