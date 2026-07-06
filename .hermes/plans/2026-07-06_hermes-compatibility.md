# Hermes Agent 兼容性 Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 让 ai-investment-advisor 项目在现有 Codex / Claude Code 兼容之外，也支持 Hermes Agent 作为一等运行时。

**Architecture:** 不改变现有 Codex/Claude Code 插件结构。新增一套 Hermes 风格的 skill frontmatter + plugin manifest + marketplace entry，确保同一套 skills 目录下的 SKILL.md 能被三个 agent 运行时正确加载。同时修正 4 个技能文件中的平台特定措辞，改为平台中立语言。

**Tech Stack:** YAML frontmatter, JSON manifest, Markdown

---

## 背景

- 现有 24 个 SKILL.md 文件已有 `name` + `description` YAML frontmatter，满足 Hermes 最低要求
- Hermes 要求更丰富的 frontmatter：`version`, `author`, `license`, `metadata.hermes.tags`, `metadata.hermes.related_skills`
- 4 个 SKILL.md 中写了 "Claude" 或 "Codex" 特定措辞，需改为平台中立
- Hermes plugin 通过 `.hermes-plugin/plugin.json` + marketplace.json 发现
- Hermes skills 可通过 `hermes skills tap add <repo-url>` 或本地路径安装

---

### Task 1: 调查 Hermes plugin 格式规范

**Objective:** 确认 Hermes plugin manifest 的准确格式

**Files:**
- Check: Hermes 官方文档 https://hermes-agent.nousresearch.com/docs/ 中 plugin 章节
- Check: `hermes plugins --help` 本地 CLI 输出

**Step 1: 浏览器打开文档**

```text
打开 https://hermes-agent.nousresearch.com/docs/ 查找 plugin manifest 格式
或在本地运行 hermes plugins --help 查看 plugin 子命令
```

**Step 2: 确认格式后继续 Task 2**

---

### Task 2: 创建 Hermes Plugin Manifest

**Objective:** 在 `plugins/invest-flow/.hermes-plugin/plugin.json` 创建 Hermes 风格的 plugin 描述文件

**Files:**
- Create: `plugins/invest-flow/.hermes-plugin/plugin.json`

**Step 1: 创建 manifest 文件**

参照 Codex 版本的 plugin.json 结构，创建 Hermes 版本：

```json
{
  "name": "invest-flow",
  "version": "0.3.5",
  "description": "Investment research skills bundle: multi-agent stock analysis, chain-alpha industry-chain stock selection, buyability scoring, earnings review, daily US market scans, non-consensus discovery, reflexivity workflows, report generation, and market data routing.",
  "author": {
    "name": "Potter",
    "email": "45678072+cryptowizard0@users.noreply.github.com",
    "url": "https://github.com/cryptowizard0/ai-investment-advisor"
  },
  "homepage": "https://github.com/cryptowizard0/ai-investment-advisor",
  "repository": "https://github.com/cryptowizard0/ai-investment-advisor",
  "keywords": ["investment", "finance", "stocks", "analysis", "chain-alpha", "research"],
  "skills": "./skills/",
  "hermes": {
    "min_version": "2.0.0",
    "skill_prefix": "invest-flow"
  }
}
```

**Step 2: 验证 JSON 格式**

```bash
python -c "import json; json.load(open('plugins/invest-flow/.hermes-plugin/plugin.json')); print('OK')"
```

---

### Task 3: 创建 Hermes Marketplace Entry

**Objective:** 在 repo 根目录创建 `.hermes-plugin/marketplace.json` 用于 Hermes 本地 plugin 发现

**Files:**
- Create: `.hermes-plugin/marketplace.json`

**Step 1: 创建 marketplace 文件**

```json
{
  "name": "investflow-local",
  "metadata": {
    "description": "Repo-local marketplace for the InvestFlow investment research plugin."
  },
  "owner": {
    "name": "Potter",
    "email": "45678072+cryptowizard0@users.noreply.github.com",
    "url": "https://github.com/cryptowizard0/ai-investment-advisor"
  },
  "plugins": [
    {
      "name": "invest-flow",
      "source": "./plugins/invest-flow",
      "description": "Investment research, reflexivity analysis, and market data workflows: multi-agent stock analysis, chain-alpha industry-chain stock selection, buyability scoring, earnings review, daily US market scans, non-consensus discovery, and report indexing.",
      "category": "productivity"
    }
  ]
}
```

**Step 2: 验证 JSON 格式**

