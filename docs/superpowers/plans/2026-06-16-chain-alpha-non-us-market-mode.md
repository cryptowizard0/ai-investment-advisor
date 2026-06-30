# Chain Alpha Non-US Market Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update chain-alpha so A 股、港股、日股、台股主板候选和美股/ADR 一样进入第三步验证与仓位建议，仅未上市和仅 OTC 粉单不给仓位。

**Architecture:** This is a Markdown skill contract change, not a Python runtime change. The implementation updates the three downstream chain-alpha skills that currently encode US-listed/ADR assumptions, confirms mismatch discovery already uses a global market scope, then validates the text contract and reruns one human-robot pipeline report as an end-to-end proof.

**Tech Stack:** Markdown skill files, YAML frontmatter, Python `unittest`, existing InvestFlow skill/report conventions.

---

## File Structure

- Modify: `plugins/invest-flow/skills/chain-alpha-verification/SKILL.md`
  - Responsibility: public third-step skill contract, supported markets, trigger scope, warehouse position semantics.
- Modify: `plugins/invest-flow/skills/chain-alpha-verification/references/methodology.md`
  - Responsibility: market-specific valuation and drawdown methodology, unchanged scoring and sizing formulas.
- Modify: `plugins/invest-flow/skills/chain-alpha-verification/references/report-template.md`
  - Responsibility: verification card fields for market, same-market valuation benchmark, and local-market drawdown basis.
- Modify: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md`
  - Responsibility: second-step public contract for candidate investability and Step 3 eligibility.
- Modify: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/methodology.md`
  - Responsibility: tie-break and candidate treatment without US-only preference.
- Modify: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/report-template.md`
  - Responsibility: Step 2 report fields and Step 3 handoff table.
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md`
  - Responsibility: orchestration wording for Step 2 candidate output and Step 3 top-K selection.
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md`
  - Responsibility: fan-out top-K selection, funnel fallback, handoff contract, and failure handling.
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/references/subagent-prompts.md`
  - Responsibility: Step 2 and Step 3 dispatch prompts and structured final-message fields.
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/references/report-template.md`
  - Responsibility: final funnel table label.
- Read/confirm: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md`
  - Responsibility: confirm default global scope language already exists.
- Read/confirm: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/references/methodology.md`
  - Responsibility: confirm representative-company field already requires global suppliers including China/Japan/Korea/Taiwan/Europe.
- Create output during final proof run: `output/chain-alpha-*/...`
  - Responsibility: new human-robot rerun artifacts using append suffixes when files already exist.

## Current Workspace Note

There may already be uncommitted draft edits in the listed files from an earlier premature implementation attempt. Execution workers must not revert those edits without explicit user approval. Treat the draft as working material: compare it against every task below, keep matching lines, fix mismatches, and only commit after task-level verification passes.

### Task 1: Preflight And Baseline

**Files:**
- Read: `docs/superpowers/specs/2026-06-16-chain-alpha-non-us-market-mode-design.md`
- Read: `plugins/invest-flow/skills/chain-alpha-verification/SKILL.md`
- Read: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md`
- Read: `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md`
- Read: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md`

- [ ] **Step 1: Check working tree before edits**

Run:

```bash
git status --short
```

Expected: either a clean tree or only previously drafted edits to the chain-alpha files listed in this plan. If unrelated files are dirty, leave them untouched and mention them in the task result.

- [ ] **Step 2: Locate all old market-scope phrases**

Run:

```bash
rg -n "US-listed|US listed|US-listed/ADR|US-investable|美股/ADR|非美股|是否美股|候选全为非美股|只挑美股|不进第三步|仅这些进第三步" \
  plugins/invest-flow/skills/chain-alpha-verification \
  plugins/invest-flow/skills/chain-alpha-monopoly-screen \
  plugins/invest-flow/skills/chain-alpha-pipeline \
  plugins/invest-flow/skills/chain-alpha-mismatch-discovery
