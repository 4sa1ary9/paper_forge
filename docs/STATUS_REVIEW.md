# PaperForge Agent 完成度核对

## 结论

**当前项目已经完成 Step 31 的 scaffold 闭环、LLM Query Planner、OpenAI-compatible LLM 执行层、PDF 文本证据提取、paragraph / chunk 级证据切分、本地 evidence search、深度笔记准备度计划、保守版深度笔记写入 MVP、ai-paper-reader Prompt Pack、chunk-grounded ai-paper-reader Note Generation、chunk-aware 术语证据 MVP、chunk-aware 疑难点证据 MVP、function-level 代码映射证据 MVP、面试项目适配度评估 MVP 和多篇论文批处理 MVP，但还没有完成文档中描述的最终研究包目标。**

最近核对日期：2026-05-25。当前状态是 Step 31 completed；核心 MVP、Extension 0、LLM 执行层、Extension 1、本地检索 MVP、ai-paper-reader chunk evidence 接入、terminology / doubts chunk evidence 接入、function-level code mapping MVP 和多篇论文批处理 MVP 已闭环。后续建议先做真实样例验证和 demo 整理。

更准确的表述是：

> PaperForge Agent 当前已经跑通单篇论文研究包的确定性 workflow、query plan、LLM-backed ai-paper-reader note、文件产物骨架、PDF 文本证据图、paragraph / chunk 级证据图、本地 evidence search、深度笔记 readiness gate、TL;DR / Paper Overview / Background and Motivation / Core Method / Experiments / Limitations / Deep Q&A / Practical Takeaways 的保守证据草稿、ai-paper-reader handoff prompt、chunk-grounded ai-paper-reader generation prompt、带 chunk id/page 证据的术语候选条目、带 chunk id/page 证据的疑难点候选、本地代码目录扫描得到的文件级和 Python function/class 级代码映射候选、面试项目适配度评估，以及多行输入顺序创建多个 intake jobs 的 batch workflow；但完整深度论文理解、术语自动解释、完整疑难点分析、语义/向量检索、line-level 代码映射、跨论文综述总结、完整项目方案仍然是后续规划。

所以项目不能说“完整完成”。可以说：

> 当前版本完成了可演示、可追踪、可扩展的 scaffold MVP。

## 已按文档完成的部分

