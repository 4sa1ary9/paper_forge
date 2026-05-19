# PaperForge Agent 开发步骤记录

## Step 0: 技术栈调整

### 背景

最初版本使用 TypeScript + React + Express 搭了一个全栈骨架。这个方案展示效果好，但需要同时理解前端、后端、TypeScript 和 Node 工程，对当前学习目标不合适。

因此项目调整为：

```text
Python + Streamlit + 本地文件系统
```

### 为什么这样改

这个项目的核心不是炫技术栈，而是讲清楚：

- 为什么需要这个 agent；
- agent workflow 怎么拆；
- 每一步产物是什么；
- 失败如何记录；
- 如何把论文学习转成面试项目。

用 Python 可以让你把注意力集中在这些核心能力上。

## Step 1: Python 工程地基和论文 Intake 最小闭环

### 目标

先让项目变成一个可运行、可验证、可继续扩展的 Python Agent 工程，而不是直接堆 prompt。

本阶段完成的最小闭环：

```text
用户输入 arXiv URL
  -> Agent 解析 arXiv 元信息
  -> 创建 ResearchJob
  -> 创建 paper workspace
  -> 写 metadata.json
  -> 写 external-sources.md
  -> Streamlit 展示 paper summary、timeline、artifacts
```

### 为什么先做这一步

PaperForge Agent 后面会涉及论文下载、TeX Source、PDF 解析、GitHub 代码分析、笔记生成、术语库和面试项目映射。如果一开始没有稳定的数据结构和目录规范，后续功能会很快混在一起。

所以第一步先确定几个边界：

- `app.py`：Streamlit 工作台入口。
- `paperforge/`：Python 核心代码。
- `paperforge/models.py`：统一数据结构。
- `paperforge/intake_agent.py`：当前第一条 agent workflow。
- `.paperforge-data/`：本地生成数据，默认不进入 git。
- `.paperforge-data/paper-vault/`：论文研究产物目录。

### 已完成文件

核心工程文件：

- `pyproject.toml`
- `.python-version`
- `uv.lock`
- `.gitignore`
- `.env.example`
- `app.py`

Python 核心模块：

- `paperforge/models.py`
- `paperforge/arxiv_client.py`
- `paperforge/intake_agent.py`
- `paperforge/storage.py`
- `paperforge/steps.py`
- `paperforge/slug.py`

测试：

- `tests/test_arxiv_client.py`
- `tests/test_slug.py`

### 当前能力

已支持：

- 解析 arXiv URL；
- 解析 arXiv PDF URL；
- 解析裸 arXiv ID；
- 通过 arXiv Atom API 获取标题、作者、摘要、年份、PDF URL、TeX Source URL；
- 在 `.paperforge-data/paper-vault/<paper-slug>/` 创建目录；
- 写入 `metadata.json`；
- 写入 `notes/external-sources.md`；
- 保存 job record；
- Streamlit 展示 intake 结果。

### 验证方式

安装依赖：

```powershell
uv venv --prompt agent .venv
uv sync
```

运行测试：

```powershell
uv run python -m pytest
```

启动应用：

```powershell
uv run streamlit run app.py
```

真实 intake 示例：

```text
https://arxiv.org/abs/1706.03762
```

预期生成结果：

```text
.paperforge-data/
├── jobs/
│   └── <job-id>.json
└── paper-vault/
    └── attention-is-all-you-need/
        ├── metadata.json
        ├── images/
        ├── raw/
        └── notes/
            └── external-sources.md
```

当前验证结果：

```text
pytest: 6 passed
Streamlit: http://localhost:8501 返回 200
真实 intake: https://arxiv.org/abs/1706.03762 -> completed
```

实现过程中修复过一个问题：

- arXiv API 曾返回 HTTP 429，已通过为请求添加 User-Agent 解决。
- Python 版读取旧 TypeScript 版本留下的 job 文件时，已兼容 camelCase 字段。

### 这一阶段没有做什么

这些能力留到后续步骤：