```

Expected: hits identify the exact phrases this plan will replace. After implementation, the only remaining `美股/ADR` wording should describe one supported market among several, not a gate.

- [ ] **Step 3: Confirm spec scope**

Run:

```bash
sed -n '1,130p' docs/superpowers/specs/2026-06-16-chain-alpha-non-us-market-mode-design.md
```

Expected: the scope says only the four chain-alpha skills change, all hard gate numbers stay unchanged, no global market-mode switch is introduced, and no Python script is added.

- [ ] **Step 4: Commit preflight only if no file content changed**

No commit is needed for this read-only task.

### Task 2: Update chain-alpha-verification Market Contract

**Files:**
- Modify: `plugins/invest-flow/skills/chain-alpha-verification/SKILL.md`
- Modify: `plugins/invest-flow/skills/chain-alpha-verification/references/methodology.md`
- Modify: `plugins/invest-flow/skills/chain-alpha-verification/references/report-template.md`

- [ ] **Step 1: Replace the SKILL.md description line**

In `plugins/invest-flow/skills/chain-alpha-verification/SKILL.md`, set the frontmatter description to exactly:

```yaml
description: "chain-alpha 工作流第三步：对全球主要可投市场（美股/ADR、A 股、港股、日股、台股主板）候选公司做最终验证——环节收入占比双轨硬门槛（≥40% 纯正 / 20-40% 增量贡献测试 / <20% 剔除）、100 分模型四档分级（金池子/通过/待验证/剔除）、最大回撤推断与风险预算法仓位上限。适用于：(1) 验证产业链筛出的候选公司是否可投并定仓位, (2) chain-alpha-pipeline 的第三步。输出保存至 ./output/chain-alpha-verification/。"
```

- [ ] **Step 2: Replace the SKILL.md overview market sentence**

In the Overview section, replace the input-scope sentence with:

```markdown
本 skill 是 chain-alpha 工作流的第三步：验证候选公司，给出四档结论和仓位上限。输入为全球主要可投市场候选（美股/ADR、A 股、港股、日股、台股主板，通常来自 `chain-alpha-monopoly-screen`）。
```

- [ ] **Step 3: Replace the SKILL.md non-US exclusion note**

In the Trigger section, replace the old non-US limitation paragraph with:

```markdown
非美股不再自动排除；A 股、港股、日股、台股主板候选按各自上市地市场口径验证并给仓位。未上市或仅 OTC 粉单标的只列背景参考，不给仓位建议。
```

- [ ] **Step 4: Add portfolio-percent wording to the position section**

Under `### 5) 最大回撤推断与仓位`, after the position formula bullet, ensure this bullet exists exactly once:

```markdown
- 仓位为组合占比 %，与候选公司计价币种无关。
```

- [ ] **Step 5: Insert methodology market-basis section**

In `plugins/invest-flow/skills/chain-alpha-verification/references/methodology.md`, insert this section immediately after the title and renumber the later sections:

```markdown
## 1. 市场口径

- 可投范围：美股/ADR 主板、A 股、港股、日股、台股主板。非美股不再自动排除。
- 估值比较：用候选公司自身上市地的同市场可比中位数（A 股比 A 股、日股比日股），不跨市场套用估值基准。
- 最大回撤：用候选公司本地市场历史价格；过去 5 年数据不足时，用上市以来数据。
- 数据经 market-data-router 降级获取时，必须在报告中降低置信度并标注。
- 仓位为组合占比 %，与候选公司的计价币种无关。
- 未上市或仅 OTC 粉单标的列背景参考，不给仓位建议。
```

Expected heading order after this step:

```markdown
## 1. 市场口径
## 2. 环节收入占比（双轨硬门槛）
## 3. 100 分模型评分标准
## 4. 最大回撤推断（三情景取最大）
## 5. 仓位公式
```

- [ ] **Step 6: Replace drawdown methodology lines**

In `## 4. 最大回撤推断（三情景取最大）`, set the first two numbered lines to:

