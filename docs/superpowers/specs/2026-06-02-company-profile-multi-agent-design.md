# Company Profile Multi-Agent Integration Design

Date: 2026-06-02
Status: Approved design, pending implementation plan
Scope:
- `plugins/invest-flow/skills/company-profile/`
- `plugins/invest-flow/skills/multi-agent-stock-analysis/`
- `README.md`
- `README.zh-CN.md`
- `AGENTS.md`

## Background

`multi-agent-stock-analysis` currently cross-checks a stock through six investment lenses:
fundamental analysis, institutional accumulation, GIE, reflexivity deep analysis,
Reportify, and non-consensus discovery. This helps validate an investment thesis, but
it does not reliably answer the first question a user has when they hear about a
company for the first time: what does this company actually do, where does it sit in
the value chain, why might it have an advantage, and who does it compete with?

Some of this information exists in `professional-investment-analyst`, but that skill
is a formal buy-side research report and is not part of the current default
multi-agent flow. The new capability should make company understanding the first step
of the default single-stock workflow.

## Goals

1. Add a dedicated `company-profile` skill that produces a reusable company primer.
2. Run `company-profile` by default as the first required step in
   `multi-agent-stock-analysis`.
3. Produce both a standalone Markdown company profile report and a structured handoff
   for the final summary composer.
4. Add a compact `公司画像摘要` section before the investment execution summary in
   the multi-agent report.
5. Keep AI positioning industry-generic by default: analyze the company normally first,
   then include AI value-chain relevance only when supported by evidence.
6. Preserve the existing six investment analysis dimensions and extend them rather
   than replacing them.

## Non-Goals

1. Do not turn `company-profile` into a buy/sell recommendation skill.
2. Do not make every company an AI company by narrative force.
3. Do not require a database or external persistent state.
4. Do not rewrite unrelated InvestFlow skills.
5. Do not migrate plugin paths; this repository intentionally keeps the packaged
   plugin under `plugins/invest-flow/`.

## Recommended Approach

Create a new packaged skill:

```text
plugins/invest-flow/skills/company-profile/
├── SKILL.md
└── references/
    └── report-template.md
```

The skill's purpose is company understanding, not investment timing. It answers:

- company overview
- core business and revenue model
- customers and downstream demand
- core technical advantages and barriers
- industry-chain position
- AI value-chain relevance, when evidence supports it
- competitors and industry position
- business model quality
- key uncertainties
- questions that downstream investment analysis must verify

`multi-agent-stock-analysis` then expands from six to seven default dimensions:

```text
company-profile
-> fundamental-analysis
-> institutional-accumulation-analysis
-> gie-investment-framework
-> reflexivity-deep-analysis
-> reportify-stock-analysis
-> non-consensus-company-discovery
-> summary composer
```

## Company Profile Report

The standalone report should use this structure:

```markdown
# {company}（{ticker}）公司画像报告

## 一页式公司画像
- 公司一句话定义
- 核心业务
- 主要客户 / 下游需求
- 收入来源
- 核心竞争力
- 行业地位
- AI 相关性结论
- 最重要的不确定性

## 1. 公司简介
## 2. 核心业务与收入结构
## 3. 核心技术优势与技术壁垒
## 4. 产业链位置
## 5. AI 产业链相关性
## 6. 竞争对手与行业地位
## 7. 商业模式质量
## 8. 投资分析前置问题
## 9. 数据来源与不确定性
```

The AI section must classify relevance as one of:

- `直接受益`
- `间接受益`
- `弱相关`
- `无明显相关`
- `不确定`

When relevant, it should identify the value-chain position, such as compute chips,
networking, memory, servers, cloud, software, data, power, cooling, equipment,
materials, or applications. It must distinguish actual revenue/customer exposure from
market narrative exposure.

## Multi-Agent Registry And Planning

Add `company-profile` to the registry with:

```text
skill_name: company-profile
agent_name: company_profile
stage: single_asset_context
required: true
output_dir: output/company-profile
prompt_template:
  使用 invest-flow:company-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
```

`basic_stock_specs()` must return `company-profile` as the first item. Existing six
dimensions keep their current relative order.

## Data Model

Add a `CompanyProfile` model:

```text
CompanyProfile
- one_liner: str
- business_summary: str
- core_products: list[str]
- revenue_model: str
- customers_and_end_markets: list[str]
- technical_advantages: list[str]
- moat_assessment: str
- industry_chain_position: str
- ai_relevance: str
- ai_value_chain_position: list[str]
- competitors: list[str]
- industry_position: str
- key_uncertainties: list[str]
- pre_analysis_questions: list[str]
- data_sources: list[str]
```