- PDF 下载；
- TeX Source 下载和解压；
- PDF 图片提取；
- GitHub 仓库搜索；
- clone 代码仓库；
- RAG；
- 深度论文笔记生成；
- 术语库和疑难点生成；
- 面试项目映射报告。

### 下一步建议

Step 2 应该做 **Asset Collector Agent**：

```text
metadata.pdf_url
  -> 下载 raw/paper.pdf
metadata.source_url
  -> 下载 raw/source.tar.gz
  -> 解压 raw/tex-source/
  -> 更新 timeline 和 artifacts
```

这一步完成后，PaperForge Agent 就从“只建研究任务”进入“真正收集论文资产”的阶段。

## Step 2: Asset Collector Agent

### 目标

让已经完成 intake 的论文研究任务继续收集原始资产：

```text
metadata.pdf_url
  -> raw/paper.pdf
metadata.source_url
  -> raw/source.tar.gz
  -> raw/tex-source/
```

本阶段重点不是做 PDF 理解或笔记生成，而是把论文 PDF 和 TeX Source 先稳定落盘，并把每一步记录到 timeline。

### 为什么这样做

后续的图片提取、TeX 解析、深度笔记和代码映射都依赖稳定的本地资产。如果没有统一的 `raw/` 目录和 artifact 记录，后续模块很难判断哪些输入已经存在、哪些步骤失败、哪些步骤可以重跑。

所以 Step 2 只解决三件事：

- 资产下载到固定路径；
- TeX Source 尝试解压到固定目录；
- 下载和解压状态写回 `ResearchJob`。

### 已完成文件

新增核心模块：

- `paperforge/asset_collector.py`

修改工作台：

- `app.py`

新增测试：

- `tests/test_asset_collector.py`

### 当前能力

已支持：

- 根据 `metadata.pdf_url` 下载 PDF，并统一保存为 `raw/paper.pdf`；
- 根据 `metadata.source_url` 下载 TeX Source，并统一保存为 `raw/source.tar.gz`；
- 从 `source.tar.gz` 解压到 `raw/tex-source/`；
- 已存在的资产不会被覆盖；
- PDF、TeX Source archive、解压目录会加入 artifacts；
- `asset.collect_pdf`、`asset.collect_source`、`asset.extract_source` 会加入 timeline；
- 缺少 TeX Source URL 时跳过 source 步骤，不把整个 job 判失败；
- source 下载失败时记录错误，并把 job 标记为 `partial`；
- Streamlit 页面可以对已有 job 点击 `Collect Assets`。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

当前验证结果：

```text
pytest: 9 passed
Streamlit: http://localhost:8501 返回 200
真实样例: https://arxiv.org/abs/1706.03762 -> completed
```

真实样例生成资产：

```text
.paperforge-data/paper-vault/attention-is-all-you-need/
└── raw/
    ├── paper.pdf
    ├── source.tar.gz
    └── tex-source/
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- PDF 图片提取；
- TeX 内容解析；
- GitHub 仓库搜索；
- clone 仓库；
- 深度论文笔记生成；
- 术语库和疑难点生成；
- 面试项目映射报告。

### 下一步建议

下一步不要直接扩大 scope。建议先确认是继续做 **PDF Image Extractor Agent**，还是转向 **Source Enrichment Agent**。

## Step 3: Source Enrichment Agent

### 目标

优先实现轻量版外部资料整理，而不是先做图片提取。

本阶段完成的流程：

```text
metadata + artifacts + user source URLs
  -> notes/external-sources.md
  -> 更新 timeline
  -> 更新 artifacts