```markdown
1. 历史回撤：候选公司本地市场价格过去 5 年（不足则上市以来）最大回撤。
2. 估值压缩情景：估值回到本地市场历史中位数或同市场可比公司中位数对应的跌幅。
```

- [ ] **Step 7: Add portfolio-percent wording to methodology position formula**

At the end of `## 5. 仓位公式`, ensure this line exists exactly once:

```markdown
- 仓位为组合占比 %，与候选公司的计价币种无关。
```

- [ ] **Step 8: Update verification report template header**

In `plugins/invest-flow/skills/chain-alpha-verification/references/report-template.md`, add this field under `- 所属环节`:

```markdown
- 上市地/市场：{美股/ADR/A股/港股/日股/台股主板/仅粉单/未上市}
```

- [ ] **Step 9: Update verification report template valuation and drawdown rows**

In the scoring table, set the valuation basis cell to:

```markdown
| 估值与透支度 | | 20 | 同市场可比中位数：{市场} {N} vs 本公司 {N} |
```

In `## 四、业绩与估值细节`, add:

```markdown
- 同市场估值基准：{市场 + 可比公司清单 + 中位数}
```

In `## 五、最大回撤推断`, set the first two rows to:

```markdown
| 历史回撤 | | {本地市场价格，过去 5 年或上市以来} |
| 估值压缩 | | {本地市场历史中位数或同市场可比中位数} |
```

- [ ] **Step 10: Verify verification files**

Run:

```bash
rg -n "全球主要可投市场|非美股不再自动排除|同市场可比中位数|本地市场历史价格|仓位为组合占比|上市地/市场" \
  plugins/invest-flow/skills/chain-alpha-verification
```

Expected: at least one hit for every phrase in the command.

- [ ] **Step 11: Commit verification contract**

Run:

```bash
git add plugins/invest-flow/skills/chain-alpha-verification/SKILL.md \
  plugins/invest-flow/skills/chain-alpha-verification/references/methodology.md \
  plugins/invest-flow/skills/chain-alpha-verification/references/report-template.md
git commit -m "docs: support non-us chain-alpha verification"
```

Expected: commit succeeds only after Step 10 passes.

### Task 3: Update chain-alpha-monopoly-screen Handoff Contract

**Files:**
- Modify: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md`
- Modify: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/methodology.md`
- Modify: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/report-template.md`

- [ ] **Step 1: Replace SKILL.md overview output sentence**

Set the Overview output sentence to:

```markdown
本 skill 是 chain-alpha 工作流的第二步：找壁垒、找垄断、排除低端竞争。输入一个供需错位环节（通常来自 `chain-alpha-mismatch-discovery`），输出该环节内 ≤10 家通过硬门槛的候选公司，并标注上市地与可投性。
```

- [ ] **Step 2: Replace global-company field wording**

In `### 3) 列全球公司格局`, set the company-field bullet to:

```markdown
- 每家公司标注：总部/上市地、可投性（可投主板 / 仅粉单 / 未上市）、在该子环节的产品和份额估计。
```

- [ ] **Step 3: Replace Step 3 eligibility wording**

In `### 6) 输出报告`, replace the US-only Step 3 paragraph with:

```markdown
- 标注每家候选的上市地与可投性；所有可投主板候选（美股/ADR、A 股、港股、日股、台股主板）均可进入第三步 `chain-alpha-verification`。仅粉单/未上市的最强格局者作为产业格局背景保留在报告中。
```

- [ ] **Step 4: Replace methodology tie-break**

In `references/methodology.md`, replace the final tie-break sentence with:

```markdown
按总分排序取前 ≤10 家。同分时优先可投主板候选（美股/ADR、A 股、港股、日股、台股主板）；仅粉单/未上市公司可作为格局背景保留。
```

- [ ] **Step 5: Update report template global landscape table**

In `references/report-template.md`, set the global landscape header to:

