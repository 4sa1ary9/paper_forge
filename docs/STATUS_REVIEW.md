# PaperForge Agent 完成度核对

## 结论

**当前项目已经完成 Step 23 的 scaffold 闭环、PDF 文本证据提取、深度笔记准备度计划、保守版深度笔记写入 MVP、术语证据 MVP、疑难点证据 MVP、代码映射证据 MVP 和面试项目适配度评估 MVP，但还没有完成文档中描述的最终研究包目标。**

最近核对日期：2026-05-24。当前状态是 Step 23 completed；核心 MVP 已闭环，后续建议进入 `docs/EXTENSION_ROADMAP.md`。

更准确的表述是：

> PaperForge Agent 当前已经跑通单篇论文研究包的确定性 workflow、文件产物骨架、PDF 文本证据图、深度笔记 readiness gate、TL;DR / Paper Overview / Background and Motivation / Core Method / Experiments / Limitations / Deep Q&A / Practical Takeaways 的保守证据草稿、带页码证据的术语候选条目、由证据草稿派生的疑难点候选、本地代码目录扫描得到的文件级代码映射候选，以及面试项目适配度评估；但完整深度论文理解、术语自动解释、完整疑难点分析、行级或语义级代码映射、完整项目方案仍然是后续规划。

所以项目不能说“完整完成”。可以说：

> 当前版本完成了可演示、可追踪、可扩展的 scaffold MVP。

## 已按文档完成的部分

| 规划能力 | 当前状态 | 说明 |
| --- | --- | --- |
| Python + Streamlit 本地工作台 | 已完成 | 当前没有继续使用 TypeScript/React/Express。 |
| uv 环境和 pytest 基线 | 已完成 | 当前测试基线为 `48 passed`。 |
| Paper Intake | 已完成 | 支持 arXiv URL/ID 解析，生成 metadata 和 workspace。 |
| Asset Collection | 已完成 | 下载 PDF、TeX Source，并尝试解压。 |
| Source Enrichment | 已完成轻量版 | 记录官方论文链接、本地资产状态和用户补充 URL，不抓取正文。 |
| PDF Image Extraction | 已完成轻量版 | 使用 PyMuPDF 提取图片或页面 snapshot，生成 manifest。 |
| Code Linker | 已完成轻量版 | 整理 GitHub 候选 URL，不自动搜索全网，不 clone。 |
| Code Mapping Evidence | 已完成 MVP | 用户提供本地代码目录后，按 Core Method 方法词重合度生成文件级候选映射；不自动 clone，不声明行级实现映射。 |
| Note Writer | 已完成骨架版 | 生成 `notes/README.md` 结构，不生成深度解释。 |
| Terminology Agent | 已完成证据 MVP | 生成 `notes/terminology.md` 模板，并能从 README 页码证据行抽取有 evidence-map 页码支撑的术语候选；不自动生成完整解释。 |
| Doubts Agent | 已完成证据 MVP | 生成 `notes/doubts.md` 模板，并能从 README 证据草稿、Deep Q&A 和 terminology first-seen 条目派生疑难点候选；不生成完整疑难点分析。 |
| Interview Mapper | 已完成评估 MVP | 生成 `notes/interview-project.md`，并基于现有证据输出适配度、最小 demo 范围和风险边界。 |
| Package Validator | 已完成骨架版 | 生成 `notes/package-status.md`，只检查文件存在状态，包括 PDF text evidence map。 |
| PDF Text Evidence Extractor | 已完成轻量版 | 生成 `notes/evidence-map.md`，只保留页码级文本证据。 |
| Deep Note Planner | 已完成骨架版 | 生成 `notes/deep-note-plan.md`，只判断章节准备度，不生成深度正文。 |
| Deep Note Writer | 已完成 MVP | 只写入 ready 的 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways，保留页码/图片证据和人工复查标记。 |
| Agent timeline 和 artifacts | 已完成基础版 | 每个步骤写入 `AgentStep` 和 `Artifact`。 |
| 真实样例 pipeline | 已完成 | Attention Is All You Need 样例可跑到 Step 21；Step 22/23 通过本地单元样例验证，真实第三方仓库读取需用户提供本地路径。 |

## 按文档规划尚未完成的部分