| 规划能力 | 当前状态 | 说明 |
| --- | --- | --- |
| Python + Streamlit 本地工作台 | 已完成 | 当前没有继续使用 TypeScript/React/Express。 |
| uv 环境和 pytest 基线 | 已完成 | 当前测试基线为 `92 passed`。 |
| LLM Provider Config | 已完成 MVP | 支持 OpenAI-compatible `/chat/completions`，通过环境变量配置 DeepSeek base URL、API key 和模型。 |
| LLM Query Planner | 已完成 MVP | 在 arXiv 查询前生成 canonical title / search query，`unet`、`u-net`、`u net` 会解析到原始 U-Net 论文，arXiv ID/URL/PDF URL 不改写。 |
| Paper Intake | 已完成 | 支持 arXiv URL/ID 解析，生成 query plan、metadata 和 workspace。 |
| Asset Collection | 已完成 | 下载 PDF、TeX Source，并尝试解压。 |
| Source Enrichment | 已完成轻量版 | 记录官方论文链接、本地资产状态和用户补充 URL，不抓取正文。 |
| PDF Image Extraction | 已完成轻量版 | 使用 PyMuPDF 提取图片或页面 snapshot，生成 manifest。 |
| Code Linker | 已完成轻量版 | 整理 GitHub 候选 URL，不自动搜索全网，不 clone。 |
| Code Mapping Evidence | 已完成 MVP | 用户提供本地代码目录后，按 Core Method 方法词重合度生成文件级和 Python function/class 级候选映射；不自动 clone，不声明真实实现对应。 |
| Batch Intake | 已完成 MVP | 支持多行论文输入，顺序创建多个 intake jobs，保存 batch JSON 和 Markdown summary；不并发，不做综述总结。 |
| Note Writer | 已完成骨架版 | 生成 `notes/README.md` 结构，不生成深度解释。 |
| Terminology Agent | 已完成证据 MVP | 生成 `notes/terminology.md` 模板，并能优先从 chunks 抽取带 chunk id/page 的术语候选；chunks 缺失时 fallback 到 README 页码证据行；不自动生成完整解释。 |
| Doubts Agent | 已完成证据 MVP | 生成 `notes/doubts.md` 模板，并能优先从 method / experiment / limitation chunks 派生带 chunk id/page 的疑难点候选；chunks 缺失时 fallback 到 README 证据草稿、Deep Q&A 和 terminology first-seen 条目；不生成完整疑难点分析。 |
| Interview Mapper | 已完成评估 MVP | 生成 `notes/interview-project.md`，并基于现有证据输出适配度、最小 demo 范围和风险边界。 |
| Package Validator | 已完成骨架版 | 生成 `notes/package-status.md`，只检查文件存在状态，包括 PDF text evidence map。 |
| PDF Text Evidence Extractor | 已完成轻量版 | 生成 `notes/evidence-map.md`，只保留页码级文本证据。 |
| Evidence Chunker | 已完成 MVP | 读取 `notes/evidence-map.md` 的 Page excerpt，生成 `notes/evidence-chunks.md`，保留 chunk id、page、section guess、字符数和文本 excerpt。 |
| Evidence Retriever | 已完成 MVP | 基于 `notes/evidence-chunks.md` 做本地关键词检索，生成 `notes/evidence-search.md`，返回 chunk id、page、score 和 excerpt。 |
| Deep Note Planner | 已完成骨架版 | 生成 `notes/deep-note-plan.md`，只判断章节准备度，不生成深度正文。 |
| Deep Note Writer | 已完成 MVP | 只写入 ready 的 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways，保留页码/图片证据和人工复查标记。 |
| ai-paper-reader Prompt Pack | 已完成 MVP | 生成 `notes/ai-paper-reader-prompt.md`，要求另一个 Codex 对话读取 `./docs/PAPER_SKILL.md` 和 canonical skill 路径。 |
| ai-paper-reader Note Generation | 已完成 MVP | 配置 LLM 后生成 `notes/ai-paper-reader-note.md`，优先使用 `notes/evidence-chunks.md`，缺失时 fallback 到 `notes/evidence-map.md`，并保存 generation prompt 方便复盘。 |
| Agent timeline 和 artifacts | 已完成基础版 | 每个步骤写入 `AgentStep` 和 `Artifact`。 |
| 真实样例 pipeline | 已完成 | Attention Is All You Need 样例可跑到 Step 21；Step 22/23/24 通过本地单元样例验证，真实第三方仓库读取需用户提供本地路径。 |

## 按文档规划尚未完成的部分

| 规划能力 | 当前缺口 | 为什么未完成 |
| --- | --- | --- |
| 完整深度论文笔记生成 | `notes/README.md` 只有 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways 的保守证据草稿 | 已有 chunk 证据入口，但还没有 chunk-grounded LLM 生成链路、实验深度解释或完整方法推导。 |
| 术语自动解释 | `terminology.md` 只有有页码证据的术语候选 | 当前不生成完整术语解释，也还没有从 chunk evidence 派生术语解释。 |
| 完整疑难点分析 | `doubts.md` 只有证据候选问题 | 当前不解析公式推导、方法细节或代码缺口，只保留可追溯 question seed。 |
| 行级或语义级代码映射 | `code-references.md` 只有文件级和 symbol-level 候选 | 当前只做本地代码目录的确定性词面重合扫描，不做远端读取、clone 或 line-level mapping。 |
| 完整项目方案 | `interview-project.md` 只有适配度评估和最小 demo 边界 | 当前不生成完整项目设计、排期或实现方案。 |
| 外部资料内容抽取 | 只记录 URL | 当前不抓取博客、视频、公众号或教程正文。 |
| 跨论文综述总结 | 未实现 | 当前 batch intake 只创建多个 jobs，不做 related work 或自动综述。 |
| 语义 / 向量检索 | 未实现 | 当前只有确定性关键词检索，没有 embedding 存储或向量数据库。 |
| Agent workflow 可视化增强 | 基础 timeline 已有 | 还没有 plan/git/file-change 可视化。 |
| 自动 clone 仓库 | 明确暂不做 | clone 需要用户确认，避免 scope 和数据体积失控。 |
| FastAPI / React 产品化 | 明确暂不做 | 当前技术路线是 Python + Streamlit。 |

