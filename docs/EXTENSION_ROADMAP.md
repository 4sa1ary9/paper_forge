# PaperForge Agent 扩展路线图

## 当前状态

截至 Step 28，PaperForge Agent 的核心 MVP、Extension 0、Extension 1、本地检索 MVP 和 ai-paper-reader chunk evidence 接入已闭环：

```text
query planning
  -> intake
  -> asset collection
  -> source enrichment
  -> image extraction
  -> code candidate linking
  -> note / terminology / doubts / interview scaffolds
  -> PDF text evidence map
  -> paragraph / chunk evidence map
  -> local evidence search
  -> package validation
  -> deep note readiness
  -> conservative deep note writing
  -> ai-paper-reader prompt pack
  -> chunk-grounded ai-paper-reader note generation
  -> terminology evidence
  -> doubts evidence
  -> code mapping evidence
  -> interview project assessment
```

当前版本适合展示 agent workflow、状态管理、产物规范、证据约束和可扩展架构。它还不是完整深度研究系统。

## 扩展原则

- 先提升 evidence 质量，再提升生成质量。
- 不把没有证据支撑的内容包装成最终结论。
- 不自动 clone 大仓库；远端仓库读取或 clone 需要用户确认。
- 不直接从 MVP 跳到完整项目方案生成。
- 每个扩展阶段都要有明确输入、输出、失败状态和验证方式。

## 推荐顺序

### Extension 0: LLM Query Planner 与 ai-paper-reader Prompt Pack

状态：已完成。

目标：

- 先解决“用户输入简称时找错论文”的入口问题。例如 `unet` 应优先解析到原始论文 `U-Net: Convolutional Networks for Biomedical Image Segmentation`，而不是随机 U-Net 变体。
- 把现有 Codex skill `ai-paper-reader` 纳入 PaperForge workflow：第一版不在应用运行时直接调用 skill，而是生成可复制给 Codex 的 prompt pack。

输入：

- 用户输入的论文标题、简称、arXiv ID 或 URL。
- 当前 research job 的 `metadata.json`、`raw/paper.pdf`、`notes/README.md`、`notes/evidence-map.md`、`images/manifest.md`。
- skill 文件：`C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md`

输出：

- `notes/query-plan.md`
- `notes/ai-paper-reader-prompt.md`

边界：

- arXiv ID、arXiv URL 和 PDF URL 不经过 LLM 改写。
- LLM 不可用时必须 fallback 到原始查询或确定性别名表。
- 第一版只生成给 Codex 的 prompt，不假装 Streamlit 能直接调用本地 Codex skill。

详细设计和实现提示词：

- `docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md`
- `docs/PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md`

验证：

- `unet` / `u-net` / `u net` 能稳定解析到原始 U-Net 论文。
- prompt 文件包含准确 skill 路径和当前 job 的关键 artifact 路径。
- 单元测试覆盖 LLM fallback、坏 JSON、缺失 artifact 和 timeline/artifact 更新。

### Extension 1: 段落级 Evidence Map

状态：已完成。

目标：

- 把当前页码级 `notes/evidence-map.md` 细化为 paragraph / chunk 级证据。
- 给后续深度笔记、术语解释、疑难点分析和 RAG 提供更精确的来源定位。

输入：

- `raw/paper.pdf`
- `notes/evidence-map.md`

输出：

- `notes/evidence-chunks.md`
- 每个 chunk 包含 chunk id、page、section guess、character count 和 text excerpt。

边界：

- 只做证据切分和索引，不生成深度解释。
- 不做 embedding，不做语义检索。

验证：

- 单元测试覆盖 Page 1 / Page 2 解析、空行和长度切分、稳定 chunk id、section guess、缺失 evidence-map partial report、timeline/artifact 和 job 保存。

### Extension 2: RAG / 本地检索 MVP

状态：已完成。

目标：

- 基于 `notes/evidence-chunks.md` 做本地关键词检索。
- 支持“在论文证据内查找答案”，而不是泛泛问答。

输入：

- 用户查询。
- `notes/evidence-chunks.md`

输出：

- `notes/evidence-search.md`
- 检索结果返回 chunk id、page、score 和 excerpt。

边界：

- 第一版使用确定性关键词匹配或 BM25-like 简单评分。
- 不做向量数据库，不引入复杂依赖。
- 不把检索结果直接包装成最终答案。

验证：

- 测试 method 和 experiment chunk 命中、缺失 chunks 文件的 partial / needs_user_input、输出 Markdown、timeline 和 artifact 更新。

### Extension 3: Evidence-Grounded Deep Explanation

状态：进行中。Step 28 已完成，让 ai-paper-reader note generation 优先使用 evidence chunks。下一步是 Step 29，让 terminology / doubts 使用 evidence chunks。

