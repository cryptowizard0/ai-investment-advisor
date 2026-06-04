---
name: output-report-index
description: "Use when the user explicitly asks to 生成索引, 更新索引, 生成 output 报告索引, 更新 output 报告索引, or create/update an index.md page for reports under output/."
---

# Output 报告索引

## Overview

为 `output/` 下已有 Markdown 报告生成或更新 `output/index.md`。索引按 `output/` 一级目录分类展示报告表格，分类内按时间升序排列，新的报告在后面。

## Trigger

只在用户明确要求时使用，例如：

- `生成索引`
- `更新索引`
- `生成 output 报告索引`
- `更新 output/index.md`

不要在生成其他报告后主动触发本 Skill，除非用户同时要求更新索引。

## Workflow

1. 运行脚本：

```bash
python plugins/invest-flow/skills/output-report-index/scripts/generate_index.py
```

2. 脚本递归扫描 `output/**/*.md`，排除 `output/index.md` 本身。
3. 如果 `output/index.md` 已存在，脚本会用最新扫描结果全量重写。
4. 生成后检查索引包含分类、标题和原文链接。

## Index Rules

- 分类使用报告所在的 `output/` 一级子目录名。
- 标题优先读取 Markdown 文件第一个 `# ` 一级标题；没有一级标题时使用文件名。
- 日期优先从文件名解析 `YYYY-MM-DD`，其次解析 `YYYYMMDD` 并格式化为 `YYYY-MM-DD`。
- 分类内按日期升序排列；同日按文件路径升序排列。
- 每个分类表格列为：`日期 | 标题 | 原文链接`。
- 原文链接相对 `output/index.md`，例如 `./fundamental-analysis/HPE-Hewlett-Packard-Enterprise-2026-06-03.md`。

## Resources

### scripts/

- `generate_index.py`: 生成或更新 `output/index.md`，不读取网络，不生成投资内容。
