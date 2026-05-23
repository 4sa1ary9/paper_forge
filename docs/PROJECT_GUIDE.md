# PaperForge Agent 项目指南

## 1. 项目名称

**PaperForge Agent**

Tagline:

> Research-to-project agent for AI papers.

这个名字的含义是：系统不只是“读论文”，而是把论文、源码、教程、术语、疑难点和项目想法这些原始材料锻造成可复用的学习资产和面试项目素材。

## 2. 核心叙事

这个项目的出发点是一个真实的个人需求：

> 我经常学习 AI 论文，但整个流程非常碎片化。找论文资产很慢，社区讲解分散，代码仓库和论文方法不容易对应，最后写出来的笔记也很难复用。于是我做了 PaperForge Agent，用 agent 把论文整理成一个结构化研究包，并进一步判断它是否适合转化成面试项目。

这个叙事比较可信，因为它不是假装 agent 可以一次性理解所有论文，而是把重点放在“重复性研究流程自动化”和“中间产物可追踪”上。

## 3. 目标用户

主要用户：

- 正在学习 AI/LLM/Agent 方向的学生或工程师；
- 正在准备面试，需要把论文学习转化成项目能力；
- 经常需要阅读论文、GitHub 代码、技术博客和社区教程；
- 想沉淀自己的论文笔记库和项目灵感库。

次要用户：

- 维护个人 AI 论文仓库的人；
- 想用统一格式整理论文笔记的人；
- 想把论文和代码实现联系起来理解的人。

## 4. 它为什么是 Agent 项目

PaperForge Agent 不能被包装成普通 ChatGPT 套壳。它的 agent 特征来自完整任务链路：

- 把“研究一篇论文”拆成多个可执行步骤；
- 调用搜索、下载、PDF 解析、TeX 解析、代码检查、文件管理、笔记生成等工具；
- 维护一个有状态的研究任务；
- 记录每一步的输入、输出、失败原因和重试结果；
- 根据情况决定是否 clone GitHub 仓库；
- 保存可复用的结构化产物，而不是只返回聊天文本；
- 为生成内容保留证据来源；
- 用可视化 plan/timeline 防止 agent 跑偏。

面试时可以强调：

> 我没有做一个泛用聊天机器人，而是做了一个能管理论文研究流程的 agentic workflow system。

## 5. 项目范围

### 当前完成度

当前代码已经完成 **单篇论文 scaffold MVP + PDF text evidence map + deep note readiness gate + conservative deep note writing MVP**：

- 可以跑通 intake -> asset collection -> source enrichment -> PDF image extraction -> code linking -> note scaffold -> terminology scaffold -> doubts scaffold -> interview mapping scaffold -> package validation -> PDF text evidence extraction -> deep note planning -> conservative deep note writing；
- 所有产物都能落盘；
- agent timeline 和 artifacts 能记录每一步状态；
- 真实 arXiv 样例已经验证。

但项目还没有完成最终愿景：

- `notes/README.md` 已能写入 TL;DR 和 Paper Overview 的保守证据草稿，但仍不是完整深度论文解释；
- `notes/terminology.md` 仍是术语模板，不是自动抽取和解释结果；
- `notes/doubts.md` 仍是疑难点模板，不是真实阅读疑问；
- `notes/interview-project.md` 仍是项目映射模板，不是适配度判断；
- `notes/package-status.md` 只检查文件是否存在，不评估内容质量。
- `notes/evidence-map.md` 只提供页码级文本证据，不生成解释。
- `notes/deep-note-plan.md` 只判断章节准备度。
- Deep Note Writer MVP 内容必须保留人工复查标记，不应包装成最终深度结论。

所以当前版本适合展示 agent workflow、状态管理、产物规范和失败容错；还不适合宣称已经自动完成深度论文研究。

### MVP 范围内

- 论文元信息识别；
- PDF 下载；
- TeX Source 下载；
- 论文资产重命名和归档；
- PDF 图片提取；
- GitHub 仓库候选发现；
- 可选 clone 仓库到独立代码目录；
- 外部教程链接或用户粘贴文本的整理；
- 深度论文笔记生成；
- 专业术语提取；
- 疑难点提取；
- 面试项目适配度分析；
- agent workflow 可视化。

