# PaperForge Agent

**PaperForge Agent** 是一个用 Python 实现的 AI 论文研究 Agent。

它的目标不是再做一个“论文总结聊天框”，而是把一篇论文从零整理成一个可复用的研究工作区：

1. 自动识别论文标题、作者、摘要、PDF 地址和 TeX Source 地址。
2. 在 arXiv 查询前规划简称或模糊输入，例如把 `unet`、`u-net`、`u net` 解析到原始 U-Net 论文。
3. 创建规范化论文目录，保存元信息、query plan 和外部来源记录。
4. 用 timeline 记录 agent 每一步做了什么、产出了什么、哪里失败。
5. 下载 PDF 和 TeX Source，尝试解压论文源码。
6. 整理官方论文链接、本地资产状态和用户补充的外部资料 URL。
7. 从 PDF 提取图片并生成图片 manifest。
8. 记录 GitHub 代码仓库候选并生成 code references。
9. 生成论文笔记骨架，保留证据入口但不伪造深度解释。
10. 生成术语库骨架。
11. 生成疑难点骨架，并可从已有证据草稿派生疑难点候选。
12. 生成面试项目映射骨架，保留项目判断入口但不自动下结论。
13. 从 PDF 提取分页文本证据，生成 `notes/evidence-map.md`。
14. 从页码级 evidence map 切分 paragraph / chunk 级证据，生成 `notes/evidence-chunks.md`。
15. 基于 evidence chunks 做本地关键词检索，生成 `notes/evidence-search.md`。
16. 生成研究包状态检查报告，区分 required、recommended 和 optional 产物。
17. 生成深度笔记准备计划，标记哪些章节有证据支撑、哪些暂不能自动生成。
18. 写入保守版深度笔记 MVP，只填充 ready 的 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways，并保留页码/图片证据和人工复查标记。
19. 生成 `notes/ai-paper-reader-prompt.md`，让另一个 Codex 对话读取 `./docs/PAPER_SKILL.md` 和 `ai-paper-reader` skill 后继续写专业阅读笔记。
20. 在配置 LLM 后，按 `docs/PAPER_SKILL.md` 自动生成 `notes/ai-paper-reader-note.md`，并优先使用 `notes/evidence-chunks.md` 作为证据来源。
21. 在用户提供本地代码目录后，生成文件级和 Python function/class 级代码映射候选，不自动 clone 第三方仓库。
22. 评估论文作为面试项目素材的适配度，输出 high / medium / low / not recommended、最小 demo 范围和风险边界。
23. 支持多行论文输入，顺序创建多个 intake jobs，并保存 batch summary。

## 为什么做这个项目

学习 AI 论文时，真正耗时的地方通常不是“让 AI 总结一篇论文”，而是整个资料处理链路：

- 找正确的 PDF、arXiv 页面、OpenReview 页面、TeX Source 和官方仓库很麻烦。
- 论文、源码、图表、教程、笔记经常散落在不同地方。
- 单独看论文容易卡在公式、方法细节和实现对应关系上。
- 单独看代码又容易不知道它对应论文里的哪一部分。
- 社区教程有帮助，但来源分散，质量不稳定，很难和论文原文互相校验。
- 读完论文后，常常不知道它能不能变成自己的面试项目。

PaperForge Agent 要解决的是这个完整工作流，而不是单点问答。

## 当前技术栈

当前版本故意保持简单：

- **Python**：核心业务和 agent workflow。
- **uv**：项目依赖和本地虚拟环境管理。
- **Streamlit**：本地可视化工作台。
- **PyMuPDF**：PDF 图片提取。
- **pytest**：基础测试。
- **本地文件系统**：保存 job、metadata、notes 和后续论文资产。

不再使用 TypeScript、React、Express。这样项目更适合你学习和面试包装。

## 当前可运行能力

当前版本已经具备 LLM provider config + query planning + intake + batch intake + asset collection + source enrichment + PDF image extraction + code linking + note scaffold + terminology scaffold + doubts scaffold + interview mapping scaffold + package validation + PDF text evidence extraction + paragraph / chunk evidence extraction + local evidence search + deep note planning + conservative deep note writing MVP + ai-paper-reader prompt pack + chunk-grounded ai-paper-reader note generation + chunk-aware terminology evidence MVP + chunk-aware doubts evidence MVP + function-level code mapping evidence MVP + interview project assessment MVP 的最小闭环：

