# PaperForge Agent 项目进度

## 当前阶段

**阶段：Step 5，Code Linker Agent 轻量版已完成。**

当前项目已经从 TypeScript/React/Express 调整为 **Python + Streamlit**。

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

## 当前验证状态

Python 版本已验证通过：

- 已配置 uv 项目环境；
- 已创建 `.venv` 虚拟环境；
- 激活提示名为 `agent`；
- 已生成 `uv.lock`；
- 执行 `uv run python -m pytest` 通过：14 passed；
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
- Streamlit 已启动：
  - URL：`http://localhost:8501`
  - HTTP 状态：200

验证时修复过两个问题：

- arXiv API 返回 HTTP 429：已给请求添加 User-Agent。
- 旧 TypeScript 版本留下的 job 文件是 camelCase：Python 版读取逻辑已兼容。

## 下一步

Step 5 已跑通。下一步不要直接扩大 scope，建议做 **Note Writer Agent 骨架版**：

```text
metadata + images/manifest.md + external-sources.md + code-references.md
  -> 写 notes/README.md 的结构化初稿
  -> 更新 timeline
```

## 暂不做

- clone 仓库；
- 深度论文笔记生成；
- 术语库；
- 疑难点；
- 面试项目映射；
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

> 我做的是一个 AI 论文研究 Agent。它不是简单总结论文，而是把论文研究拆成可追踪的 workflow：论文识别、资产下载、代码关联、资料增强、深度笔记、疑难点和面试项目映射。当前版本先完成了 Python 版 intake workflow，后续会逐步扩展到资产收集和笔记生成。

不要说：

> 我从零手写了一个完整多智能体系统。

更稳的说法是：

> 我用 AI 辅助开发，但需求设计、工作流拆分、产物规范和核心逻辑是我主导理解和迭代的。