```

这里的 Source Enrichment 指“外部资料来源增强”，不是 arXiv TeX Source。考虑到有些论文没有 TeX Source，本阶段明确保留 PDF 处理路径：只要 `raw/paper.pdf` 存在，后续仍然可以继续做 PDF 图片提取和 PDF-based 笔记生成。

### 为什么这样做

外部资料来源是后续深度笔记和代码关联的证据入口。第一版不应该直接做脆弱爬虫，也不应该假设每篇论文都有 TeX Source。更稳的做法是先维护一个清楚的 `external-sources.md`：

- 官方论文链接；
- PDF URL；
- TeX Source URL；
- 本地 PDF 是否可用；
- 本地 TeX Source 是否可用；
- 用户手动提供的教程、博客或项目 URL；
- 可靠性标签。

### 已完成文件

新增核心模块：

- `paperforge/source_enrichment.py`

修改工作台：

- `app.py`

新增测试：

- `tests/test_source_enrichment.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 生成或更新 `notes/external-sources.md`；
- 记录 canonical paper、PDF URL、TeX Source URL；
- 记录本地 `raw/paper.pdf` 是否可用；
- 记录本地 `raw/tex-source/` 或 `raw/source.tar.gz` 是否可用；
- 缺少 TeX Source 时写入 `Fallback: continue with PDF-based processing.`；
- 支持 Streamlit 输入用户外部资料 URL，每行一个；
- 将 `source.enrich_external_sources` 写入 timeline；
- 将 `notes/external-sources.md` 保持为 note artifact。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

当前验证结果：

```text
pytest: 10 passed
真实样例: https://arxiv.org/abs/1706.03762 -> source.enrich_external_sources completed
```

测试覆盖了一个关键约束：

```text
TeX Source 缺失
  -> PDF 仍然记录为可用
  -> external-sources.md 写入 PDF-based fallback
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动抓取教程正文；
- 判断外部资料质量；
- GitHub 仓库搜索；
- clone 仓库；
- PDF 图片提取；
- 深度论文笔记生成；
- 术语库和疑难点生成；
- 面试项目映射报告。

### 下一步建议

下一步建议做 **PDF Image Extractor Agent**。原因是现在已经有：

- metadata；
- PDF；
- TeX Source（可选）；
- external source log。

继续提取 PDF 图片后，深度笔记会有更稳定的图表输入。

## Environment Update: uv + .venv 环境

### 目标

把项目迁移到 uv 管理的本地环境。虚拟环境目录保持为 `.venv/`，激活后显示 `(agent)`。

### 为什么这样做

uv 可以用 `pyproject.toml` 和 `uv.lock` 固定项目依赖，后续接手项目时只需要同步环境，不需要手动记住 pip 安装步骤。

### 已完成文件

- `pyproject.toml`
- `.python-version`
- `uv.lock`
- `.gitignore`
- `README.md`
- `AGENTS.md`
- `docs/PROGRESS.md`

### 验证方式

```powershell
uv venv --prompt agent .venv
uv sync
uv run python -m pytest
```

预期结果：

```text
pytest: 10 passed
```

当前验证结果：

```text
uv sync: created .venv environment and uv.lock
uv run python -m pytest: 10 passed
```

## Step 4: PDF Image Extractor Agent

### 目标

从已下载的 `raw/paper.pdf` 中提取图片，给后续深度笔记提供图表输入。

本阶段完成的流程：

```text
raw/paper.pdf
  -> images/<figure-file>
  -> images/manifest.md
  -> 更新 timeline
  -> 更新 artifacts
```

TeX Source 仍然是可选输入。只要 PDF 存在，本步骤就可以继续运行。

### 为什么这样做

深度论文笔记不能只依赖摘要和正文总结。架构图、方法图、实验结果图通常是理解论文最关键的材料。先把 PDF 图片提取出来，后续 Note Writer Agent 才能引用稳定的本地图片和页码映射。

### 已完成文件

新增核心模块：

- `paperforge/pdf_image_extractor.py`

新增脚本：

- `scripts/run_pipeline.py`

修改工作台：

- `app.py`

新增测试：

- `tests/test_pdf_image_extractor.py`

更新依赖：

- `pyproject.toml`
- `uv.lock`
- `requirements.txt`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 使用 PyMuPDF 打开 `raw/paper.pdf`；
- 提取 PDF 内嵌图片；
- 过滤过小图片，减少图标和装饰图；
- 如果没有可用内嵌图片，渲染前几页作为 fallback；
- 图片写入 `images/`；
- 生成 `images/manifest.md`；
- manifest 记录文件名、页码、尺寸和来源；
- 图片和 manifest 写入 artifacts；
- `pdf.extract_images` 写入 timeline；
- 缺少 PDF 时跳过并标记 job 为 `partial`；
- Streamlit 页面增加 `Extract PDF Images` 按钮，并能预览图片 artifact。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py
```

