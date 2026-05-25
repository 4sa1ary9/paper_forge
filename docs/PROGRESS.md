# PaperForge Agent 项目进度

## 当前阶段

**阶段：Step 28，ai-paper-reader Note 使用 Evidence Chunks 已完成。**

最近文档刷新：2026-05-25。Step 23 已完成核心 MVP 闭环；Step 24 已完成 Extension 0；Step 25 已完成 OpenAI-compatible LLM 执行层和 ai-paper-reader 自动笔记生成；Step 26 已完成 paragraph / chunk 级 evidence map；Step 27 已完成基于 evidence chunks 的本地关键词检索 MVP；Step 28 已让 ai-paper-reader note generation 优先使用 evidence chunks。下一步优先建议让 terminology / doubts 使用 evidence chunks。

当前项目已经从 TypeScript/React/Express 调整为 **Python + Streamlit**。

## 完成度结论

当前项目已经完成 **Step 28 LLM provider config + query planning + scaffold MVP + conservative deep note writing MVP + ai-paper-reader prompt pack + chunk-grounded ai-paper-reader note generation + paragraph / chunk evidence map + local evidence search MVP + terminology evidence MVP + doubts evidence MVP + code mapping evidence MVP + interview project assessment MVP**，但还没有完成文档中描述的最终研究包目标。

- 已完成：单篇论文从 LLM query planning + intake 到 PDF text evidence extraction + paragraph / chunk evidence extraction + local evidence search + deep note planning + conservative deep note writing + ai-paper-reader prompt pack + chunk-grounded ai-paper-reader note generation + terminology evidence writing + doubts evidence writing + code mapping evidence writing + interview project assessment 的 workflow，包含 query plan、metadata、PDF/TeX 资产、外部来源记录、图片 manifest、代码候选、笔记/术语/疑难点/面试项目模板、研究包状态报告、PDF 文本证据图、paragraph / chunk 级证据文件、本地 evidence search 结果、深度笔记准备计划，以及带页码/图片证据的 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments、Limitations、Deep Q&A、Practical Takeaways 保守草稿、ai-paper-reader handoff prompt、优先引用 chunk evidence 的 LLM ai-paper-reader note、术语候选条目、疑难点证据草稿、文件级代码映射候选和面试项目适配度评估。
- 未完成：完整深度论文笔记生成、术语自动解释、完整疑难点分析、行级或语义级代码映射、完整项目方案生成、语义/向量检索、自动 clone、多篇论文批处理。
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
- 已实现 Evidence Chunker Agent：
  - 新增 `paperforge/evidence_chunker.py`；
  - 第一版读取 `notes/evidence-map.md` 的 Page excerpt，不重新解析 PDF；
  - 生成 `notes/evidence-chunks.md`；
  - 按空行和合理长度切分 paragraph / chunk；
  - 每个 chunk 写入 stable chunk id、page、section guess、字符数和文本 excerpt；
  - section guess 覆盖 introduction、method、experiment 和 limitation 基础关键词；
  - 缺少 evidence-map 或空页时写 partial report，不阻塞 job；
  - 将 `pdf.extract_evidence_chunks` 写入 timeline，artifact label 为 `Evidence chunks`。
- Streamlit 工作台已增加 `Extract Evidence Chunks` 按钮。
- 已实现 Evidence Retriever Agent：
  - 新增 `paperforge/evidence_retriever.py`；
  - 读取用户查询和 `notes/evidence-chunks.md`；
  - 第一版使用确定性关键词匹配 / BM25-like 简单评分，不引入向量数据库；
  - 返回 chunk id、page、section guess、score 和 excerpt；
  - 生成 `notes/evidence-search.md`；
  - 缺少 chunks 文件时写 partial report，不阻塞 job；
  - 空查询时返回 `needs_user_input`；
  - 将 `evidence.search_chunks` 写入 timeline，artifact label 为 `Evidence search results`。
- Streamlit 工作台已增加 `Evidence search query` 输入框和 `Search Evidence Chunks` 按钮。
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
- 已实现 LLM Query Planner：
  - 新增 `paperforge/query_planner.py`；
  - 在 arXiv 查询前生成 canonical title / search query；
  - `unet`、`u-net`、`u net` 稳定解析到原始 U-Net 论文；
  - 记录 author hint `Ronneberger` 和 year hint `2015`；
  - arXiv ID、arXiv URL 和 PDF URL 不交给 LLM 改写；
  - fake LLM 合法 JSON 可生效，坏 JSON、空响应或异常 fallback；
  - 写入 `notes/query-plan.md`；
  - 将 `query.plan_paper_identity` 写入 timeline。