```markdown
| 公司 | 总部/上市地 | 可投性（可投主板/仅粉单/未上市） | 产品 | 份额估计 | 证据等级 |
|---|---|---|---|---|---|
```

- [ ] **Step 6: Update report template Step 3 candidates section**

Set section six to:

```markdown
## 六、进入第三步的可投候选（标注市场）

| 公司 | Ticker | 上市地与可投性 | 子环节 | 总分 | 占比初值（置信度） | CR3 证据等级 | 待第三步核实事项 |
|---|---|---|---|---|---|---|---|

仅粉单/未上市的最强格局者（产业格局背景，不给仓位）：{清单}
```

- [ ] **Step 7: Verify monopoly-screen files**

Run:

```bash
rg -n "上市地与可投性|所有可投主板候选|进入第三步的可投候选|仅粉单/未上市的最强格局者" \
  plugins/invest-flow/skills/chain-alpha-monopoly-screen
```

Expected: at least one hit for every phrase in the command.

- [ ] **Step 8: Verify no US-only gate remains in monopoly-screen**

Run:

```bash
rg -n "仅这些进第三步|非美股垄断者（产业格局背景，不进第三步）|是否 US-listed/ADR|US-investable" \
  plugins/invest-flow/skills/chain-alpha-monopoly-screen
```

Expected: no output and exit code 1.

- [ ] **Step 9: Commit monopoly-screen contract**

Run:

```bash
git add plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md \
  plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/methodology.md \
  plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/report-template.md
git commit -m "docs: carry investability through monopoly screen"
```

Expected: commit succeeds only after Steps 7 and 8 pass.

### Task 4: Update chain-alpha-pipeline Top-K And Handoff Contract

**Files:**
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md`
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md`
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/references/subagent-prompts.md`
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/references/report-template.md`

- [ ] **Step 1: Replace Step 2 output bullets in SKILL.md**

Set the final two bullets of `### Step 2: chain-alpha-monopoly-screen（步内 fan-out）` to:

```markdown
- 每个工作单元产出：该环节 ≤10 家候选（25 分排序），标注上市地与可投性。
- 主 agent 收齐各环节交接字段，汇总候选池，跨市场按 25 分排序，挑可投主板候选 top-K（默认 6）进入 Step 3。
```

- [ ] **Step 2: Replace methodology Step 3 top-K rule**

In `references/methodology.md`, set the Step 3 top-K bullet to:

```markdown
- **Step 3 收口（top-K）**：Step 2 的可投主板候选可能很多，主 agent 跨市场按 25 分排序只取 **top-K（默认 6）** 进入 Step 3 fan-out，不对全部可投候选逐一验证。
```

- [ ] **Step 3: Replace methodology funnel fallback**

In the funnel table, set the Step 3 fallback row to:

```markdown
| Step 3 深挖 | 2-3 家 | 无"通过"及以上档位时触发兜底规则：列出最强格局者，不给仓位 |
```

- [ ] **Step 4: Replace methodology Step 2 handoff fields**

Set the Step 2 handoff paragraph to:

```markdown
Step 2 -> 主 agent（每家候选）：公司名、Ticker、子环节、候选 25 分、占比初值与置信度、CR3 证据等级、上市地与可投性（可投主板，注明市场如 A股/港股/日股/台股/美股；仅粉单；未上市）、待核实事项。
```

- [ ] **Step 5: Replace methodology failure rule**

In `## 5. 失败与降级处理`, replace the non-US skip rule with:

```markdown
- **Step 2 候选全为不可投（未上市/仅粉单）**：Step 3 跳过，报告说明可投资性受限，列出最强格局者作背景参考。
```

- [ ] **Step 6: Replace Step 2 subagent handoff row**

In `references/subagent-prompts.md`, set the candidates row to:

```markdown
- 公司 | Ticker | 子环节 | 候选25分 | 占比初值(置信度) | CR3证据等级 | 上市地与可投性（可投主板，注明市场如 A股/港股/日股/台股/美股；仅粉单；未上市） | 待核实事项
```