```bash
python -c "import json; json.load(open('.hermes-plugin/marketplace.json')); print('OK')"
```

---

### Task 4: 修正平台特定措辞（4 个文件）

**Objective:** 将 SKILL.md 中的 "Claude" 和 "Codex" 措辞改为平台中立语言

**Files:**
- Modify: `plugins/invest-flow/skills/fundamental-analysis/SKILL.md:10` — "This skill enables Claude" → "This skill enables the agent"
- Modify: `plugins/invest-flow/skills/institutional-accumulation-analysis/SKILL.md` — 检查并修正 Claude/Codex 引用
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md` — 检查并修正 Claude/Codex 引用
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md` — 检查并修正 Claude/Codex 引用（如 "(Claude Code 原生支持；Codex 在 subagent 派发工具可用时默认启用)"）

**Step 1: 读取需要修改的每个文件的精确内容**

对每个文件执行 `read_file` 获取当前精确内容

**Step 2: 逐文件 patch**

- `fundamental-analysis/SKILL.md` line 10:
  - old: `This skill enables Claude to act as`
  - new: `This skill enables the agent to act as`

- `chain-alpha-pipeline/SKILL.md` description line 3:
  - old: `（Claude Code 原生支持；Codex 在 subagent 派发工具可用时默认启用）`
  - new: `（Claude Code 原生支持；Codex 在 subagent 派发工具可用时默认启用；Hermes 通过 delegate_task 支持并行）`

- 其余两个文件需先读取确认具体位置

**Step 3: 验证修改**

```bash
# 确认没有残留的 Claude/Codex 硬编码引用（排除 Hermes 兼容性说明自身）
grep -rn "Claude\|Codex" plugins/invest-flow/skills/*/SKILL.md | grep -v "hermes\|Hermes\|Claude Code\|Codex\|agent 会话\|平台中立"
```

---

### Task 5: 更新所有 24 个 SKILL.md 的 frontmatter 为 Hermes 完整格式

**Objective:** 在现有 `name` + `description` frontmatter 基础上，添加 `version`, `author`, `license`, `platforms`, `metadata.hermes` 字段

**Files:**
- Modify: `plugins/invest-flow/skills/*/SKILL.md` (24 files)

**Step 1: 准备统一的前端模板片段**

现有 frontmatter 格式（以 fundamental-analysis 为例）：
```yaml
---
name: fundamental-analysis
description: "基础分析 ..."
---
```

目标 Hermes 格式：
```yaml
---
name: fundamental-analysis
description: "基础分析 (Fundamental Analysis) ..."
version: 1.0.0
author: Potter
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [investment, fundamental-analysis, stock-research]
    related_skills: [company-profile, reportify-stock-analysis, professional-investment-analyst]
---
```

**Step 2: 逐文件 patch frontmatter**

对每个 SKILL.md，用 `patch` 工具替换 frontmatter 区块。需要根据每个 skill 的功能设定合适的 `tags` 和 `related_skills`。

核心 skills 分组及 related_skills 建议：

