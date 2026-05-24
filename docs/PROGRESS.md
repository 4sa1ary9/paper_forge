# PaperForge Agent 项目进度

## 当前阶段

**阶段：Step 23，Interview Project Mapping Assessment MVP 已完成。**

最近文档刷新：2026-05-24。Step 23 已完成核心 MVP 闭环；扩展路线已整理到 `docs/EXTENSION_ROADMAP.md`。根据最新需求，下一步优先建议做 LLM Query Planner 与 ai-paper-reader Prompt Pack，然后再做段落级 evidence map。

当前项目已经从 TypeScript/React/Express 调整为 **Python + Streamlit**。

## 完成度结论

当前项目已经完成 **Step 23 scaffold MVP + conservative deep note writing MVP + terminology evidence MVP + doubts evidence MVP + code mapping evidence MVP + interview project assessment MVP**，但还没有完成文档中描述的最终研究包目标。

- 已完成：单篇论文从 intake 到 PDF text evidence extraction + deep note planning + conservative deep note writing + terminology evidence writing + doubts evidence writing + code mapping evidence writing + interview project assessment 的确定性 workflow，包含 metadata、PDF/TeX 资产、外部来源记录、图片 manifest、代码候选、笔记/术语/疑难点/面试项目模板、研究包状态报告、PDF 文本证据图、深度笔记准备计划，以及带页码/图片证据的 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways 保守草稿、术语候选条目、疑难点证据草稿、文件级代码映射候选和面试项目适配度评估。
- 未完成：完整深度论文笔记生成、术语自动解释、完整疑难点分析、行级或语义级代码映射、完整项目方案生成、RAG、自动 clone、多篇论文批处理。
- 详细核对见：`docs/STATUS_REVIEW.md`。

## 当前技术栈

- Python 3.13.5
- uv
- Streamlit
- PyMuPDF
- pytest
- 本地文件系统

本地环境使用 uv。虚拟环境目录是 `.venv/`，激活后显示 `(agent)`。

```powershell
uv venv --prompt agent .venv
uv sync
```

常用命令：

```powershell
uv run streamlit run app.py
uv run python -m pytest
```

## 已完成

- 项目名称确定为 **PaperForge Agent**。
- 项目需求确定为“AI 论文研究与面试项目孵化助手”。
- 已创建基础文档：
  - `README.md`
  - `docs/PROJECT_GUIDE.md`
  - `docs/WORKFLOW_SPEC.md`
  - `docs/EXTENSION_ROADMAP.md`
  - `docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md`
  - `docs/PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md`
  - `docs/DOCUMENTATION_GUIDE.md`
  - `docs/BUILD_STEPS.md`
  - `docs/PROGRESS.md`
- 已移除旧的 TypeScript/React/Express 工程。
- 已创建 Python 项目结构：
  - `app.py`
  - `paperforge/`
  - `tests/`
- 已配置 uv 项目环境：
  - `pyproject.toml`
  - `.python-version`
  - `uv.lock`
  - 本地环境目录：`.venv/`
  - 激活提示名：`agent`
- 已实现 Paper Intake Agent 最小闭环：
  - 输入论文标题、arXiv ID 或 URL；
  - 解析 arXiv 元信息；
  - 创建 `ResearchJob`；
  - 创建 `.paperforge-data/paper-vault/<paper-slug>/`；
  - 写入 `metadata.json`；
  - 写入 `notes/external-sources.md`；
  - Streamlit 展示 timeline 和 artifacts。
- 已实现 Asset Collector Agent：
  - 根据 `metadata.pdf_url` 下载 `raw/paper.pdf`；
  - 根据 `metadata.source_url` 下载 `raw/source.tar.gz`；
  - 尝试解压到 `raw/tex-source/`；
  - 不覆盖已有资产文件；
  - 将 PDF、TeX Source archive 和解压目录写入 artifacts；
  - 将下载和解压过程写入 agent timeline。
- Streamlit 工作台已增加 `Collect Assets` 按钮，可对已有 intake job 执行资产收集。
- 已实现 Source Enrichment Agent：
  - 更新 `notes/external-sources.md`；
  - 记录 canonical paper、PDF URL、TeX Source URL；
  - 记录本地 PDF 和 TeX Source 资产状态；
  - 支持用户手动输入外部资料 URL；
  - TeX Source 缺失时明确保留 PDF-based processing 路径；
  - 将 source enrichment 写入 agent timeline 和 artifacts。