- [ ] **Step 7: Replace Step 2 to Step 3收口 paragraph**

Set the收口 paragraph to:

```markdown
主 agent 收齐各环节候选后，跨市场按候选 25 分排序，只挑可投主板候选 **top-K（默认 6）** 进入 Step 3 fan-out，不对全量候选逐一派发。单波并行默认 ≤6 个 subagent，超出分批。
```

- [ ] **Step 8: Add market field to Step 3 prompt**

Set the Step 3 input placeholder line to:

```markdown
输入占位符：`{主题}`、`{环节名称}`、`{公司}`、`{Ticker}`、`{上市地与可投性}`、`{子环节}`、`{候选25分}`、`{占比初值与置信度}`、`{CR3证据等级}`、`{待核实事项}`、`{Step2报告路径}`。
```

Set the first prompt context line to:

```text
主题：{主题}；所属环节：{环节名称}；公司：{公司}（{Ticker}）；上市地与可投性：{上市地与可投性}；子环节：{子环节}。
```

Set task item 1 to:

```text
1. 读取 invest-flow:chain-alpha-verification 的 SKILL.md 与 references/methodology.md，严格按其规则执行；按候选公司上市地使用同市场可比估值与本地市场历史回撤口径。
```

- [ ] **Step 9: Update pipeline report template funnel label**

In `references/report-template.md`, set the fourth funnel row to:

```markdown
| 可投候选进入验证（标注市场） | | |
```

- [ ] **Step 10: Verify pipeline files**

Run:

```bash
rg -n "跨市场按 25 分排序|跨市场按候选 25 分排序|上市地与可投性|候选全为不可投|可投候选进入验证" \
  plugins/invest-flow/skills/chain-alpha-pipeline
```

Expected: at least one hit for every phrase in the command.

- [ ] **Step 11: Verify no pipeline non-US skip remains**

Run:

```bash
rg -n "候选全为非美股|只挑美股|是否美股或ADR|US-listed 进入验证" \
  plugins/invest-flow/skills/chain-alpha-pipeline
```

Expected: no output and exit code 1.

- [ ] **Step 12: Commit pipeline contract**

Run:

```bash
git add plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md \
  plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md \
  plugins/invest-flow/skills/chain-alpha-pipeline/references/subagent-prompts.md \
  plugins/invest-flow/skills/chain-alpha-pipeline/references/report-template.md
git commit -m "docs: select chain-alpha candidates across markets"
```

Expected: commit succeeds only after Steps 10 and 11 pass.

### Task 5: Confirm mismatch-discovery Needs No Scope Change

**Files:**
- Read: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md`
- Read: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/references/methodology.md`

- [ ] **Step 1: Confirm SKILL.md already has global default scope**

Run:

```bash
rg -n "默认全球视角（含中国大陆及日韩台欧）" \
  plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md
```

Expected: one hit.

- [ ] **Step 2: Confirm methodology representative-company field already requires global suppliers**

Run:

```bash
rg -n "全球代表公司，必须含中国大陆及日韩台欧供应商" \
  plugins/invest-flow/skills/chain-alpha-mismatch-discovery/references/methodology.md
```

Expected: one hit.

- [ ] **Step 3: Commit only if a file had to be changed**

Expected: no commit for this task because the spec says current wording already satisfies the requirement.

### Task 6: Validate Skill Contracts And Existing Tests

**Files:**
- Test: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`
- Test: `plugins/invest-flow/skills/company-buyability-score/scripts/tests/test_generate_report.py`
- Test: `plugins/invest-flow/skills/non-consensus-company-discovery/scripts/tests/test_generate_report.py`
- Test: `plugins/invest-flow/skills/daily-us-market-scan/scripts/tests/test_create_report.py`
- Test: `plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py`
- Test: `plugins/invest-flow/skills/output-report-index/scripts/tests/test_serve_reports.py`

- [ ] **Step 1: Validate frontmatter and required phrases**

Run:

```bash
python - <<'PY'
from pathlib import Path
import re
import yaml