| Skill | Tags | Related Skills |
|---|---|---|
| chain-alpha-pipeline | investment, chain-alpha, orchestration, stock-selection | chain-alpha-mismatch-discovery, chain-alpha-monopoly-screen, chain-alpha-verification, chain-alpha-delivery-tracking |
| chain-alpha-mismatch-discovery | investment, chain-alpha, industry-analysis, supply-demand | chain-alpha-monopoly-screen, chain-alpha-pipeline, industry-chain-analysis |
| chain-alpha-monopoly-screen | investment, chain-alpha, monopoly, screening | chain-alpha-mismatch-discovery, chain-alpha-verification, chain-alpha-pipeline |
| chain-alpha-verification | investment, chain-alpha, verification, position-sizing | chain-alpha-monopoly-screen, chain-alpha-pipeline, chain-alpha-delivery-tracking |
| chain-alpha-delivery-tracking | investment, chain-alpha, delivery-tracking, revenue | chain-alpha-verification, chain-alpha-pipeline |
| multi-agent-stock-analysis | investment, multi-agent, stock-analysis, orchestration | company-profile, fundamental-analysis, institutional-accumulation-analysis, gie-investment-framework, reflexivity-deep-analysis, reportify-stock-analysis, non-consensus-company-discovery |
| company-profile | investment, company-profile, research | fundamental-analysis, industry-chain-analysis, multi-agent-stock-analysis |
| company-buyability-score | investment, scoring, valuation, buyability | fundamental-analysis, company-profile, reportify-stock-analysis |
| fundamental-analysis | investment, fundamental-analysis, technical-analysis, stock-research | company-profile, company-buyability-score, multi-agent-stock-analysis |
| earnings-report-analysis | investment, earnings, financial-results | fundamental-analysis, company-profile, professional-investment-analyst |
| institutional-accumulation-analysis | investment, institutional, capital-flow | fundamental-analysis, multi-agent-stock-analysis |
| gie-investment-framework | investment, framework, golden-shovel, infrastructure | industry-chain-analysis, reflexivity-deep-analysis, ai-infrastructure-sector-discovery |
| industry-chain-analysis | investment, industry-chain, supply-chain, bottleneck | chain-alpha-mismatch-discovery, non-consensus-company-discovery |
| non-consensus-company-discovery | investment, non-consensus, discovery, theme | industry-chain-analysis, chain-alpha-mismatch-discovery, company-profile |
| gold-trend-analysis | investment, gold, macro, bubble-risk | reflexivity-quick-scan |
| reflexivity-quick-scan | investment, reflexivity, narrative, quick-scan | reflexivity-deep-analysis, gie-investment-framework |
| reflexivity-deep-analysis | investment, reflexivity, narrative, deep-analysis | reflexivity-quick-scan, gie-investment-framework |
| professional-investment-analyst | investment, professional, research-report, buy-side | fundamental-analysis, company-profile, earnings-report-analysis, reportify-stock-analysis |
| reportify-stock-analysis | investment, report, structured, standardized | fundamental-analysis, company-profile, professional-investment-analyst |
| daily-us-market-scan | investment, market-scan, daily, us-market | fundamental-analysis, reflexivity-quick-scan |
| ai-infrastructure-sector-discovery | investment, ai-infrastructure, sector, discovery | ai-infrastructure-scarcity-radar, industry-chain-analysis, gie-investment-framework |
| ai-infrastructure-scarcity-radar | investment, ai-infrastructure, scarcity, bottleneck | ai-infrastructure-sector-discovery, industry-chain-analysis, gie-investment-framework |
| output-report-index | reporting, index, html, markdown | — |
| market-data-router | data, market-data, routing, cache | — |

**Step 3: 使用 execute_code 批量处理**

编写 Python 脚本遍历所有 SKILL.md，对每个文件读取 frontmatter，追加 Hermes 必需字段，写回。因为 24 个文件手工 patch 太繁琐，用脚本处理效率更高。

```python
# 伪代码
for skill_dir in skills_dirs:
    path = skill_dir / "SKILL.md"
    content = path.read_text()
    # Parse existing frontmatter
    # Append version, author, license, platforms, metadata
    # Write back
```

**Step 4: 验证所有 SKILL.md 格式**

```bash
python -c "
import yaml, re, pathlib
skills = pathlib.Path('plugins/invest-flow/skills/')
for f in sorted(skills.rglob('SKILL.md')):
    content = f.read_text()
    assert content.startswith('---'), f'{f}: no frontmatter start'
    m = re.search(r'\n---\s*\n', content[3:])
    fm = yaml.safe_load(content[3:m.start()+3])
    assert 'name' in fm, f'{f}: missing name'
    assert 'description' in fm, f'{f}: missing description'
    assert 'version' in fm, f'{f}: missing version'
    assert 'metadata' in fm, f'{f}: missing metadata'
    assert len(fm['description']) <= 1024, f'{f}: description too long ({len(fm["description"])})'
    print(f'  OK: {f.relative_to(skills.parent)}')
print('All 24 SKILL.md files validated.')
"
```

---

### Task 6: 验证 skills 在 Hermes 中可被发现

**Objective:** 测试 Hermes 能否加载这些 skills

**Files:**
- Test: `~/.hermes/skills/` symlink 或 copy

**Step 1: 创建符号链接测试**

```bash
# 创建软链接让 Hermes 发现 skills
mkdir -p ~/.hermes/skills/invest-flow
for d in plugins/invest-flow/skills/*/; do
    name=$(basename "$d")
    ln -sfn "$(pwd)/$d" ~/.hermes/skills/invest-flow/"$name"
done
```

**Step 2: 列出 skills**

```bash
hermes skills list | grep -i "invest\|chain-alpha\|fundamental\|company"
```

**Step 3: 如有问题排查**

检查 Hermes log 中 skill 加载错误：
```bash
grep -i "skill.*error\|skill.*fail" ~/.hermes/logs/*.log | tail -20
```

---

### Task 7: 更新 README.md 添加 Hermes 安装说明