当前验证结果：

```text
pytest: 12 passed
真实样例: https://arxiv.org/abs/2006.11239 -> pdf.extract_images completed
输出: 22 个图片文件 + images/manifest.md
```

真实样例生成目录：

```text
.paperforge-data/paper-vault/denoising-diffusion-probabilistic-models/
└── images/
    ├── fig001_page1_img1.png
    ├── ...
    └── manifest.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 图片语义分类；
- 自动判断架构图、方法图、结果图；
- OCR；
- PDF 正文解析；
- GitHub 仓库搜索；
- clone 仓库；
- 深度论文笔记生成；
- 术语库和疑难点生成；
- 面试项目映射报告。

### 下一步建议

下一步建议做 **Code Linker Agent 轻量版**：

```text
metadata.github_candidates + external-sources.md
  -> 识别或记录 GitHub URL
  -> notes/code-references.md
  -> 更新 timeline 和 artifacts
```

第一版只记录和整理候选仓库，不做自动 clone，不做大型 GitHub 搜索。

## Step 5: Code Linker Agent 轻量版

### 目标

整理论文相关的 GitHub 候选仓库，生成代码引用说明，但不自动 clone 仓库。

本阶段完成的流程：

```text
metadata.github_candidates + notes/external-sources.md
  -> notes/code-references.md
  -> 更新 timeline
  -> 更新 artifacts
```

### 为什么这样做

代码关联是 PaperForge Agent 的重要能力，但直接自动搜索和 clone 仓库容易扩大 scope，也容易遇到仓库过大、license 不清楚、官方性不确定等问题。

所以第一版只做保守整理：

- 读取 metadata 里的 GitHub 候选；
- 从 external source log 中提取 GitHub URL；
- 生成 `code-references.md`；
- 明确记录 `Clone decision: not cloned`；
- 后续 clone 必须由用户确认。

### 已完成文件

新增核心模块：

- `paperforge/code_linker.py`

修改工作台：

- `app.py`

新增测试：

- `tests/test_code_linker.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 从 `metadata.github_candidates` 读取候选仓库；
- 从 `notes/external-sources.md` 提取 GitHub 仓库 URL；
- 去重候选 URL；
- 生成 `notes/code-references.md`；
- 写入 license、技术栈、核心文件、方法映射等待检查字段；
- 写入 `Clone decision: not cloned`；
- 没有 GitHub 候选时标记为 `partial`；
- 将 `code.link_repositories` 写入 timeline；
- 将 `notes/code-references.md` 写入 artifacts；
- Streamlit 页面增加 `Link Code Candidates` 按钮。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行真实样例：

```powershell
uv run python - <<'PY'
from paperforge.intake_agent import run_paper_intake
from paperforge.asset_collector import run_asset_collection
from paperforge.source_enrichment import run_source_enrichment
from paperforge.code_linker import run_code_linking

job = run_paper_intake("https://arxiv.org/abs/1706.03762")
job = run_asset_collection(job)
job = run_source_enrichment(job, ["https://github.com/harvardnlp/annotated-transformer"])
job = run_code_linking(job)
print(job.status)
print(job.steps[-1].state)
print(job.steps[-1].outputs)
PY
```

当前验证结果：

```text
pytest: 14 passed
真实样例: https://arxiv.org/abs/1706.03762 -> code.link_repositories completed
输出: paper-vault/attention-is-all-you-need/notes/code-references.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- GitHub 全网搜索；
- GitHub API 查询仓库元信息；
- license 自动检测；
- 自动 clone；
- 代码文件分析；
- 方法到代码的真实映射。

### 下一步建议

下一步建议做 **Note Writer Agent 骨架版**：

```text
metadata + images/manifest.md + external-sources.md + code-references.md
  -> notes/README.md
  -> 更新 timeline 和 artifacts
