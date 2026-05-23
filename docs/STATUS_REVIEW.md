# PaperForge Agent 完成度核对

## 结论

**当前项目已经完成 Step 13 的 scaffold 闭环、PDF 文本证据提取、深度笔记准备度计划和保守版深度笔记写入 MVP，但还没有完成文档中描述的最终研究包目标。**

更准确的表述是：

> PaperForge Agent 当前已经跑通单篇论文研究包的确定性 workflow、文件产物骨架、PDF 文本证据图、深度笔记 readiness gate 和 TL;DR / Paper Overview 的保守证据草稿；但完整深度论文理解、术语解释、疑难点生成、代码到论文的真实映射、面试项目适配度判断仍然是后续规划。

所以项目不能说“完整完成”。可以说：

> 当前版本完成了可演示、可追踪、可扩展的 scaffold MVP。

## 已按文档完成的部分

| 规划能力 | 当前状态 | 说明 |
| --- | --- | --- |
| Python + Streamlit 本地工作台 | 已完成 | 当前没有继续使用 TypeScript/React/Express。 |
| uv 环境和 pytest 基线 | 已完成 | 当前测试基线为 `29 passed`。 |
| Paper Intake | 已完成 | 支持 arXiv URL/ID 解析，生成 metadata 和 workspace。 |
| Asset Collection | 已完成 | 下载 PDF、TeX Source，并尝试解压。 |
| Source Enrichment | 已完成轻量版 | 记录官方论文链接、本地资产状态和用户补充 URL，不抓取正文。 |
| PDF Image Extraction | 已完成轻量版 | 使用 PyMuPDF 提取图片或页面 snapshot，生成 manifest。 |
| Code Linker | 已完成轻量版 | 整理 GitHub 候选 URL，不自动搜索全网，不 clone。 |
| Note Writer | 已完成骨架版 | 生成 `notes/README.md` 结构，不生成深度解释。 |
| Terminology Agent | 已完成骨架版 | 生成 `notes/terminology.md` 模板，不自动抽取术语。 |
| Doubts Agent | 已完成骨架版 | 生成 `notes/doubts.md` 模板，不自动生成问题。 |
| Interview Mapper | 已完成骨架版 | 生成 `notes/interview-project.md` 模板，不判断适配度。 |
| Package Validator | 已完成骨架版 | 生成 `notes/package-status.md`，只检查文件存在状态，包括 PDF text evidence map。 |
| PDF Text Evidence Extractor | 已完成轻量版 | 生成 `notes/evidence-map.md`，只保留页码级文本证据。 |
| Deep Note Planner | 已完成骨架版 | 生成 `notes/deep-note-plan.md`，只判断章节准备度，不生成深度正文。 |
| Deep Note Writer | 已完成 MVP | 只写入 ready 的 TL;DR 和 Paper Overview，保留页码证据和人工复查标记。 |
| Agent timeline 和 artifacts | 已完成基础版 | 每个步骤写入 `AgentStep` 和 `Artifact`。 |
| 真实样例 pipeline | 已完成 | Attention Is All You Need 样例可跑到 Stage 13。 |

## 按文档规划尚未完成的部分

| 规划能力 | 当前缺口 | 为什么未完成 |
| --- | --- | --- |
| 完整深度论文笔记生成 | `notes/README.md` 只有 TL;DR 和 Paper Overview 的保守证据草稿 | 还没有段落级证据定位、LLM 生成链路、方法/实验深度解释。 |
| 术语自动抽取和解释 | `terminology.md` 仍是模板 | 当前不从论文全文中抽取术语，也不生成解释。 |
| 疑难点自动生成 | `doubts.md` 仍是模板 | 当前不解析公式、方法细节或代码缺口。 |
| 代码到论文方法映射 | `code-references.md` 只记录候选 URL | 当前不 clone 仓库，不分析代码文件。 |
| 面试项目适配度判断 | `interview-project.md` 仍是模板 | 当前不判断 high/medium/low，也不设计 demo。 |
| 外部资料内容抽取 | 只记录 URL | 当前不抓取博客、视频、公众号或教程正文。 |
| 段落级证据和语义 evidence map | 未实现 | 当前只做页码级文本 excerpt，还没有段落切分或语义索引。 |
| RAG / 向量检索 | 未实现 | 当前没有索引、检索器或 embedding 存储。 |
| Agent workflow 可视化增强 | 基础 timeline 已有 | 还没有 plan/git/file-change 可视化。 |
| 自动 clone 仓库 | 明确暂不做 | clone 需要用户确认，避免 scope 和数据体积失控。 |
| 多篇论文批处理 | 未实现 | 当前以单篇论文 job 为主。 |
| FastAPI / React 产品化 | 明确暂不做 | 当前技术路线是 Python + Streamlit。 |

## 当前版本可以怎么介绍

推荐说法：

> 这是一个已经跑通单篇论文 scaffold 研究包的 agentic workflow。它能稳定完成论文识别、资产下载、来源整理、图片提取、代码候选整理、笔记/术语/疑难点/项目映射模板生成、研究包状态检查、PDF 文本证据提取、深度笔记准备度计划，并把 ready 的 TL;DR / Paper Overview 写成带页码证据的保守草稿。

不要说：

> 已经能自动深度读懂论文并生成完整研究报告。

更稳的面试表达：

> 当前版本重点展示的是 workflow 拆分、状态管理、产物持久化、失败容错和证据约束写入。完整深度内容生成还没有做，因为我先把可验证的数据管道、scaffold 结构和 evidence gate 跑通，再逐步引入 LLM。

## 是否符合文档规划

分两层看：

- **符合当前阶段文档**：Step 13 的目标已经实现，测试和真实 pipeline 已验证。
- **未完成长期规划**：`PROJECT_GUIDE.md`、`WORKFLOW_SPEC.md` 中的深度笔记、术语抽取、疑难点生成、面试项目判断、RAG、代码分析还没做。

因此当前状态应标记为：

```text
Stage: Step 13 completed
Completion level: scaffold MVP + conservative deep note writing MVP completed
Full project vision: not completed
```

## 建议下一步

下一步可以继续扩展 Deep Note Writer，但仍然不能生成无证据支撑的完整深度报告：

```text
Step 14: Deep Note Writer Background MVP
```

目标：

- 读取 `notes/deep-note-plan.md` 和 `notes/evidence-map.md`；
- 只填充 ready 的 Background and Motivation；
- 更新 `notes/README.md`；
- 保留页码证据和人工复查标记。

这样可以继续保持项目原则：先引用证据，再做生成内容。