**Objective:** 在 README.md 的 Quick Start 部分添加 Hermes 安装步骤

**Files:**
- Modify: `README.md`

**Step 1: 在 Quick Start 部分添加 Hermes 段落**

在 "### Claude Code" 之后新增 "### Hermes Agent" 段落：

```markdown
### Hermes Agent

1. Open this repository in Hermes Agent.
2. Install skills via symlink:
   ```bash
   mkdir -p ~/.hermes/skills/invest-flow
   for d in plugins/invest-flow/skills/*/; do
       name=$(basename "$d")
       ln -sfn "$(pwd)/$d" ~/.hermes/skills/invest-flow/"$name"
   done
   ```
3. Reload skills: `/reload-skills` or restart Hermes.
4. Use skills in the chat directly:
   ```
   Load chain-alpha-pipeline and run with theme humanoid robots.
   Use fundamental-analysis to analyze AAPL.
   ```

Alternatively, use Hermes `skills tap` if the repo is hosted on GitHub:
```bash
hermes skills tap add https://github.com/cryptowizard0/ai-investment-advisor
```
```

**Step 2: 将 "Use Skills In Agent" 段落更新为三平台**

在现有的 Codex/Claude Code 示例后添加 Hermes 示例：
```markdown
Use invest-flow:multi-agent-stock-analysis to analyze TSLA.   # Codex / Claude Code
/skill multi-agent-stock-analysis then analyze TSLA.           # Hermes
```

**Step 3: 更新 Maintenance Notes**

添加：
```markdown
- Hermes plugin discovery metadata lives in `.hermes-plugin/marketplace.json` and `plugins/invest-flow/.hermes-plugin/plugin.json`.
```

---

### Task 8: 更新 AGENTS.md 和 CLAUDE.md

**Objective:** 在项目指导文件中补充 Hermes 兼容性信息

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

**Step 1: AGENTS.md 更新**

- 在开头的 "compatible with both Codex and Claude Code" 改为 "compatible with Codex, Claude Code, and Hermes Agent"
- 在 Repository Structure 部分标注 `.hermes-plugin/` 目录
- 在 Maintenance Guidance 部分添加 Hermes 相关说明

**Step 2: CLAUDE.md 更新**

- 添加 Hermes marketplace 文件路径：`.hermes-plugin/marketplace.json`

---

### Task 9: 版本号同步和提交

**Objective:** 同步三个 plugin.json 和两个 marketplace.json 的版本号，提交所有更改

**Files:**
- Modify: `plugins/invest-flow/.codex-plugin/plugin.json:3` — version → `0.3.6`
- Modify: `plugins/invest-flow/.claude-plugin/plugin.json:3` — version → `0.3.6`
- Modify: `plugins/invest-flow/.hermes-plugin/plugin.json:3` — version → `0.3.6`

**Step 1: 版本号 bump**

```bash
# 统一设为 0.3.6
```

**Step 2: 提交**

```bash
git add -A
git commit -m "feat: add Hermes Agent compatibility

- Add .hermes-plugin/plugin.json manifest
- Add .hermes-plugin/marketplace.json local marketplace entry
- Update all 24 SKILL.md frontmatter to Hermes-compatible format
- Replace Claude/Codex-specific language with platform-neutral wording
- Update README.md with Hermes installation instructions
- Update AGENTS.md and CLAUDE.md
- Version bump to 0.3.6"
```

---

## 风险评估

- **Skill 命名冲突**：Hermes 使用 `~/.hermes/skills/` 作为 skill 存储，invest-flow 的 skills 使用 `invest-flow:` 前缀避免与其他已安装 skill 冲突 — 低风险
- **Frontmatter 兼容性**：新字段（version, author, license, metadata）是 Hermes 推荐但非强制字段，Codex/Claude Code 会忽略未知 frontmatter 字段 — 低风险
- **Plugin manifest 格式差异**：Hermes plugin 格式可能与 Codex/Claude Code 不同，需要 Task 1 确认 — 中风险
- **描述长度限制**：Hermes 要求 description ≤ 1024 字符，现有部分 skill 描述可能超长需截断 — 中风险

---

## 开放问题

1. Hermes plugin manifest 的准确 JSON Schema 是什么？需要在 Task 1 中确认
2. 是否需要 `.hermesignore` 文件来排除无关文件？
3. Hermes 的 skill 加载是否支持 `skills: "./skills/"` 这种相对路径指向？
4. 是否需要为 Hermes 单独创建一个 profile？