```

第一版只生成结构化笔记骨架和引用本地 artifact，不生成深度解释，避免伪造论文理解。

## Step 6: Note Writer Agent 骨架版

### 目标

生成主论文笔记入口 `notes/README.md`，但只做结构化骨架，不生成未经验证的深度解释。

本阶段完成的流程：

```text
metadata + external-sources.md + images/manifest.md + code-references.md
  -> notes/README.md
  -> 更新 timeline
  -> 更新 artifacts
```

### 为什么这样做

前面步骤已经生成了 metadata、PDF、图片 manifest、外部来源记录和代码候选。此时需要一个主笔记入口把这些产物串起来。

但第一版不能假装已经完成深度论文理解，所以 Note Writer 只生成：

- 元信息；
- 标准章节结构；
- evidence inventory；
- 明确的 scaffold 状态；
- 后续需要人工或 LLM 深入生成的占位内容。

### 已完成文件

新增核心模块：

- `paperforge/note_writer.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 生成 `notes/README.md`；
- 写入标题、论文 URL、作者、venue、年份；
- 写入 `Draft status: scaffold only; deep explanation not generated yet.`；
- 生成 `TL;DR`、`Paper Overview`、`Background and Motivation`、`Core Method`、`Code Mapping`、`Experiments`、`Deep Q&A`、`Limitations`、`Practical Takeaways` 等章节；
- 引用 `notes/external-sources.md`；
- 引用 `images/manifest.md`；
- 引用 `notes/code-references.md`；
- 将 `note.write_readme` 写入 timeline；
- 将 `notes/README.md` 写入 artifacts；
- Streamlit 页面增加 `Write Note Scaffold` 按钮。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 15 passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_readme completed
输出: paper-vault/attention-is-all-you-need/notes/README.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动生成 TL;DR；
- 深度方法解释；
- 公式解释；
- 实验结果解读；
- 图文对应解释；
- 术语库；
- 疑难点；
- 面试项目映射。

### 下一步建议

下一步建议做 **Terminology Agent 骨架版**：

```text
metadata + notes/README.md
  -> notes/terminology.md
  -> 更新 timeline 和 artifacts
```

第一版只生成术语文件结构，不自动提取术语，避免从摘要里机械编造关键词。

## Step 7: Terminology Agent 骨架版

### 目标

生成专业术语文件 `notes/terminology.md` 的结构化模板，但不自动抽取术语。

本阶段完成的流程：

```text
metadata + notes/README.md
  -> notes/terminology.md
  -> 更新 timeline
  -> 更新 artifacts
```

### 为什么这样做

术语库应该服务后续学习，而不是把标题、摘要里的名词机械列出来。当前还没有深度论文解析能力，所以第一版只创建可填写的结构，避免生成看似完整但不可靠的术语解释。

### 已完成文件

新增核心模块：

- `paperforge/terminology_agent.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_terminology_agent.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 生成 `notes/terminology.md`；
- 写入论文标题；
- 链接 `notes/README.md`；
- 写入 `Draft status: scaffold only; terms not extracted yet.`；
- 写入标准术语字段：
  - `Category`
  - `Short explanation`
  - `Why it matters in this paper`
  - `Related terms`
  - `First seen in`
  - `Follow-up reading`
- 将 `knowledge.write_terminology` 写入 timeline；
- 将 `notes/terminology.md` 写入 artifacts；
- Streamlit 页面增加 `Write Terminology Scaffold` 按钮。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 16 passed
真实样例: https://arxiv.org/abs/1706.03762 -> knowledge.write_terminology completed
输出: paper-vault/attention-is-all-you-need/notes/terminology.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动抽取术语；
- 术语解释生成；
- 术语与公式、图表、代码的定位；
- 术语可靠性评估；
- 深度疑难点生成；
- 面试项目映射。

### 下一步建议

下一步建议做 **Doubts Agent 骨架版**：

```text
metadata + notes/README.md
  -> notes/doubts.md
  -> 更新 timeline 和 artifacts