### MVP 暂不做

- 自动完整抓取微信公众号正文；
- 自动下载 B 站视频；
- 绕过登录、付费墙或反爬机制；
- 自动复现整篇论文；
- 训练大型模型；
- 支持所有学科领域；
- 完全替代人工校对。

这些限制是有意设计的。第一版要能做完、能展示、能解释，而不是做成一个不可控的大杂烩。

## 6. 推荐 MVP

第一版聚焦“单篇论文完整闭环”。

输入：

- 论文标题；
- arXiv URL；
- OpenReview URL；
- PDF URL；
- 可选 GitHub URL；
- 可选社区教程链接；
- 可选用户粘贴的教程文本。

输出：

- 规范化论文目录；
- 论文 PDF；
- TeX Source；
- 关键图片；
- 元信息文件；
- 深度论文笔记；
- 专业术语表；
- 疑难点列表；
- 代码关联说明；
- 面试项目映射报告。

## 7. 推荐目录结构

应用代码、论文资产和第三方代码仓库应该分开。

```text
PaperForge-Agent/
├── README.md
├── app.py
├── docs/
│   ├── PROJECT_GUIDE.md
│   ├── WORKFLOW_SPEC.md
│   ├── DOCUMENTATION_GUIDE.md
│   └── PROGRESS.md
├── paperforge/
│   ├── arxiv_client.py
│   ├── asset_collector.py
│   ├── code_linker.py
│   ├── deep_note_writer.py
│   ├── doubts_agent.py
│   ├── interview_mapper.py
│   ├── intake_agent.py
│   ├── models.py
│   ├── note_writer.py
│   ├── package_validator.py
│   ├── pdf_image_extractor.py
│   ├── source_enrichment.py
│   ├── terminology_agent.py
│   ├── slug.py
│   ├── steps.py
│   └── storage.py
└── tests/

.paperforge-data/
├── jobs/
└── paper-vault/
    └── paper-slug/
        ├── raw/
        │   ├── paper.pdf
        │   ├── source.tar.gz
        │   └── tex-source/
        ├── images/
        ├── notes/
        │   ├── README.md
        │   ├── terminology.md
        │   ├── doubts.md
        │   ├── code-references.md
        │   ├── interview-project.md
        │   └── package-status.md
        └── metadata.json

code-vault/
└── repo-owner__repo-name/
```

面试解释：

- `app.py` 是本地工作台入口，相当于产品界面。
- `paperforge/` 是核心 agent 代码。
- `paperforge/intake_agent.py` 是当前最重要的 agent workflow。
- `paperforge/asset_collector.py` 负责下载 PDF 和 TeX Source，并尝试解压源码。
- `paperforge/code_linker.py` 负责整理 GitHub 候选仓库并生成代码引用说明。
- `paperforge/deep_note_writer.py` 负责把 ready 章节的保守证据草稿写入主笔记。
- `paperforge/doubts_agent.py` 负责生成疑难点骨架。
- `paperforge/interview_mapper.py` 负责生成面试项目映射骨架。
- `paperforge/note_writer.py` 负责生成 `notes/README.md` 的结构化笔记骨架。
- `paperforge/package_validator.py` 负责生成研究包状态检查报告。
- `paperforge/pdf_image_extractor.py` 负责从 PDF 提取图片和生成图片 manifest。
- `paperforge/source_enrichment.py` 负责整理外部资料来源和本地资产状态。
- `paperforge/terminology_agent.py` 负责生成术语库骨架。
- `.paperforge-data/` 是 agent 运行后生成的研究资产。
- `docs/PROGRESS.md` 记录项目做到哪一步，方便后续接着开发。

## 8. 技术栈选择

当前项目使用 **Python + Streamlit**，不使用 TypeScript/React/Express。

原因：

- 学习成本更低；
- 你可以重点理解 agent workflow，而不是同时学习前端框架和后端框架；
- Python 更贴合 AI/Agent 项目的面试语境；
- Streamlit 足够做本地可视化 demo；
- 后续如果需要更强工程感，可以再把核心逻辑迁移到 FastAPI。

## 9. 论文产物目录规范