- Streamlit 工作台已增加 `Enrich Sources` 按钮，可对已有 job 整理外部资料。
- 已实现 PDF Image Extractor Agent：
  - 从 `raw/paper.pdf` 提取 PDF 内嵌图片；
  - 图片输出到 `.paperforge-data/paper-vault/<paper-slug>/images/`；
  - 生成 `images/manifest.md`；
  - 将图片和 manifest 写入 artifacts；
  - 缺少 PDF 时跳过并写入 timeline，不影响已有 metadata 和 source log；
  - 没有可用内嵌图片时渲染前几页作为 fallback。
- Streamlit 工作台已增加 `Extract PDF Images` 按钮，可预览提取出的图片。
- 已新增真实流水线脚本 `scripts/run_pipeline.py`：
  - intake；
  - asset collection；
  - PDF image extraction。
- 已实现 Code Linker Agent 轻量版：
  - 从 `metadata.github_candidates` 读取候选仓库；
  - 从 `notes/external-sources.md` 提取 GitHub URL；
  - 生成 `notes/code-references.md`；
  - 记录 clone decision 为 `not cloned`；
  - 不自动 clone 仓库，不做大范围 GitHub 搜索；
  - 将 `code.link_repositories` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Link Code Candidates` 按钮。
- 已实现 Note Writer Agent 骨架版：
  - 生成 `notes/README.md`；
  - 写入论文元信息；
  - 写入主笔记章节结构；
  - 引用 external source log、image manifest 和 code references；
  - 明确标注 scaffold only，不生成未经验证的深度解释；
  - 将 `note.write_readme` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Note Scaffold` 按钮。
- 已实现 Terminology Agent 骨架版：
  - 生成 `notes/terminology.md`；
  - 写入论文标题和来源 note；
  - 写入标准术语条目字段；
  - 明确标注 scaffold only，不自动抽取术语；
  - 将 `knowledge.write_terminology` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Terminology Scaffold` 按钮。
- 已实现 Terminology Evidence MVP：
  - 读取 `notes/evidence-map.md`、`notes/README.md` 和 `notes/terminology.md`；
  - 只从 README 中带 `Page N ... evidence` 的保守证据行抽取术语候选；
  - 使用 `notes/evidence-map.md` 校验页码存在，避免写入没有页码证据的术语；
  - 写入 `notes/terminology.md`，保留术语来源章节、first seen page 和人工复查标记；
  - 明确标注 terminology evidence MVP，不生成完整术语解释；
  - 将 `knowledge.write_terminology_evidence` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Terminology Evidence` 按钮。
- 已实现 Doubts Agent 骨架版：
  - 生成 `notes/doubts.md`；
  - 写入论文标题和来源 note；
  - 写入推荐疑难点章节；
  - 明确标注 scaffold only，不自动编造问题；
  - 将 `knowledge.write_doubts` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Doubts Scaffold` 按钮。
- 已实现 Doubts Evidence MVP：
  - 读取 `notes/README.md`、`notes/terminology.md` 和 `notes/doubts.md`；
  - 从 Core Method、Experiments、Limitations、Deep Q&A 和术语 first-seen 条目派生疑难点候选；
  - 写入来源章节、page evidence 和人工复查标记；
  - 不泛泛生成开放问题，不把候选问题包装成最终疑难点分析；
  - 将 `knowledge.write_doubts_evidence` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Doubts Evidence` 按钮。
- 已实现 Code Mapping Evidence MVP：
  - 读取 `notes/code-references.md` 和 `notes/README.md`；
  - 只在用户提供本地代码仓库路径时扫描代码文件；
  - 不自动 clone、不读取远端仓库、不把候选路径包装成确定实现；
  - 从 `notes/README.md` 的 Core Method 章节提取方法证据词；
  - 在本地代码目录中扫描常见代码文件，按方法词重合度生成候选代码路径；
  - 更新 `notes/code-references.md` 的 `Code Mapping Evidence` 章节；
  - 缺少本地代码路径时将 `code.map_evidence` 标记为 `needs_user_input`；
  - 将 `code.map_evidence` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Code Mapping Evidence` 按钮，并要求输入本地代码仓库路径。
- 已实现 Interview Mapper Agent 骨架版：
  - 生成 `notes/interview-project.md`；
  - 写入论文标题、来源 note 和代码引用入口；
  - 写入推荐面试项目映射章节；
  - 明确标注 scaffold only，不自动判断适配度；
  - 将 `project.write_interview_mapping` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Interview Mapping Scaffold` 按钮。