```

第一版只生成疑难点文件结构，不自动编造问题。

## Step 8: Doubts Agent 骨架版

### 目标

生成疑难点文件 `notes/doubts.md` 的结构化模板，但不自动编造开放问题。

本阶段完成的流程：

```text
metadata + notes/README.md
  -> notes/doubts.md
  -> 更新 timeline
  -> 更新 artifacts
```

### 为什么这样做

疑难点是后续深度阅读的重要资产，但在没有真正解析论文方法、公式和代码之前，自动生成问题很容易变成泛泛的问题清单。

所以第一版只创建可填写的结构：

- open questions；
- confusing formulas；
- missing implementation details；
- claims that need verification；
- questions to ask an interviewer or mentor。

### 已完成文件

新增核心模块：

- `paperforge/doubts_agent.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_doubts_agent.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 生成 `notes/doubts.md`；
- 写入论文标题；
- 链接 `notes/README.md`；
- 写入 `Draft status: scaffold only; doubts not generated yet.`；
- 写入推荐章节：
  - `Open Questions`
  - `Confusing Formulas`
  - `Missing Implementation Details`
  - `Claims That Need Verification`
  - `Questions to Ask an Interviewer or Mentor`
- 将 `knowledge.write_doubts` 写入 timeline；
- 将 `notes/doubts.md` 写入 artifacts；
- Streamlit 页面增加 `Write Doubts Scaffold` 按钮。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 17 passed
真实样例: https://arxiv.org/abs/1706.03762 -> knowledge.write_doubts completed
输出: paper-vault/attention-is-all-you-need/notes/doubts.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动生成疑难点；
- 公式定位；
- 代码实现缺口判断；
- 论文 claim 证据核验；
- 面试项目映射。

### 下一步建议

下一步建议做 **Interview Mapper Agent 骨架版**：

```text
metadata + notes/README.md + notes/code-references.md
  -> notes/interview-project.md
  -> 更新 timeline 和 artifacts
```

第一版只生成面试项目评估结构，不自动给出适配度结论。

## Step 9: Interview Mapper Agent 骨架版

### 目标

生成面试项目映射文件 `notes/interview-project.md` 的结构化模板，但不自动判断论文是否适合做项目。

本阶段完成的流程：

```text
metadata + notes/README.md + notes/code-references.md
  -> notes/interview-project.md
  -> 更新 timeline
  -> 更新 artifacts
```

### 为什么这样做

PaperForge 的长期目标之一是把论文阅读转成可讲清楚的面试项目。但在还没有完成深度论文理解、代码映射和资源评估之前，直接输出“高适配度”或完整项目方案会过早下结论。

所以第一版只创建评估结构：

- suitability；
- 为什么可能成为项目；
- 为什么可能不值得做；
- minimal demo version；
- full version；
- technical highlights；
- risks；
- 与已有项目的连接；
- interview talking points。

### 已完成文件

新增核心模块：

- `paperforge/interview_mapper.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_interview_mapper.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 生成 `notes/interview-project.md`；
- 写入论文标题；
- 链接 `notes/README.md`；
- 链接 `notes/code-references.md`；
- 写入 `Draft status: scaffold only; suitability not assessed yet.`；
- 写入完整项目映射章节；
- 将 `project.write_interview_mapping` 写入 timeline；
- 将 `notes/interview-project.md` 写入 artifacts；
- Streamlit 页面增加 `Write Interview Mapping Scaffold` 按钮。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 18 passed
真实样例: https://arxiv.org/abs/1706.03762 -> project.write_interview_mapping completed
输出: paper-vault/attention-is-all-you-need/notes/interview-project.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动判断项目适配度；
- 自动设计 minimal demo；
- 自动设计 full version；
- 自动生成面试话术；
- 结合真实代码文件做技术亮点判断；
- 计算资源和实现周期评估。

### 下一步建议

下一步建议做 **Research Package Validator Agent 骨架版**：

```text
paper-vault/<slug>/
  -> 检查 metadata、PDF、图片 manifest、notes 产物是否存在
  -> notes/package-status.md
  -> 更新 timeline 和 artifacts
```

这一步可以把当前的多个 scaffold 产物变成一个可验收的研究包状态，再进入深度内容生成。
