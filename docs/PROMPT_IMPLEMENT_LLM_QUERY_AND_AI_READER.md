# 给另一个 Codex 对话的实现提示词

把下面整段发给另一个 Codex 对话即可。

```text
你是 Codex，请在本机项目 D:\AI Project\paper_forge 中实现两个小扩展：

1. LLM Query Planner：在 arXiv 查询前，先判断用户输入真正指向哪篇论文，生成 canonical paper title / search query，再去查询。
2. ai-paper-reader Prompt Pack：基于当前 job 的论文资料，生成一份可复制给 Codex 的专业论文阅读笔记提示词。

请先阅读这些文件，按项目现有约束工作：

- AGENTS.md
- README.md
- docs/PROGRESS.md
- docs/STATUS_REVIEW.md
- docs/WORKFLOW_SPEC.md
- docs/EXTENSION_ROADMAP.md
- docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md
- C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md

特别注意：

- 项目是 Python + Streamlit，不要引入 TypeScript、React、Express。
- 使用 uv：`uv run python -m pytest`。
- 生成数据放在 `.paperforge-data/`，不要提交进 git。
- 每次完成阶段后更新 `docs/PROGRESS.md`，较大阶段更新 `docs/BUILD_STEPS.md`。
- 不确定是否扩 scope 时，先写文档或说明，不直接扩大实现。

实现范围：

一、LLM Query Planner

新增 `paperforge/query_planner.py`，提供：

- `QueryPlan` 数据结构；
- `QueryPlannerClient` 可注入接口；
- `plan_paper_query(raw_input, client=None)` 函数；
- 生成 `notes/query-plan.md` 的函数。

行为要求：

- `unet`、`u-net`、`u net` 必须解析到原始论文：
  `U-Net: Convolutional Networks for Biomedical Image Segmentation`
- 同时记录 author hint `Ronneberger` 和 year hint `2015`。
- arXiv ID、arXiv URL、PDF URL 不要交给 LLM 改写。
- fake LLM 返回合法 JSON 时，使用 canonical title 和 search query。
- fake LLM 返回空、坏 JSON 或异常时，fallback 到原始输入或确定性别名表。
- query plan 必须写入 `notes/query-plan.md`，包含 original input、canonical title、search query、rationale、confidence、fallback 状态。
- 不要求第一版接真实 OpenAI API；可以只做 client interface 和 fake-client 测试。

修改 intake workflow：

- 在 `paperforge/intake_agent.py` 的 arXiv 查询前加入 query planning。
- timeline step 建议命名为 `query.plan_paper_identity`。
- 保持现有 title / arXiv ID / URL 输入兼容。
- Streamlit intake 区域增加一个最小复选框 `Use LLM query planner`。未配置真实 client 时，也能靠别名表和 fallback 工作。

二、ai-paper-reader Prompt Pack

新增 `paperforge/ai_paper_reader_prompt.py`，提供：

- `run_ai_paper_reader_prompt_pack(job)`。

生成文件：

- `notes/ai-paper-reader-prompt.md`

timeline step：

- `note.prepare_ai_paper_reader_prompt`

artifact label：

- `AI Paper Reader Prompt`

Prompt 文件必须明确写入并要求 Codex 读取这个 skill：

`C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md`

Prompt 文件至少包含：

- 论文工作区路径；
- `metadata.json` 路径；
- `raw/paper.pdf` 路径；
- `notes/README.md` 路径；
- `notes/evidence-map.md` 路径，如不存在则标注缺失；
- `images/manifest.md` 路径，如不存在则标注缺失；
- 要求生成符合 ai-paper-reader 规范的专业阅读笔记；
- 要求使用 skill 中的结构：元信息、TL;DR、论文概述、背景与动机、核心方法、实验分析、深度理解问答、总结与思考；
- 要求不得编造论文内容，无法从 artifacts 验证的内容标注为待核查。

修改 Streamlit：

- 在 job 操作区增加 `Prepare ai-paper-reader Prompt` 按钮。
- 点击后生成 prompt 文件并显示 artifact。

测试要求：

- 新增 `tests/test_query_planner.py`：
  - `unet` 解析到原始 U-Net；
  - arXiv URL / ID 不被改写；
  - fake LLM 合法 JSON 生效；
  - fake LLM 坏 JSON fallback；
  - query plan markdown 内容正确。
- 新增 `tests/test_ai_paper_reader_prompt.py`：
  - prompt 文件包含准确 skill 路径；
  - prompt 文件包含关键 artifact 路径；
  - 缺少 PDF 或 evidence map 时仍生成 prompt 并标注 missing；
  - timeline 和 artifact 更新正确。

实现顺序：

1. 先写 failing tests。
2. 实现 `query_planner.py`。
3. 接入 intake workflow 和 Streamlit。
4. 实现 `ai_paper_reader_prompt.py`。
5. 接入 Streamlit 按钮。
6. 更新 README、docs/PROGRESS.md、docs/BUILD_STEPS.md，必要时更新 docs/WORKFLOW_SPEC.md。
7. 运行验证：
   - `uv run python -m pytest`
   - `uv run python -m compileall app.py paperforge tests scripts`
   - `git diff --check`

请保持改动小而清楚。不要实现完整自动论文报告生成，不要把 Codex skill 当 Python 包导入，不要引入新的前后端技术栈。
```