```text
.paperforge-data/paper-vault/
└── paper-slug/
    ├── raw/
    │   ├── paper.pdf
    │   ├── source.tar.gz
    │   └── tex-source/
    ├── images/
    ├── notes/
    │   ├── README.md
    │   ├── terminology.md
    │   ├── doubts.md
    │   ├── code-references.md
    │   ├── interview-project.md
    │   └── package-status.md
    └── metadata.json

code-vault/
└── repo-owner__repo-name/
```

说明：

- `PaperForge-Agent/` 存放应用代码。
- `.paperforge-data/paper-vault/` 存放论文、图片、笔记和研究产物。
- `code-vault/` 存放 clone 下来的第三方代码仓库。
- 大 PDF 和第三方仓库不应该直接塞进应用代码仓库。

## 10. Agent 模块划分

### Paper Intake Agent

负责把用户输入转换成标准论文身份。

需要识别：

- 标题；
- 作者；
- 会议或期刊；
- 年份；
- arXiv ID 或 OpenReview ID；
- canonical URL；
- PDF URL；
- 摘要；
- paper slug。

### Asset Collector Agent

负责下载和整理原始资产。

需要处理：

- PDF；
- TeX Source；
- 补充材料；
- bibliography 文件；
- PDF 中的关键图片。

### Source Enrichment Agent

负责收集外部解释资料。

支持来源：

- Hugging Face Papers；
- GitHub 仓库候选；
- 官方项目页；
- 用户提供的教程链接；
- 用户粘贴的公众号、知乎、CSDN、B 站文本或摘要。

对于需要登录或反爬的平台，MVP 不强行爬取正文，先支持用户手动提供内容。

### Code Linker Agent

负责判断论文是否需要结合代码理解，以及是否需要 clone 仓库。

输出内容：

- 仓库摘要；
- 核心文件列表；
- 论文方法到代码文件的映射；
- 是否建议 clone；
- 复现难度；
- 推荐优先阅读的代码路径。

### Note Writer Agent

负责生成主论文笔记。

笔记风格参考现有 `ai-paper-reader` 规范，重点包括：

- 元信息；
- TL;DR；
- 背景和动机；
- 核心方法；
- 公式解释；
- 图表解释；
- 代码片段；
- 实验分析；
- 深度 Q&A；
- 局限性和适用场景。

### Knowledge Curator Agent

负责提取可复用学习资产。

输出内容：

- 专业术语；
- 前置知识；
- 易混淆概念；
- 疑难点；
- 后续问题；
- 相关论文。

### Interview Mapper Agent

负责把论文研究转化成面试项目判断。

需要回答：

- 这篇论文适不适合做面试项目？
- 最小可展示版本是什么？
- 完整版本可以做到什么程度？
- 能和已有项目如何串联？
- 面试时能讲哪些技术深度？
- 需要规避哪些实现风险？

### Research Package Validator Agent

负责检查单篇论文研究包的文件产物是否齐全。

输出内容：

- required 产物状态；
- recommended 产物 warning；
- optional 产物缺失记录；
- `notes/package-status.md` 状态报告；
- `notes/evidence-map.md` recommended 状态；
- timeline 和 artifact 记录。

### Deep Note Planner Agent

负责在深度笔记生成之前做 readiness gate。

输出内容：

- `notes/deep-note-plan.md`；
- readiness input table；
- 主笔记章节的 ready / blocked / review-ready 状态；
- 缺失输入清单；
- 建议的后续生成顺序。

### Deep Note Writer Agent

负责把准备度为 ready 的主笔记章节写入 `notes/README.md`。

当前 MVP 输出内容：

- 只处理 TL;DR 和 Paper Overview；
- 引用 `notes/evidence-map.md` 中的页码证据；
- 将主笔记 Draft status 更新为 conservative deep note MVP；
- 明确标注 needs human review；
- 不生成 Core Method、Experiments、Deep Q&A 或 Practical Takeaways；
- 不把 evidence excerpt 包装成最终深度结论。

### PDF Text Evidence Extractor Agent

负责从 PDF 提取可引用的页码级文本证据。

输出内容：

- `notes/evidence-map.md`；
- page inventory；
- 每页 text excerpt；
- PDF 缺失或无可抽取文本时的 partial report；
- timeline 和 artifact 记录。

## 11. 产品界面形态