Extend `Handoff` with:

```text
company_profile: CompanyProfile | None
```

This keeps existing handoff fields compatible while giving the composer structured
data for the company primer. `PipelineResult.to_dict()` should serialize the nested
profile so the orchestration JSON can be reused for later review.

## Extraction

The first implementation should use deterministic Markdown extraction from the fixed
company-profile template. It should extract:

- one-line company definition
- business summary
- core products
- revenue model
- customers and end markets
- technical advantages
- moat assessment
- industry-chain position
- AI relevance and AI value-chain position
- competitors
- industry position
- key uncertainties
- pre-analysis questions
- data sources

If a field cannot be extracted, use an empty string or empty list and add the missing
field to `data_gaps`. Do not block downstream stages when optional profile fields are
missing.

## Summary Composer

The final multi-agent report should start with company understanding:

```markdown
# 综合分析报告 - {ticker}

作者：InvestmentFlow

## 公司画像摘要
| 项目 | 内容 |
|---|---|
| 公司一句话定义 | {one_liner} |
| 核心业务 | {business_summary} |
| 收入来源 | {revenue_model} |
| 核心技术 / 壁垒 | {technical_advantages} |
| 产业链位置 | {industry_chain_position} |
| AI 相关性 | {ai_relevance} / {ai_value_chain_position} |
| 主要竞争对手 | {competitors} |
| 行业地位 | {industry_position} |
| 关键不确定性 | {key_uncertainties} |

## 执行摘要
{execution_summary}
```

The composer should use structured `company_profile` fields to generate
`## 公司画像摘要` when present. If `company_profile` is absent, it should render a
company profile status row instead of falling back to other handoff fields. If
`company-profile` fails, the report can still be produced as partial output, but it
must warn that missing company context lowers confidence in the overall judgment.

`子报告索引` must list all seven dimensions, including `company-profile`.

## Output Conventions

Add:

```text
output/company-profile/company-profile-{TICKER}-{YYYY-MM-DD}.md
```

As with other report writers, existing files must not be overwritten. Scripts should
append numbered suffixes like `(1)` and `(2)` when necessary.

## Documentation Updates

Update:

- `AGENTS.md`: active skills, key files, output conventions, and maintenance notes.
- `README.md`: English skill list, recommended workflows, and output paths.
- `README.zh-CN.md`: Chinese skill list, recommended workflows, and output paths.
- `plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md`: seven-dimension
  default flow and new summary section.
- `plugins/invest-flow/skills/multi-agent-stock-analysis/references/workflow-guide.md`:
  workflow and handoff semantics.
- `plugins/invest-flow/skills/multi-agent-stock-analysis/assets/summary-report-template.md`:
  `公司画像摘要` and seven-item subreport index.

## Tests

Add or update unit tests for:

1. `CompanyProfile.to_dict()` and `Handoff.company_profile` serialization.
2. Registry ordering: `company-profile` is first in `basic_stock_specs()` and is
   required.
3. Prompt planning: prompt plans include the company profile prompt.
4. Extractor behavior: a fixed company profile Markdown sample populates the structured
   profile fields.
5. Composer behavior: `公司画像摘要` appears before `执行摘要`.
6. Composer fallback: missing or failed `company-profile` is reported as a data gap.
7. Subreport index: all seven dimensions are listed.

Run:

```bash
python -m unittest discover plugins/invest-flow -p 'test_*.py'
```

## Rollout

1. Add models and tests for `CompanyProfile`.
2. Add `company-profile` skill files and report template.
3. Add registry and planner integration.
4. Add extractor support for the company profile template.
5. Add composer summary table and failure fallback.
6. Update documentation and templates.
7. Run unit tests.
8. Manually generate a prompt plan for a known ticker and verify that the company
   profile prompt appears first.

## Acceptance Criteria

1. `multi-agent-stock-analysis` default prompt plan starts with `company-profile`.
2. The final summary report contains `## 公司画像摘要` before `## 执行摘要`.
3. The summary report links or statuses include seven subreports.
4. The company profile report explains core business, technology barriers,
   industry-chain position, AI relevance, competitors, and industry position.
5. Non-AI companies are not forced into AI relevance; they can be classified as weak,
   none, or uncertain.
6. Existing six analysis dimensions continue to work.
7. Unit tests pass with the repository's standard test command.