skills = [
    Path("plugins/invest-flow/skills/chain-alpha-verification/SKILL.md"),
    Path("plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md"),
    Path("plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md"),
    Path("plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md"),
]
for path in skills:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"missing frontmatter: {path}"
    data = yaml.safe_load(match.group(1))
    assert data["name"] == path.parent.name, f"name mismatch: {path}"

required = {
    "plugins/invest-flow/skills/chain-alpha-verification/SKILL.md": [
        "全球主要可投市场",
        "非美股不再自动排除",
        "仅 OTC 粉单标的只列背景参考",
    ],
    "plugins/invest-flow/skills/chain-alpha-verification/references/methodology.md": [
        "同市场可比中位数",
        "本地市场历史价格",
        "仓位为组合占比 %",
    ],
    "plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md": [
        "上市地与可投性",
        "所有可投主板候选",
        "仅粉单/未上市的最强格局者",
    ],
    "plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md": [
        "跨市场按 25 分排序",
        "上市地与可投性",
        "候选全为不可投",
    ],
    "plugins/invest-flow/skills/chain-alpha-pipeline/references/subagent-prompts.md": [
        "上市地与可投性",
        "跨市场按候选 25 分排序",
        "同市场可比估值与本地市场历史回撤",
    ],
}
for file_name, phrases in required.items():
    text = Path(file_name).read_text(encoding="utf-8")
    for phrase in phrases:
        assert phrase in text, f"missing {phrase!r} in {file_name}"

for file_name in required:
    text = Path(file_name).read_text(encoding="utf-8")
    forbidden = [
        "只挑美股",
        "候选全为非美股",
        "是否美股或ADR",
        "非美股公司不做验证",
        "仅这些进第三步",
    ]
    for phrase in forbidden:
        assert phrase not in text, f"forbidden {phrase!r} in {file_name}"

print("chain-alpha non-us market contract ok")
PY
```

Expected:

```text
chain-alpha non-us market contract ok
```

- [ ] **Step 2: Run existing helper tests**

Run:

```bash
python -m unittest \
  plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py \
  plugins/invest-flow/skills/company-buyability-score/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/non-consensus-company-discovery/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/daily-us-market-scan/scripts/tests/test_create_report.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_serve_reports.py
```

Expected:

```text
Ran 50 tests

OK
```

- [ ] **Step 3: Commit validation state**

If Tasks 2-4 were committed separately and Task 5 made no change, no commit is needed here. If validation required a small fix, commit only that fix:

```bash
git add plugins/invest-flow/skills/chain-alpha-verification \
  plugins/invest-flow/skills/chain-alpha-monopoly-screen \
  plugins/invest-flow/skills/chain-alpha-pipeline \
  plugins/invest-flow/skills/chain-alpha-mismatch-discovery