- 已实现 Interview Project Mapping Assessment MVP：
  - 读取 `notes/README.md`、`notes/code-references.md`、`notes/doubts.md` 和 `notes/interview-project.md`；
  - 基于方法证据、实验/实践证据、本地代码映射和风险信号输出 high / medium / low / not recommended；
  - 写入最小 demo 范围、技术亮点、风险、已有代码关联和面试讲述点；
  - 明确标注 interview assessment MVP，不生成完整项目方案；
  - 缺少输入时将 `project.assess_interview_mapping` 标记为 `partial`；
  - 将 `project.assess_interview_mapping` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Assess Interview Project` 按钮。
- 已实现 Research Package Validator Agent 骨架版：
  - 生成 `notes/package-status.md`；
  - 检查 `metadata.json`、PDF、图片 manifest、PDF text evidence map 和 notes 产物是否存在；
  - 区分 required、recommended 和 optional 产物；
  - PDF 和图片 manifest 缺失记录为 warning；
  - TeX Source 缺失记录为 optional missing，不阻塞 PDF-based processing；
  - 只检查文件存在状态，不判断内容质量、论文理解深度或项目适配度；
  - 将 `package.validate_research_package` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Validate Research Package` 按钮。
- 已实现 PDF Text Evidence Extractor Agent：
  - 生成 `notes/evidence-map.md`；
  - 使用 PyMuPDF 从 `raw/paper.pdf` 提取分页文本；
  - 记录页码、字符数和每页文本 excerpt；
  - 明确标注 raw text evidence only，不总结、不解释；
  - 缺少 PDF 时仍写 partial report，保留 timeline 和 artifact；
  - 将 `pdf.extract_text_evidence` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Extract PDF Text Evidence` 按钮。
- 已实现 Deep Note Planner / Readiness Gate：
  - 生成 `notes/deep-note-plan.md`；
  - 读取 `notes/package-status.md`、`notes/README.md`、PDF、`notes/evidence-map.md`、图片 manifest、外部来源记录和代码引用文件的存在状态；
  - 标记 TL;DR、Paper Overview、Background and Motivation、Core Method、Code Mapping、Experiments、Deep Q&A、Limitations 和 Practical Takeaways 的准备度；
  - 明确标注 readiness gate only，不生成深度解释；
  - 缺少 required 或 recommended 输入时将 step 标记为 `partial`；
  - 将 `note.plan_deep_note` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Plan Deep Note Readiness` 按钮。
- 已实现 Deep Note Writer MVP：
  - 读取 `notes/deep-note-plan.md`、`notes/evidence-map.md` 和 `notes/README.md`；
  - 只处理 readiness table 中标记为 ready 的目标章节；
  - 当前只写入 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways，不一次性生成完整深度报告；
  - 写入 evidence-grounded draft，引用 `notes/evidence-map.md` 页码；
  - Core Method 和 Experiments 额外读取 `images/manifest.md`，保留 figure/table evidence 入口；
  - 将主笔记 Draft status 更新为 conservative deep note MVP；
  - 明确保留 needs human review 标记；
  - 跳过明显版权/授权声明页，避免把 PDF boilerplate 当作论文内容；
  - Background and Motivation 优先选择 introduction、motivation、background 证据页，并避开明显图注页；
  - Core Method 优先选择 method、model、architecture、attention 等方法证据页，并在 manifest 缺失时返回 partial、不改写 README；
  - Experiments 优先选择 experiment、evaluation、benchmark、result、ablation、table 等实验证据页，并单独列出 table/result evidence 和 training detail evidence；
  - Limitations 优先选择 limitation、future work、failure、constraint、risk 等限制/风险证据页，不需要图片 manifest；
  - Deep Q&A 从已写入的 Core Method、Experiments、Limitations 证据草稿派生问题，保留来源章节和页码；
  - Practical Takeaways 从已写入的 Core Method、Experiments、Limitations、Deep Q&A 证据草稿派生学习型 takeaway，保留来源章节和页码，不生成项目建议；
  - 将 `note.write_deep_note_mvp` 写入 timeline 和 artifacts。
- Streamlit 工作台已增加 `Write Deep Note MVP` 按钮。

## 当前验证状态

Python 版本已验证通过：

- 已配置 uv 项目环境；
- 已创建 `.venv` 虚拟环境；
- 激活提示名为 `agent`；
- 已生成 `uv.lock`；
- 执行 `uv run python -m pytest` 通过：48 passed；
- 执行 `uv run python -m compileall app.py paperforge tests scripts` 通过；
- 执行 `git diff --check` 通过；
- 真实 intake + asset collection + source enrichment 通过：
  - 输入：`https://arxiv.org/abs/1706.03762`
  - 输出：`attention-is-all-you-need`
  - 状态：`completed`
  - PDF：`paper-vault/attention-is-all-you-need/raw/paper.pdf`
  - TeX Source：`paper-vault/attention-is-all-you-need/raw/source.tar.gz`
  - 解压目录：`paper-vault/attention-is-all-you-need/raw/tex-source`
  - 外部来源记录：`paper-vault/attention-is-all-you-need/notes/external-sources.md`