1. 输入论文标题、arXiv ID 或 URL。
2. Query Planner 先生成 canonical title / search query，并把规划结果写入 `notes/query-plan.md`；arXiv ID、arXiv URL 和 PDF URL 不改写。
3. Agent 调用 arXiv API 解析论文元信息。
4. 系统创建本地研究任务 `ResearchJob`。
5. 系统在 `.paperforge-data/paper-vault/` 下生成论文工作区。
6. 系统写入 `metadata.json` 和 `notes/external-sources.md`。
7. Asset Collector 下载 `raw/paper.pdf` 和 `raw/source.tar.gz`。
8. 系统尝试解压 `raw/tex-source/`。
9. Source Enrichment Agent 更新 `notes/external-sources.md`，记录本地 PDF/TeX 状态和用户补充 URL。
10. PDF Image Extractor 从 `raw/paper.pdf` 提取图片到 `images/` 并生成 `images/manifest.md`。
11. Code Linker Agent 生成 `notes/code-references.md`，记录 GitHub 候选仓库但不自动 clone。
12. Note Writer Agent 生成 `notes/README.md` 的结构化笔记骨架。
13. Terminology Agent 生成 `notes/terminology.md` 的术语库骨架。
14. Doubts Agent 生成 `notes/doubts.md` 的疑难点骨架。
15. Interview Mapper Agent 生成 `notes/interview-project.md` 的面试项目映射骨架。
16. PDF Text Evidence Extractor Agent 生成 `notes/evidence-map.md`，保留页码级文本证据入口。
17. Evidence Chunker Agent 读取 `notes/evidence-map.md`，生成 `notes/evidence-chunks.md`，记录 chunk id、page、section guess、字符数和文本 excerpt。
18. Evidence Retriever Agent 根据用户查询检索 `notes/evidence-chunks.md`，生成 `notes/evidence-search.md`，返回 chunk id、page、score 和 excerpt。
19. Research Package Validator Agent 生成 `notes/package-status.md`，检查研究包文件状态。
20. Deep Note Planner Agent 生成 `notes/deep-note-plan.md`，判断深度笔记章节准备度。
21. Deep Note Writer Agent 更新 `notes/README.md` 中 ready 的 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways，写入带页码/图片证据的保守草稿。
22. AI Paper Reader Prompt Pack 生成 `notes/ai-paper-reader-prompt.md`，明确要求另一个 Codex 对话读取 `./docs/PAPER_SKILL.md` 和 canonical skill 路径。
23. AI Paper Reader Note Writer 使用 OpenAI-compatible LLM 生成 `notes/ai-paper-reader-note.md`，优先读取 `notes/evidence-chunks.md` 的 chunk excerpt，缺失时 fallback 到 `notes/evidence-map.md`，同时保存 `notes/ai-paper-reader-generation-prompt.md` 方便复盘。
24. Terminology Agent 更新 `notes/terminology.md`，优先从 `notes/evidence-chunks.md` 抽取术语候选并保留 chunk id/page；chunks 缺失时 fallback 到页码证据。
25. Doubts Agent 更新 `notes/doubts.md`，优先从 method / experiment / limitation chunks 派生疑难点候选并保留 chunk id/page；chunks 缺失时 fallback 到主笔记证据草稿和术语条目。
26. Code Mapping Agent 在用户提供本地代码仓库路径后扫描代码文件，把 Core Method 证据词映射到候选代码路径和 Python function/class symbol，并更新 `notes/code-references.md`。
27. Interview Mapper Agent 更新 `notes/interview-project.md`，基于主笔记、代码映射和疑难点输出保守适配度评估、最小 demo 范围和风险。
28. Streamlit 页面展示论文摘要、任务状态、agent timeline 和 artifact 列表。
29. Batch Runner 支持多行输入，顺序调用 intake，保存 `.paperforge-data/batches/<batch-id>.json` 和 batch summary。

当前接续点：核心 MVP、Extension 0、LLM 执行层、段落级 evidence chunks、本地 evidence search、ai-paper-reader chunk evidence 接入、terminology / doubts chunk evidence 接入、function-level code mapping MVP 和多篇论文批处理 MVP 已完成。后续建议先做真实样例验证、demo 整理或再选择语义 / 向量检索等可选扩展。详见 [扩展路线图](docs/EXTENSION_ROADMAP.md)。

## 项目结构

```text
PaperForge-Agent/
├── app.py                         # Streamlit 页面入口
├── paperforge/                    # Python 核心代码
│   ├── arxiv_client.py             # arXiv 查询和解析
│   ├── ai_paper_reader_note.py      # LLM-backed ai-paper-reader note generation
│   ├── ai_paper_reader_prompt.py    # ai-paper-reader Codex handoff prompt
│   ├── asset_collector.py           # PDF / TeX Source 下载和解压
│   ├── batch_runner.py              # 多篇论文顺序 intake
│   ├── code_linker.py               # GitHub 候选仓库整理和本地代码映射证据
│   ├── deep_note_planner.py          # 深度笔记准备度计划
│   ├── deep_note_writer.py           # 保守版深度笔记 MVP
│   ├── doubts_agent.py              # 疑难点骨架和证据草稿生成
│   ├── evidence_chunker.py           # paragraph / chunk 级证据切分
│   ├── evidence_retriever.py         # 本地 evidence chunk 关键词检索
│   ├── interview_mapper.py           # 面试项目映射骨架和适配度评估
│   ├── intake_agent.py             # 论文 intake agent workflow
│   ├── llm_client.py                # OpenAI-compatible LLM client/config
│   ├── models.py                   # ResearchJob / AgentStep / Artifact 数据结构
│   ├── note_writer.py               # 论文笔记骨架生成
│   ├── package_validator.py          # 研究包状态检查
│   ├── pdf_image_extractor.py       # PDF 图片提取
│   ├── pdf_text_extractor.py        # PDF 文本证据提取
│   ├── query_planner.py             # arXiv 查询前的论文身份规划
│   ├── source_enrichment.py         # 外部来源和本地资产状态整理
│   ├── terminology_agent.py         # 术语库骨架和证据草稿生成
│   ├── slug.py                     # 论文目录名生成
│   ├── steps.py                    # timeline step 状态流转
│   └── storage.py                  # 本地文件读写
├── tests/                         # pytest 测试
├── scripts/                       # 本地真实样例流水线脚本
├── docs/                          # 项目文档
└── .paperforge-data/              # 本地生成数据，不进入 git
```