git commit -m "docs: validate chain-alpha market contract"
```

Expected: commit only when there are staged validation fixes.

### Task 7: Rerun Human-Robot Pipeline As End-To-End Proof

**Files:**
- Create: `output/chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-人形机器人-2026-06-16*.md`
- Create: `output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-*-2026-06-16*.md`
- Create: `output/chain-alpha-verification/chain-alpha-verification-*-2026-06-16*.md`
- Create: `output/chain-alpha-pipeline/chain-alpha-pipeline-人形机器人-2026-06-16*.md`

- [ ] **Step 1: Locate existing human-robot reports to avoid overwrites**

Run:

```bash
rg --files output | rg "人形机器人|humanoid|机器人"
```

Expected: existing files, if any, remain in place. New files must use the repo convention of appending `(1)`, `(2)`, or another non-overwriting suffix when the base filename already exists.

- [ ] **Step 2: Run the pipeline with the new market contract**

In the agent session, invoke the packaged skill with this exact user-facing task:

```text
使用 invest-flow:chain-alpha-pipeline 分析 人形机器人。按 2026-06-16 已更新的非美股市场模式执行：美股/ADR、A 股、港股、日股、台股主板都是可投主板候选；候选不可因非美股被剔除；未上市和仅 OTC 粉单只列背景、不给仓位。Step 2 到 Step 3 的交接字段必须使用“上市地与可投性”。绿的谐波、金力永磁、新剑传动、五洲新春等如通过 Step 2 可进入 Step 3 验证。所有输出写入既有 output 目录，已存在文件追加 (1)(2)，不得覆盖旧报告。
```

Expected: the final pipeline report cites Step 1, Step 2, and Step 3 report paths and includes A 股 candidates in the Step 3 verification flow when they pass Step 2 gates.

- [ ] **Step 3: Verify A 股 candidates were not filtered solely by market**

Run:

```bash
rg -n "绿的谐波|金力永磁|新剑传动|五洲新春|上市地与可投性|A股|A 股|仓位上限|档位" \
  output/chain-alpha-pipeline \
  output/chain-alpha-verification \
  output/chain-alpha-monopoly-screen
```

Expected: hits show A 股 candidates have `上市地与可投性` fields and Step 3 outcomes or explicit non-market rejection reasons. A candidate may still fail revenue-share, score, data, or investability gates; it must not fail because it is non-US.

- [ ] **Step 4: Regenerate report indexes after new output files**

Run:

```bash
python plugins/invest-flow/skills/output-report-index/scripts/generate_index.py
```

Expected: `output/index.md` and `output/index.html` include the new chain-alpha reports.

- [ ] **Step 5: Commit rerun artifacts**

Run:

```bash
git add output/chain-alpha-mismatch-discovery \
  output/chain-alpha-monopoly-screen \
  output/chain-alpha-verification \
  output/chain-alpha-pipeline \
  output/index.md \
  output/index.html
git commit -m "docs: rerun humanoid robot chain-alpha pipeline"
```

Expected: commit includes only new report artifacts and index updates.

### Task 8: Final Review

**Files:**
- Review: all files changed by Tasks 2-7

- [ ] **Step 1: Check diff hygiene**

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 2: Confirm changed files stay within scope**

Run:

```bash
git status --short
```

Expected: no unstaged changes except user-owned unrelated files. Expected committed file families are the chain-alpha skill docs, new human-robot reports, and output indexes.

- [ ] **Step 3: Summarize final verification**

Final response must include:

```text
- Skill docs updated: verification, monopoly-screen, pipeline; mismatch-discovery confirmed no-op.
- Contract validation passed.
- Existing 50 helper tests passed.
- Human-robot pipeline rerun generated new non-overwriting output files.
- A 股 candidates were allowed into Step 3 when they passed upstream gates.
```

Expected: no claim of completion unless every listed verification is true.

## Self-Review

Spec coverage:
- Default stock pool changed from US-only to major investable global markets: Tasks 2-4.
- Non-US candidates receive full verification and position sizing: Task 2 and Task 7.
- Same-market valuation and local-market drawdown: Task 2.
- Only unlisted and OTC pink sheets are no-position background: Tasks 2-4.
- Only chain-alpha skills touched; other skills excluded: File Structure and Task 8.
- No new Python scripts and no global market-mode switch: Task 1 scope check.
- Handoff field changed to `上市地与可投性`: Tasks 3-4 and Task 6.
- Human-robot rerun proof: Task 7.

Placeholder scan:
- The plan contains exact file paths, exact replacement snippets, exact commands, and expected outputs.
- No task depends on an unspecified implementation choice.

Type and name consistency:
- The handoff field name is consistently `上市地与可投性`.
- Supported market wording is consistently `美股/ADR、A 股、港股、日股、台股主板`.
- Non-position background wording is consistently `未上市` and `仅 OTC 粉单` / `仅粉单`.