- 真实 pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py`
  - 输入：`https://arxiv.org/abs/2006.11239`
  - 输出：`denoising-diffusion-probabilistic-models`
  - 状态：`completed`
  - 图片：22 个图片文件；
  - manifest：`paper-vault/denoising-diffusion-probabilistic-models/images/manifest.md`
- 真实 code linking 通过：
  - 输入：`https://arxiv.org/abs/1706.03762`
  - 外部 GitHub URL：`https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/code-references.md`
  - 状态：`completed`
- 真实 note scaffold pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/README.md`
  - 状态：`completed`
- 真实 terminology scaffold pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/terminology.md`
  - 状态：`completed`
- 真实 terminology evidence pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/terminology.md`
  - 状态：`completed`
  - 行为：只从 README 的页码证据行抽取术语候选，并写入 first seen page、来源章节和人工复查标记。
- 真实 doubts scaffold pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/doubts.md`
  - 状态：`completed`
- 真实 doubts evidence pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/doubts.md`
  - 状态：`completed`
  - 行为：从 README 的方法、实验、限制、Deep Q&A 证据草稿和 terminology first-seen 条目派生疑难点候选，并写入来源章节、page evidence 和人工复查标记。
- 本地 code mapping evidence 单元样例通过：
  - 命令：`uv run python -m pytest tests/test_code_linker.py`
  - 输出：`paper-vault/sample-paper/notes/code-references.md`
  - 状态：`completed`
  - 行为：在用户提供本地代码目录时，按 Core Method 方法词重合度生成候选代码路径；缺少本地目录时返回 `needs_user_input`，不自动 clone。
- 本地 interview project assessment 单元样例通过：
  - 命令：`uv run python -m pytest tests/test_interview_mapper.py`
  - 输出：`paper-vault/sample-paper/notes/interview-project.md`
  - 状态：`completed`
  - 行为：基于主笔记、代码映射和疑难点信号输出适配度、最小 demo 范围和风险；缺少输入时返回 `partial`。
- 真实 interview mapping scaffold pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/interview-project.md`
  - 状态：`completed`
- 真实 package validation pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/package-status.md`
  - 状态：`completed`
- 真实 PDF text evidence pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/evidence-map.md`
  - 状态：`completed`
- 真实 deep note planning pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/deep-note-plan.md`
  - 状态：`completed`
- 真实 deep note writing MVP pipeline 通过：
  - 命令：`uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer`
  - 输出：`paper-vault/attention-is-all-you-need/notes/README.md`
  - 状态：`completed`
  - 行为：ready 的 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways 写入 evidence-grounded draft；TL;DR、Paper Overview、Background and Motivation、Limitations 引用 `notes/evidence-map.md` 页码，Core Method 同时引用 `images/manifest.md` figure evidence，Experiments 同时引用 table/result、training detail 和 figure/table evidence，Deep Q&A 引用来源章节和页码，Practical Takeaways 引用来源章节和页码并保留学习型 takeaway。
  - Attention 真实样例中，Experiments 引用了 page 6 和 page 8 的表格/结果证据，并引用 `images/manifest.md` 中的 figure/table evidence。
  - Attention 真实样例中，Limitations 引用了 page 2 和 page 7 的限制/约束证据。
  - Attention 真实样例中，Deep Q&A 生成了 3 个来源问题，分别引用 Core Method page 2、Experiments page 6、Limitations page 2。
  - Attention 真实样例中，Practical Takeaways 从 Core Method、Experiments、Limitations、Deep Q&A 派生学习型 takeaway，不生成项目建议或适配度判断。
- Streamlit 已启动：
  - URL：`http://localhost:8501`
  - HTTP 状态：200

验证时修复过五个问题：