- Streamlit intake 区域已增加 `Use LLM query planner` 复选框。
- 已实现 ai-paper-reader Prompt Pack：
  - 新增 `paperforge/ai_paper_reader_prompt.py`；
  - 生成 `notes/ai-paper-reader-prompt.md`；
  - Prompt 明确要求另一个 Codex 对话读取 `./docs/PAPER_SKILL.md`；
  - Prompt 同时记录 canonical skill 路径 `C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md`；
  - Prompt 写入论文工作区、`metadata.json`、`raw/paper.pdf`、`notes/README.md`、`notes/evidence-map.md`、`images/manifest.md`；
  - 缺少 PDF、evidence map 或 image manifest 时仍生成 prompt，并标注 missing；
  - 将 `note.prepare_ai_paper_reader_prompt` 写入 timeline；
  - 将 artifact label 设为 `AI Paper Reader Prompt`。
- Streamlit 工作台已增加 `Prepare ai-paper-reader Prompt` 按钮。
- 已实现 OpenAI-compatible LLM client：
  - 新增 `paperforge/llm_client.py`；
  - 自动读取项目根目录 `.env`；
  - 从 `.env` 或系统环境变量读取 `PAPERFORGE_LLM_BASE_URL`、`PAPERFORGE_LLM_API_KEY`、`PAPERFORGE_QUERY_MODEL`、`PAPERFORGE_READER_MODEL`；
  - query planner 默认使用 `PAPERFORGE_QUERY_MODEL`，当前建议为 `deepseek-v4-flash`；
  - ai-paper-reader note generation 使用 `PAPERFORGE_READER_MODEL`，当前建议为 `deepseek-v4-pro`；
  - `LlmConfig.__repr__` 会隐藏 API key；
  - 不把 API key 写入 job、notes 或 docs。
- 已实现 ai-paper-reader Note Generation：
  - 新增 `paperforge/ai_paper_reader_note.py`；
  - 读取 `docs/PAPER_SKILL.md`、`metadata.json`、`notes/README.md`、`images/manifest.md`，并优先读取 `notes/evidence-chunks.md`；
  - `notes/evidence-chunks.md` 存在时 generation prompt 包含 chunk excerpt 和 chunk id；
  - `notes/evidence-chunks.md` 缺失时 fallback 到 `notes/evidence-map.md`；
  - Prompt 明确要求优先引用 chunk id、无法从 chunk 验证的内容标注为待核查、不得凭模型记忆补全论文细节；
  - 生成 `notes/ai-paper-reader-note.md`；
  - 保存 `notes/ai-paper-reader-generation-prompt.md` 方便复盘；
  - 缺少 LLM 配置时将 step 标记为 `needs_user_input`；
  - 缺少 PDF、evidence map 或 image manifest 时仍可调用 LLM，但 step 标记为 `partial`；
  - 将 `note.generate_ai_paper_reader_note` 写入 timeline；
  - artifact labels 为 `AI Paper Reader Note` 和 `AI Paper Reader Generation Prompt`。
- Streamlit 工作台已增加 `Generate ai-paper-reader Note` 按钮。

## 当前验证状态

Python 版本已验证通过：

- 已配置 uv 项目环境；
- 已创建 `.venv` 虚拟环境；
- 激活提示名为 `agent`；
- 已生成 `uv.lock`；
- 执行 `uv run python -m pytest` 通过：83 passed；
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

Step 28 已跑通。当前核心 MVP、Extension 0、LLM 执行层、段落级 evidence chunks、本地 evidence search 和 ai-paper-reader chunk evidence 接入已经完成。扩展路线图已单独整理到 `docs/EXTENSION_ROADMAP.md`。

最推荐的下一步是 **Step 29: Terminology / Doubts 使用 Evidence Chunks**。术语候选和疑难点候选应优先从 `notes/evidence-chunks.md` 派生，并保留 chunk id 和 page。

完整深度论文解释、远端仓库自动 clone、完整项目方案生成仍然不建议直接展开。

核心 MVP 路线图：

```text
Step 22: Code Mapping Evidence MVP completed
Step 23: Interview Project Mapping Assessment MVP completed
Step 24: LLM Query Planner and ai-paper-reader Prompt Pack completed
Step 25: LLM Provider Config and ai-paper-reader Note Generation completed
Step 26: Paragraph / Chunk-level Evidence Map completed
Step 27: RAG / Local Evidence Search MVP completed
Step 28: ai-paper-reader Note uses Evidence Chunks completed
```

也就是说，当前核心 MVP 建议阶段已经完成。后续如果要读取远端或 clone 第三方仓库，需要再次确认。

扩展路线图暂不计入核心 MVP，详见 `docs/EXTENSION_ROADMAP.md`：

- terminology / doubts 使用 evidence chunks；
- 语义 / 向量检索；
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
