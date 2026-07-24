---
name: output-report-index
description: "Use when the user explicitly asks to 生成索引, 更新索引, 生成 output 报告索引, 更新 output 报告索引, or create/update index pages for reports under output/."
---

# Output 报告索引

## Overview

为 `output/` 下已有 Markdown 报告生成或更新 `output/index.md` 和 `output/index.html`。Markdown 索引按主题类和 skill 两级展示报告表格；HTML 索引是一个单页 Markdown 阅读器，点击报告后按需加载原始 `.md` 并渲染。

## Trigger

只在用户明确要求时使用，例如：

- `生成索引`
- `更新索引`
- `生成 output 报告索引`
- `更新 output/index.md`
- `更新 output/index.html`

不要在生成其他报告后主动触发本 Skill，除非用户同时要求更新索引。

## Workflow

1. 运行脚本：

```bash
python plugins/invest-flow/skills/output-report-index/scripts/generate_index.py
```

2. 脚本递归扫描 `output/**/*.md`，排除 `output/index.md` 本身。
3. 脚本会全量重写 `output/index.md` 和 `output/index.html`。
4. 生成后检查 Markdown 索引包含分类、标题和原文链接；HTML 索引包含顶部指标、搜索、分类列表和阅读器。
5. 测试 HTML 阅读器和原文 Markdown 链接时，运行：

```bash
python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000
```

然后访问 `http://127.0.0.1:8000/output/index.html`。不要用裸 `python -m http.server`，它对 `.md` 不声明 `charset=utf-8`，浏览器直开中文 Markdown 时可能乱码。

## Index Rules

- 一级分类使用 `chain-alpha`、`monitor`、`research` 主题类。
- 二级分类使用当前 skill 名。旧目录名和旧文件名前缀映射到语义对应的当前 skill；无法识别的报告归入“历史/其他”。
- 迁移期间同时支持旧 skill 级目录和新的扁平主题目录。
- 标题优先读取 Markdown 文件第一个 `# ` 一级标题；没有一级标题时使用文件名。
- 日期优先从文件名解析 `YYYY-MM-DD`，其次解析 `YYYYMMDD` 并格式化为 `YYYY-MM-DD`。
- 每个 skill 分组内按日期升序排列；同日按文件路径升序排列。
- 每个 skill 分组表格列为：`日期 | 标题 | 原文链接`。
- 原文链接相对 `output/index.md`，例如 `./research-fundamentals/HPE-Hewlett-Packard-Enterprise-2026-06-03.md`。
- HTML 页面顶部显示报告总数、分类总数、最新日期和最新报告。
- HTML 页面不把每个报告转换为 HTML 文件，只通过 `fetch()` 按需读取原始 Markdown。
- `serve_reports.py` 会为 `.md` 和 `.html` 显式返回 UTF-8 Content-Type，解决浏览器直开中文 Markdown 乱码。

## Resources

### scripts/

- `generate_index.py`: 生成或更新 `output/index.md` 和 `output/index.html`，不读取网络，不生成投资内容。
- `serve_reports.py`: 本地静态服务，默认从 repo root 提供 `output/`，并为 Markdown/HTML 响应添加 UTF-8 charset。