- arXiv API 返回 HTTP 429：已给请求添加 User-Agent。
- 旧 TypeScript 版本留下的 job 文件是 camelCase：Python 版读取逻辑已兼容。
- Deep Note Writer 初版会使用 PDF 版权/授权页作为 TL;DR 证据：已增加 boilerplate page 过滤和回归测试。
- Deep Note Writer 章节替换会把反斜杠证据文本当成 regex replacement 转义：已改为函数式 replacement 并增加回归测试。
- Deep Note Writer Background 初版会把图注页当成 motivation evidence：已增加背景页筛选和回归测试。
- Deep Note Writer Core Method 需要图片 manifest 支撑：已增加 manifest 缺失保护和回归测试，缺失时返回 partial 且不改写主笔记。
- Deep Note Writer Experiments 需要区分实验正文、表格/结果和训练细节：已增加实验页筛选和回归测试。
- Deep Note Writer Limitations 需要避免 substring 误判：已增加词边界筛选和回归测试，避免把 `unlimited` 当成 limitation evidence。
- Deep Note Writer Deep Q&A 不能直接从 PDF 泛泛生成问题：已改为从 Core Method、Experiments、Limitations 的证据草稿派生问题，并保留来源章节和页码。
- Deep Note Writer Practical Takeaways 不能直接生成项目建议：已改为从 Core Method、Experiments、Limitations、Deep Q&A 的证据草稿派生学习型 takeaway，并保留来源章节、页码和人工复查标记。
- Terminology Evidence 不能从标题或摘要机械列词：已改为只从 README 页码证据行抽取术语候选，并用 evidence-map 校验页码。
- Terminology Evidence 初版会把句子碎片当成术语：已收紧短语抽取规则，避免 `Introduction Recurrent`、`per-layer complexity and` 这类候选。
- Doubts Evidence 不能泛泛生成开放问题：已改为只从 README 证据草稿、Deep Q&A 已生成问题和 terminology first-seen 条目派生疑难点候选。
- Doubts Evidence 初版会把所有 Deep Q&A 来源都标成 `Method question`：已按来源章节区分 Method、Experiment 和 Limitation question，并增加回归测试。

## 下一步

Step 23 已跑通。当前核心 MVP 已闭环。扩展路线图已单独整理到 `docs/EXTENSION_ROADMAP.md`。最新需求已经拆成独立变更设计和实现提示词：

```text
docs/EXTENSION_ROADMAP.md
docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md
docs/PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md
```

最推荐的下一步是 **Extension 0: LLM Query Planner 与 ai-paper-reader Prompt Pack**。原因是它先解决两个实际 workflow 断点：

- 用户输入简称时容易找错论文，例如 `unet` 应优先解析到原始 U-Net 论文；
- 现有 `ai-paper-reader` skill 需要被纳入 PaperForge 产物链，第一版用 `notes/ai-paper-reader-prompt.md` 让另一个 Codex 对话稳定读取并使用：
  `C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md`

完成 Extension 0 后，再做 **Extension 1: 段落级 Evidence Map**。它能把当前页码级证据细化到 paragraph / chunk 级，是后续 RAG、深度解释、术语解释和疑难点分析的基础。

完整深度论文解释、远端仓库自动 clone、完整项目方案生成仍然不建议直接展开。

核心 MVP 路线图：

```text
Step 22: Code Mapping Evidence MVP completed
Step 23: Interview Project Mapping Assessment MVP completed
```

也就是说，当前核心 MVP 建议阶段已经完成。后续如果要读取远端或 clone 第三方仓库，需要再次确认。

扩展路线图暂不计入核心 MVP，详见 `docs/EXTENSION_ROADMAP.md`：

- LLM Query Planner 与 ai-paper-reader Prompt Pack；
- 段落级 evidence map；
- RAG / 向量检索；
- 多篇论文批处理；
- workflow 可视化增强；
- FastAPI / React 产品化迁移。

## 暂不做

- clone 仓库；
- 完整深度论文笔记生成；
- 自动生成完整项目方案；
- FastAPI 后端；
- React 前端。

这些功能等下一轮确认方向后再逐步加。

## 文档更新规则

- 每次开发结束后，更新本文件。
- 如果完成一个完整阶段，同时更新 `docs/BUILD_STEPS.md`。
- 如果改了项目定位或范围，更新 `docs/PROJECT_GUIDE.md`。
- 如果改了 agent 产物或流程，更新 `docs/WORKFLOW_SPEC.md`。

## 面试包装原则

这个项目后续可以说：

> 我做的是一个 AI 论文研究 Agent。它不是简单总结论文，而是把论文研究拆成可追踪的 workflow：论文识别、资产下载、代码关联、资料增强、笔记骨架、术语库、疑难点和面试项目映射。当前 Python 版已经跑通了单篇论文研究包的 scaffold 闭环，并能写入带页码证据的主笔记、术语候选和疑难点候选，后续会逐步扩展到代码方法映射和项目适配度判断。

不要说：

> 我从零手写了一个完整多智能体系统。

更稳的说法是：

> 我用 AI 辅助开发，但需求设计、工作流拆分、产物规范和核心逻辑是我主导理解和迭代的。