## 快速开始

**环境要求：Python >= 3.13**

```powershell
# 1. 克隆项目
git clone https://github.com/4sa1ary9/paper_forge.git
cd paper_forge

# 2. 安装依赖
uv venv --prompt agent .venv
uv sync

# 3. 复制环境变量模板（LLM 配置可选）
cp .env.example .env

# 4. 直接运行完整流水线（无需 LLM API key）
uv run python scripts/run_pipeline.py "https://arxiv.org/abs/2006.11239"

# 5. 或启动 Streamlit 界面
uv run streamlit run app.py
```

**无需 API Key 即可使用：** 流水线 19 个阶段中，只有 `ai-paper-reader note` 生成需要 LLM，其余所有阶段（论文解析、PDF 下载、图片提取、笔记骨架、证据提取与检索、深度笔记 MVP 等）都是本地运行，不依赖任何外部 API。

## 本地运行

项目用 uv 管理依赖。虚拟环境目录是 `.venv/`，激活后显示 `(agent)`。

```powershell
uv venv --prompt agent .venv
uv sync
```

Git Bash 激活：

```bash
source .venv/Scripts/activate
```

### Streamlit 界面

```powershell
uv run streamlit run app.py
```

界面按 5 个阶段组织：Intake → Assets → Scaffolds → Evidence → Deep Generation，每个阶段的按钮只有当前置条件满足时才会启用。

### 命令行流水线

```powershell
# 使用默认论文（DDPM）
uv run python scripts/run_pipeline.py

# 指定论文
uv run python scripts/run_pipeline.py "https://arxiv.org/abs/1706.03762"

# 附带外部资料 URL
uv run python scripts/run_pipeline.py "https://arxiv.org/abs/2006.11239" "https://github.com/hojonathanho/diffusion"

# 指定本地代码仓库用于代码映射
$env:PAPERFORGE_CODE_REPO = "C:/path/to/local/repo"
uv run python scripts/run_pipeline.py
```

LLM 配置会自动读取项目根目录的 `.env` 文件；`.env` 已在 `.gitignore` 中，不要提交真实 key。DeepSeek 的 OpenAI-compatible 配置示例：

```powershell
$env:PAPERFORGE_LLM_BASE_URL="https://api.deepseek.com"
$env:PAPERFORGE_LLM_API_KEY="<your-deepseek-api-key>"
$env:PAPERFORGE_QUERY_MODEL="deepseek-v4-flash"
$env:PAPERFORGE_READER_MODEL="deepseek-v4-pro"
```

也可以直接写入本地 `.env`：

```text
PAPERFORGE_LLM_BASE_URL=https://api.deepseek.com
PAPERFORGE_LLM_API_KEY=<your-deepseek-api-key>
PAPERFORGE_QUERY_MODEL=deepseek-v4-flash
PAPERFORGE_READER_MODEL=deepseek-v4-pro
```

`PAPERFORGE_QUERY_MODEL` 用于论文简称到 canonical title 的 query planner；`PAPERFORGE_READER_MODEL` 用于生成 `notes/ai-paper-reader-note.md` 这类复杂阅读笔记。

验证：

```powershell
uv run python -m pytest
```

## 文档入口

- [项目指南](docs/PROJECT_GUIDE.md)
- [流程规范](docs/WORKFLOW_SPEC.md)
- [扩展路线图](docs/EXTENSION_ROADMAP.md)
- [LLM 查询规划与 ai-paper-reader 变更设计](docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md)
- [给另一个 Codex 对话的实现提示词](docs/PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md)
- [文档规范](docs/DOCUMENTATION_GUIDE.md)
- [开发步骤记录](docs/BUILD_STEPS.md)
- [项目进度](docs/PROGRESS.md)

文档职责：

- `PROGRESS.md`：当前做到哪一步，适合每次重新打开项目时先看。
- `BUILD_STEPS.md`：阶段复盘，记录每一步为什么做、做了什么、如何验证。
- `PROJECT_GUIDE.md`：项目定位和面试叙事。
- `WORKFLOW_SPEC.md`：agent 流程和产物规范。
- `EXTENSION_ROADMAP.md`：核心 MVP 之后的扩展方向和推荐顺序。
- `CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md`：LLM 查询规划和 `ai-paper-reader` prompt pack 的变更设计。
- `PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md`：可复制给另一个 Codex 对话的实现提示词。
- `DOCUMENTATION_GUIDE.md`：说明文档如何维护。