## 当前版本可以怎么介绍

推荐说法：

> 这是一个已经跑通单篇论文 scaffold 研究包和多篇论文 intake batch 的 agentic workflow。它能稳定完成论文识别、资产下载、来源整理、图片提取、代码候选整理、笔记/术语/疑难点/项目映射模板生成、研究包状态检查、PDF 文本证据提取、paragraph / chunk 级证据切分、本地证据检索、深度笔记准备度计划，并把 ready 的 TL;DR / Paper Overview / Background and Motivation / Core Method / Experiments / Limitations / Deep Q&A / Practical Takeaways 写成带页码/图片证据的保守草稿，同时生成带 chunk id/page 的术语候选、疑难点候选、文件级和 Python function/class 级代码映射候选，以及面试项目适配度评估。

不要说：

> 已经能自动深度读懂论文并生成完整研究报告。

更稳的面试表达：

> 当前版本重点展示的是 workflow 拆分、状态管理、产物持久化、失败容错和证据约束写入。完整深度内容生成还没有做，因为我先把可验证的数据管道、scaffold 结构和 evidence gate 跑通，再逐步引入 LLM。

## 是否符合文档规划

分两层看：

- **符合当前阶段文档**：Step 31 的目标已经实现，Batch Runner 已顺序创建多个 intake jobs 并保存 summary。
- **未完成长期规划**：`PROJECT_GUIDE.md`、`WORKFLOW_SPEC.md` 中的完整深度笔记、术语解释、疑难点分析、完整项目方案、语义/向量检索、远端代码读取和行级代码分析还没做。

因此当前状态应标记为：

```text
Stage: Step 31 completed
Completion level: LLM provider config + query planning + scaffold MVP + conservative deep note writing MVP + ai-paper-reader prompt pack + chunk-grounded ai-paper-reader note generation + paragraph / chunk evidence map + local evidence search MVP + chunk-aware terminology evidence MVP + chunk-aware doubts evidence MVP + function-level code mapping evidence MVP + interview project assessment MVP + multi-paper batch intake MVP completed
Full project vision: not completed
```

## 建议下一步

当前核心 MVP 已闭环。扩展路线已单独整理到 `docs/EXTENSION_ROADMAP.md`。

```text
推荐优先级：真实样例验证和 demo 整理
```

当前 Step 26-31 请求清单已完成。下一轮继续加功能前，建议先用真实样例跑 batch intake 和单篇完整 pipeline，整理 demo script / evaluation 文档。

## 剩余路线图

当前核心 MVP 建议阶段已经完成：

| 阶段 | 目标 | 主要产物 |
| --- | --- | --- |
| Step 23 | Interview Project Mapping Assessment MVP | 已完成，更新 `notes/interview-project.md`，输出项目适配度判断 |
| Step 24 | LLM Query Planner 与 ai-paper-reader Prompt Pack | 已完成，生成 `notes/query-plan.md` 和 `notes/ai-paper-reader-prompt.md` |
| Step 25 | LLM Provider Config 与 ai-paper-reader Note Generation | 已完成，生成 `notes/ai-paper-reader-note.md` 和 generation prompt |
| Step 26 | Paragraph / Chunk-level Evidence Map | 已完成，生成 `notes/evidence-chunks.md` |
| Step 27 | RAG / 本地检索 MVP | 已完成，生成 `notes/evidence-search.md` |
| Step 28 | ai-paper-reader Note 使用 Evidence Chunks | 已完成，generation prompt 优先包含 `notes/evidence-chunks.md` |
| Step 29 | Terminology / Doubts 使用 Evidence Chunks | 已完成，术语和疑难点候选优先保留 chunk id/page |
| Step 30 | Code Mapping Function-level MVP | 已完成，本地 Python function/class symbol-level candidates |
| Step 31 | 多篇论文批处理 MVP | 已完成，多行输入顺序创建多个 intake jobs |

远端仓库读取或 clone 仍然需要用户再次确认。语义/向量检索、line-level code mapping、跨论文综述总结和前后端产品化属于后续扩展路线图；详见 `docs/EXTENSION_ROADMAP.md`。