目标：

- 在 paragraph / chunk 级证据基础上，逐步生成更完整的论文解释。
- 优先扩展 Core Method、Experiments、Limitations，再扩展公式、术语和疑难点。

输入：

- `notes/evidence-chunks.md`
- `notes/README.md`
- `notes/deep-note-plan.md`
- `images/manifest.md`

输出：

- 更新后的 `notes/README.md`
- 更新后的 `notes/ai-paper-reader-note.md`
- 保留 chunk/page evidence 引用和人工复查标记。

边界：

- 不一次性生成完整论文报告。
- 每个章节只使用已准备好的 evidence chunks。
- LLM 输出需要保留 evidence reference，不允许无来源结论。

验证：

- 测试章节替换、证据引用格式和缺失输入 partial 状态。
- 真实样例检查生成内容是否引用具体 page/chunk。

已完成的第一步：

- Step 28：ai-paper-reader generation prompt 优先包含 `notes/evidence-chunks.md` excerpt，缺失时 fallback 到 `notes/evidence-map.md`；prompt 要求优先引用 chunk id、无法验证的内容标注为待核查、不得凭模型记忆补全论文细节。

### Extension 4: 语义 / 向量检索扩展

目标：

- 在本地关键词检索 MVP 稳定后，再考虑 embedding 或向量检索。
- 保持所有结果都能追溯到 chunk id、page 和 excerpt。

输入：

- `notes/evidence-chunks.md`
- 可选：`notes/README.md`、`notes/terminology.md`、`notes/doubts.md`

输出：

- 本地索引文件，放在 `.paperforge-data/`。
- 检索结果返回 chunk id、page、score 和 excerpt。

边界：

- 只在关键词检索 MVP 不够用时再做。
- 不做多论文知识库。
- 不把检索结果直接包装成最终答案。

验证：

- 测试索引构建、查询返回、空索引处理和 source reference。
- 真实样例能根据关键词返回相关 chunk。

### Extension 5: Workflow 可视化增强

目标：

- 让 Streamlit 页面更清楚展示 agent step、artifact、失败原因和下一步建议。
- 提升 demo 和面试展示效果。

输入：

- `ResearchJob`
- `AgentStep`
- `Artifact`

输出：

- 更清楚的 timeline / artifact view。
- 可区分 completed、partial、failed、needs_user_input。

边界：

- 继续使用 Streamlit。
- 不迁移 FastAPI / React。
- 不做复杂前端状态管理。

验证：

- 运行 Streamlit，检查已有 job 能正常展示。
- 如果改 UI 逻辑，补轻量函数测试或手动验证记录。

### Extension 6: 多篇论文批处理

目标：

- 支持同主题多篇论文的研究包队列。
- 为后续 related work、论文对比和综述做准备。

输入：

- 多个 arXiv ID / URL
- 可选主题名称

输出：

- 多个 paper workspace。
- 批处理 summary，例如 `notes/batch-summary.md`。

边界：

- 第一版只做顺序批处理。
- 不做并发下载。
- 不做跨论文自动结论。

验证：

- 测试多输入解析、单篇失败不阻塞后续、summary 生成。

### Extension 7: Advanced Code Analysis

目标：

- 从文件级代码映射进一步走向更细的代码理解。
- 支持 line-level 或 function-level mapping。

输入：

- `notes/code-references.md`
- 用户确认的本地仓库路径

输出：

- 增强版 `notes/code-references.md`
- 可选 `notes/code-map.md`

边界：

- 仍然不自动 clone。
- 不分析超大仓库。
- 不把词面匹配当成真实实现对应关系。

验证：

- 测试文件扫描、函数识别、路径过滤、缺失仓库处理。

### Extension 8: Productization

目标：

- 当本地 workflow 稳定后，再考虑产品化迁移。

候选方向：

- FastAPI 后端；
- SQLite 或更正式的任务存储；
- React 前端；
- 多用户或远程运行；
- Docker 化 demo。

边界：

- 这不是当前优先级。
- 只有当 Python + Streamlit 版本的研究质量稳定后再做。

## 当前最推荐的下一步

优先做 **Step 29: Terminology / Doubts 使用 Evidence Chunks**。

原因：

- Step 28 已验证 ai-paper-reader generation prompt 能优先携带 chunk evidence。
- terminology / doubts 仍主要从 README 页码证据行派生，需要改成优先读取 `notes/evidence-chunks.md`。
- 这一步能让术语和疑难点都保留 chunk id + page，而不是只保留粗页码。

## 暂不建议直接做

- 直接生成完整深度论文报告；
- 自动 clone 第三方仓库；
- 自动生成完整项目方案；
- 直接迁移 FastAPI / React；
- 多论文自动综述结论。