界面应该是工作台，不是宣传落地页。当前用 Streamlit 实现，后续如果要做更正式的网页，再考虑迁移。

推荐页面：

- **Research Jobs**：论文研究任务列表和状态。
- **Paper Workspace**：单篇论文的资产、笔记、代码关联和项目映射。
- **Agent Timeline**：当前 plan、已完成步骤、失败步骤和用户干预点。
- **Knowledge Base**：术语、疑难点、可复用概念。
- **Project Candidates**：从论文生成的面试项目候选。

## 12. 代码组织形态

当前不单独做后端服务，而是把核心逻辑放在 `paperforge/` 包里。这样你可以先理解 Python 模块和 agent workflow。

核心模块：

- `models.py`：定义数据结构。
- `arxiv_client.py`：负责论文搜索和元信息解析。
- `asset_collector.py`：负责下载 PDF、TeX Source，并尝试解压源码。
- `code_linker.py`：负责从 metadata 和 external sources 整理 GitHub 候选仓库。
- `deep_note_planner.py`：负责生成深度笔记准备度计划，不做深度解释。
- `deep_note_writer.py`：负责把 ready 章节的保守证据草稿写入 `notes/README.md`，不生成完整深度报告。
- `doubts_agent.py`：负责生成 `notes/doubts.md` 的结构化模板。
- `interview_mapper.py`：负责生成 `notes/interview-project.md` 的结构化模板。
- `intake_agent.py`：负责 intake 工作流。
- `note_writer.py`：负责生成主论文笔记骨架，不做未经验证的深度解释。
- `pdf_image_extractor.py`：负责从 `raw/paper.pdf` 提取图片并生成 `images/manifest.md`。
- `pdf_text_extractor.py`：负责从 `raw/paper.pdf` 提取分页文本并生成 `notes/evidence-map.md`。
- `source_enrichment.py`：负责整理外部资料 URL、本地 PDF/TeX 状态和来源可靠性标签。
- `terminology_agent.py`：负责生成 `notes/terminology.md` 的结构化模板。
- `storage.py`：负责保存和读取本地文件。
- `steps.py`：负责 timeline 状态流转。

后续如果需要 API 服务，可以把这些模块接到 FastAPI 上，不需要重写业务逻辑。

## 13. 数据模型

核心实体：

- `Paper`
- `ResearchJob`
- `AgentStep`
- `Artifact`
- `ExternalSource`
- `RepositoryCandidate`
- `Note`
- `Term`
- `Doubt`
- `ProjectMapping`

任务模型很重要，因为这个系统经常会出现部分成功。例如 PDF 下载成功，但 TeX Source 找不到；GitHub 仓库找到多个，但不确定哪个是官方实现。系统应该保留这些状态，而不是把整个任务判定为失败。

## 14. 面试价值

这个项目可以展示：

- agent planning；
- tool calling；
- RAG over paper assets；
- 文件系统编排；
- PDF 解析和图片提取；
- 代码仓库分析；
- 任务状态机；
- Python 工程组织；
- 本地工作台产品设计；
- 数据建模；
- 失败重试和可观测性；
- prompt/output evaluation。

面试时最强的表达是：

> 我做的不是通用聊天机器人，而是一个研究工作流系统。Agent 会围绕论文、代码、社区资料和项目规划生成一组可追踪、可复用的结构化产物。

当前版本的诚实边界：

> 当前版本已经跑通 scaffold 研究包闭环、PDF 文本证据提取、深度笔记准备度计划和保守版 TL;DR / Paper Overview 写入，但完整深度论文内容生成和项目适配度判断还没有实现。这个边界是有意保留的，因为系统先要保证输入资产、状态流转、产物落盘、质量门槛和证据准备度可靠。

## 15. 开发原则

- 先完成一篇论文的完整闭环，再扩展多来源和批量处理。
- 每个 agent 步骤都要有明确输入、输出和状态。
- 所有生成内容都应该尽量落盘或入库。
- 笔记中的关键结论要能追溯到论文、图表、公式、外部资料或代码文件。
- clone 大仓库前应请求用户确认。
- 生成笔记必须可编辑。
- agent timeline 必须可见。
- 失败步骤要显式记录，不要静默吞掉。
- 不确定内容要标注，不要伪装成确定结论。