| 规划能力 | 当前缺口 | 为什么未完成 |
| --- | --- | --- |
| 完整深度论文笔记生成 | `notes/README.md` 只有 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways 的保守证据草稿 | 还没有段落级证据定位、LLM 生成链路、实验深度解释或完整方法推导。 |
| 术语自动解释 | `terminology.md` 只有有页码证据的术语候选 | 当前不生成完整术语解释，也不做段落级术语定义。 |
| 完整疑难点分析 | `doubts.md` 只有证据候选问题 | 当前不解析公式推导、方法细节或代码缺口，只保留可追溯 question seed。 |
| 行级或语义级代码映射 | `code-references.md` 只有文件级候选路径 | 当前只做本地代码目录的确定性词面重合扫描，不做远端读取、clone 或 line-level mapping。 |
| 完整项目方案 | `interview-project.md` 只有适配度评估和最小 demo 边界 | 当前不生成完整项目设计、排期或实现方案。 |
| 外部资料内容抽取 | 只记录 URL | 当前不抓取博客、视频、公众号或教程正文。 |
| 段落级证据和语义 evidence map | 未实现 | 当前只做页码级文本 excerpt，还没有段落切分或语义索引。 |
| RAG / 向量检索 | 未实现 | 当前没有索引、检索器或 embedding 存储。 |
| Agent workflow 可视化增强 | 基础 timeline 已有 | 还没有 plan/git/file-change 可视化。 |
| 自动 clone 仓库 | 明确暂不做 | clone 需要用户确认，避免 scope 和数据体积失控。 |
| 多篇论文批处理 | 未实现 | 当前以单篇论文 job 为主。 |
| FastAPI / React 产品化 | 明确暂不做 | 当前技术路线是 Python + Streamlit。 |

## 当前版本可以怎么介绍

推荐说法：

> 这是一个已经跑通单篇论文 scaffold 研究包的 agentic workflow。它能稳定完成论文识别、资产下载、来源整理、图片提取、代码候选整理、笔记/术语/疑难点/项目映射模板生成、研究包状态检查、PDF 文本证据提取、深度笔记准备度计划，并把 ready 的 TL;DR / Paper Overview / Background and Motivation / Core Method / Experiments / Limitations / Deep Q&A / Practical Takeaways 写成带页码/图片证据的保守草稿，同时生成带页码证据的术语候选、疑难点候选、文件级代码映射候选和面试项目适配度评估。

不要说：

> 已经能自动深度读懂论文并生成完整研究报告。

更稳的面试表达：

> 当前版本重点展示的是 workflow 拆分、状态管理、产物持久化、失败容错和证据约束写入。完整深度内容生成还没有做，因为我先把可验证的数据管道、scaffold 结构和 evidence gate 跑通，再逐步引入 LLM。

## 是否符合文档规划

分两层看：

- **符合当前阶段文档**：Step 23 的目标已经实现，interview project assessment MVP 已验证。
- **未完成长期规划**：`PROJECT_GUIDE.md`、`WORKFLOW_SPEC.md` 中的完整深度笔记、术语解释、疑难点分析、完整项目方案、RAG、远端代码读取和行级代码分析还没做。

因此当前状态应标记为：

```text
Stage: Step 23 completed
Completion level: scaffold MVP + conservative deep note writing MVP + terminology evidence MVP + doubts evidence MVP + code mapping evidence MVP + interview project assessment MVP completed
Full project vision: not completed
```

## 建议下一步

当前核心 MVP 已闭环。扩展路线已单独整理到 `docs/EXTENSION_ROADMAP.md`。

```text
推荐优先级：Extension 0: LLM Query Planner 与 ai-paper-reader Prompt Pack
```

这样可以先修正入口和复用现有阅读笔记 skill：用户输入 `unet` 这类简称时，query planner 应先解析到原始论文；同时生成 `notes/ai-paper-reader-prompt.md`，要求 Codex 读取 `C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md` 后再写专业阅读笔记。

## 剩余路线图

当前核心 MVP 建议阶段已经完成：

| 阶段 | 目标 | 主要产物 |
| --- | --- | --- |
| Step 23 | Interview Project Mapping Assessment MVP | 已完成，更新 `notes/interview-project.md`，输出项目适配度判断 |

远端仓库读取或 clone 仍然需要用户再次确认。LLM Query Planner、ai-paper-reader Prompt Pack、RAG、段落级 evidence map、多篇论文批处理和前后端产品化属于扩展路线图，不计入当前核心 MVP；详见 `docs/EXTENSION_ROADMAP.md`。
