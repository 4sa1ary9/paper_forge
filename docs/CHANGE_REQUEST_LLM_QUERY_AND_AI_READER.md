# LLM Query Planner 与 ai-paper-reader 接入变更设计

## 背景

当前 PaperForge 的论文输入已经支持标题、arXiv ID 和 URL，但标题搜索仍偏工程直连：用户输入会被直接拿去查 arXiv，并默认取前几个结果。这个策略在精确标题或 arXiv ID 上可用，但在简称、俗称和历史经典论文上容易跑偏。

典型例子：

```text
用户输入：unet
用户真实意图：U-Net: Convolutional Networks for Biomedical Image Segmentation
可能搜索结果：大量 U-Net 变体、医学分割改进版或其他同名方法
```

用户还提供了现有 Codex skill：

```text
C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md
```

这个 skill 的目标是“深度解析 AI 论文，生成可直接发布的专业阅读笔记”。它定义了元信息、TL;DR、论文概述、背景动机、核心方法、实验分析、深度 Q&A、总结与思考，以及图表处理规范。

## 目标

### 1. LLM Query Planner

在 arXiv 查询前增加一个可选规划步骤：

```text
用户输入
  -> query planner 判断用户真正想找哪篇论文
  -> 生成 canonical paper title / author hint / year hint / search query
  -> arXiv 查询
  -> metadata resolution
```

第一版重点解决：

- `unet`、`u-net`、`u net` 这类经典简称优先解析到原始 U-Net 论文；
- 标题不完整时，尽量生成 canonical title 再搜索；
- arXiv ID / arXiv URL / PDF URL 不经过 LLM 改写；
- LLM 不可用、返回空或 JSON 不合法时，回退到原始查询；
- 规划结果写入 `notes/query-plan.md`，方便复盘为什么搜到了这篇论文。

### 2. ai-paper-reader Prompt Pack

PaperForge 运行时不能直接把本地 Codex skill 当作 Python 函数导入。因此第一版不做“应用内自动调用 skill”，而是生成一份可复制给另一个 Codex 对话的提示词：

```text
ResearchJob artifacts
  -> metadata / notes / evidence map / image manifest
  -> notes/ai-paper-reader-prompt.md
  -> 用户复制到 Codex
  -> Codex 读取 ai-paper-reader SKILL.md
  -> 生成专业阅读笔记
```

Prompt 必须明确要求另一个对话读取这个 skill：

```text
C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md
```

第一版输出建议：

- `notes/ai-paper-reader-prompt.md`
- timeline step：`note.prepare_ai_paper_reader_prompt`
- artifact label：`AI Paper Reader Prompt`

## 非目标

- 不在第一版中把 Codex skill 嵌入 Streamlit 运行时。
- 不要求配置真实 LLM provider 才能运行基础 workflow。
- 不自动覆盖现有 `notes/README.md` 的保守证据草稿。
- 不把 skill 输出包装成已经人工审核的最终论文解读。
- 不在 query planner 中联网搜索开放网页；只规划 arXiv 查询意图。

## 推荐实现设计

### 新增 `paperforge/query_planner.py`

建议数据结构：

```python
@dataclass
class QueryPlan:
    original_input: str
    canonical_title: str
    search_query: str
    author_hint: str | None = None
    year_hint: int | None = None
    rationale: str = ""
    confidence: str = "low"
    used_llm: bool = False
```

建议函数：

```python
def plan_paper_query(raw_input: str, client: QueryPlannerClient | None = None) -> QueryPlan:
    ...
```

第一版必须有确定性别名表，保证没有 LLM 时也能正确处理经典简称：

```text
unet / u-net / u net
  -> U-Net: Convolutional Networks for Biomedical Image Segmentation
  -> author hint: Ronneberger
  -> year hint: 2015
```

LLM client 建议只做可注入接口，不在第一版绑定具体 provider。测试中使用 fake client。

### 修改 `paperforge/arxiv_client.py`

建议保持现有 API 兼容，在 intake 层把 `QueryPlan.search_query` 传入已有查询函数即可。

如果要加过滤逻辑，第一版只做保守重排：

- canonical title exact / normalized match 优先；
- author hint 命中优先；
- year hint 命中优先；
- 没有明显命中时保留 arXiv 原始排序。

### 修改 `paperforge/intake_agent.py`

在 intake workflow 的论文身份识别前加入可选步骤：

```text
query.plan_paper_identity
```

产物：

```text
notes/query-plan.md
```

状态：

- `completed`：生成 query plan 并成功进入 arXiv 查询；
- `partial`：LLM 不可用或返回不可解析，已 fallback；
- `failed`：只有在规划步骤阻断后续流程时使用，第一版尽量不用。

### 新增 `paperforge/ai_paper_reader_prompt.py`

建议函数：

```python
def run_ai_paper_reader_prompt_pack(job: ResearchJob) -> ResearchJob:
    ...
```

生成的 `notes/ai-paper-reader-prompt.md` 至少包含：

- 要读取的 skill 路径；
- 论文工作区路径；
- `metadata.json`；
- `raw/paper.pdf`；
- `notes/README.md`；
- `notes/evidence-map.md` 或后续 `notes/evidence-chunks.md`；
- `images/manifest.md`；
- 输出目标：基于 ai-paper-reader 规范生成专业阅读笔记；
- 约束：不得编造论文内容，无法确认的内容标注为待核查。

### 修改 `app.py`

建议增加两个最小 UI 控件：

- intake 区域增加 `Use LLM query planner` 复选框；
- job 操作区增加 `Prepare ai-paper-reader Prompt` 按钮。

第一版不需要在 UI 中暴露 provider key。LLM client 未配置时，query planner 仍可通过确定性别名表和 fallback 工作。

## 测试要求

建议新增：

- `tests/test_query_planner.py`
  - `unet` 解析到原始 U-Net 标题；
  - arXiv URL / ID 不被 LLM 改写；
  - fake LLM 返回 JSON 时使用 canonical title；
  - fake LLM 返回坏 JSON 时 fallback；
  - query plan markdown 写入 canonical title、rationale 和 fallback 信息。
- `tests/test_ai_paper_reader_prompt.py`
  - prompt 文件包含准确 skill 路径；
  - prompt 文件包含工作区关键 artifact；
  - 缺少 PDF 或 evidence map 时仍生成 prompt，并标注缺失项；
  - timeline 和 artifact 正确更新。

验证命令：

```powershell
uv run python -m pytest
uv run python -m compileall app.py paperforge tests scripts
git diff --check
```

## 风险与边界

- LLM 可能错误猜测论文标题，所以规划结果必须可见、可复盘、可 fallback。
- 经典简称不能完全依赖 LLM，必须先有小型确定性别名表。
- `ai-paper-reader` 是 Codex skill，不是 PaperForge Python 包；第一版应生成提示词，而不是假装应用能直接调用它。
- 后续如果要应用内生成完整阅读笔记，需要单独设计 provider、prompt、证据引用和人工审核流程。

## 建议优先级

这两个需求应该作为 Extension 0，排在段落级 evidence map 之前：

1. LLM Query Planner 先解决“找错论文”的入口问题。
2. ai-paper-reader Prompt Pack 先让现有 skill 能被稳定纳入 workflow。
3. 然后再进入 Extension 1: 段落级 Evidence Map，提高后续生成质量。
