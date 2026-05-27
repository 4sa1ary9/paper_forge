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

## Step 10: Research Package Validator Agent 骨架版

### 目标

生成研究包状态文件 `notes/package-status.md`，只检查当前论文工作区中的文件是否存在，不判断内容质量。

本阶段完成的流程：

```text
paper-vault/<slug>/
  -> 检查 metadata、PDF、图片 manifest、notes 产物是否存在
  -> notes/package-status.md
  -> 更新 timeline
  -> 更新 artifacts
```

### 为什么这样做

前面步骤已经生成了论文 metadata、PDF、图片 manifest、外部来源记录、代码引用、主笔记骨架、术语库、疑难点和面试项目映射。进入深度内容生成之前，需要一个轻量验收门槛，明确哪些基础输入已经存在，哪些还需要补齐。

这个阶段刻意不做深度判断：

- 不检查论文笔记是否真的解释了方法；
- 不判断术语解释是否正确；
- 不判断疑难点是否有价值；
- 不判断面试项目适配度；
- 不因为 TeX Source 缺失阻塞 PDF-based processing。

### 已完成文件

新增核心模块：

- `paperforge/package_validator.py`

修改数据模型：

- `paperforge/models.py`

修改已有 agent：

- `paperforge/package_validator.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_package_validator.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 生成 `notes/package-status.md`；
- 检查 required 产物：
  - `metadata.json`；
  - `notes/external-sources.md`；
  - `notes/code-references.md`；
  - `notes/README.md`；
  - `notes/terminology.md`；
  - `notes/doubts.md`；
  - `notes/interview-project.md`；
- 检查 recommended 产物：
  - `raw/paper.pdf`；
  - `images/manifest.md`；
- 检查 optional 产物：
  - `raw/source.tar.gz`；
  - `raw/tex-source/`；
- required 缺失时将 validator step 标记为 `partial`；
- PDF 或图片 manifest 缺失时记录 warning；
- TeX Source 缺失只写入 optional missing；
- 将 `package.validate_research_package` 写入 timeline；
- 将 `notes/package-status.md` 写入 artifacts；
- Streamlit 页面增加 `Validate Research Package` 按钮。

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
pytest: 21 passed
compileall: app.py paperforge tests scripts passed
真实样例: https://arxiv.org/abs/1706.03762 -> package.validate_research_package completed
输出: paper-vault/attention-is-all-you-need/notes/package-status.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动评估笔记质量；
- 自动生成深度论文解释；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- 自动 clone 或分析第三方仓库。

### 下一步建议

下一步建议先确认 **深度笔记生成前的质量门槛**，再决定是否进入深度内容生成。

## Documentation Update: 完成度核对（Step 10 时点）

### 目标

把“当前阶段已完成”和“长期规划未完成”明确分开，避免把 scaffold MVP 误说成最终研究包已经完成。

### 已完成文件

新增文档：

- `docs/STATUS_REVIEW.md`

更新文档：

- `docs/PROGRESS.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当时结论

```text
Stage: Step 10 completed
Completion level: scaffold MVP completed
Full project vision: not completed
```

当时项目已经按 Step 10 文档目标跑通，但还没有完成深度论文笔记、自动术语解释、疑难点生成、代码分析、面试项目适配度判断和 RAG 等长期规划。后续 Step 11 已继续补上 deep note readiness gate。

### 下一步建议

下一步建议做 **Step 11: Deep Note Planner / Readiness Gate**，先判断哪些章节有证据支撑，再决定是否进入 LLM 深度内容生成。

## Step 11: Deep Note Planner / Readiness Gate

### 目标

在进入 LLM 深度笔记生成之前，先生成一个确定性的准备度计划：

```text
notes/package-status.md + notes/README.md + raw/paper.pdf + images/manifest.md
  -> notes/deep-note-plan.md
  -> 更新 timeline 和 artifacts
```

本阶段仍然不生成 TL;DR、方法解释、实验解读或 practical takeaway，只判断哪些章节拥有基础证据，哪些章节必须继续保持 blocked。

### 为什么这样做

Step 10 的 `package-status.md` 只说明文件是否存在，还不能说明哪些笔记章节可以安全生成。直接让 LLM 写深度笔记会让系统重新回到不可验证的总结工具。

所以 Step 11 先做一个 readiness gate：

- required 输入缺失时不能进入深度生成；
- PDF 和图片 manifest 缺失时，Core Method 和 Experiments 不能自动生成；
- Code Mapping 即使有候选文件，也只能标记为 review-ready，因为当前仍不 clone 仓库；
- Deep Q&A 和 Practical Takeaways 必须等方法和实验笔记存在后再生成。

### 已完成文件

新增核心模块：

- `paperforge/deep_note_planner.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_deep_note_planner.py`

更新文档：

- `README.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 生成 `notes/deep-note-plan.md`；
- 检查 `notes/package-status.md`、`notes/README.md`、`raw/paper.pdf`、`images/manifest.md`、`notes/external-sources.md` 和 `notes/code-references.md` 是否存在；
- 输出 readiness input table；
- 输出 section readiness table；
- 标记 TL;DR、Paper Overview、Background and Motivation、Core Method、Code Mapping、Experiments、Deep Q&A、Limitations 和 Practical Takeaways 的状态；
- 缺少 required 或 recommended 输入时将 step 标记为 `partial`；
- 将 `note.plan_deep_note` 写入 timeline；
- 将 `notes/deep-note-plan.md` 写入 artifacts；
- Streamlit 页面增加 `Plan Deep Note Readiness` 按钮。

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
pytest: 23 passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.plan_deep_note completed
输出: paper-vault/attention-is-all-you-need/notes/deep-note-plan.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- PDF 正文提取和段落级 evidence map；
- 自动生成深度论文解释；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- clone 或分析第三方代码仓库。

### 下一步建议

下一步建议做 **Step 12: PDF Text Evidence Extractor**：

```text
raw/paper.pdf
  -> notes/evidence-map.md
  -> 为 Deep Note Writer 提供可引用的页码和文本证据
```

## Step 12: PDF Text Evidence Extractor

### 目标

在进入 Deep Note Writer 之前，先从 PDF 提取可引用的分页文本证据：

```text
raw/paper.pdf
  -> notes/evidence-map.md
  -> 更新 timeline 和 artifacts
  -> Deep Note Planner 使用 evidence map 判断章节准备度
```

本阶段仍然不总结论文、不解释方法、不调用 LLM。它只提供原文证据入口，让后续深度笔记可以引用页码和文本。

### 为什么这样做

Step 11 的 `deep-note-plan.md` 只能根据文件是否存在判断章节准备度。如果没有正文证据，后续 LLM 生成很容易变成泛泛总结。

所以 Step 12 先把 PDF 正文变成一个轻量 evidence map：

- 每页记录字符数和是否有可抽取文本；
- 每页保留一个文本 excerpt；
- 下游笔记必须引用这些页码证据；
- 缺少 PDF 时仍然写 partial report，避免静默失败。

### 已完成文件

新增核心模块：

- `paperforge/pdf_text_extractor.py`

修改数据模型：

- `paperforge/models.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_pdf_text_extractor.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 使用 PyMuPDF 从 `raw/paper.pdf` 提取分页文本；
- 生成 `notes/evidence-map.md`；
- 写入论文标题、提取状态、PDF 状态和 scope；
- 写入 page inventory table；
- 写入每页 text excerpt；
- 每页 excerpt 最多保留 2000 字符，避免 evidence map 过大；
- 缺少 PDF 时生成 partial evidence map；
- Research Package Validator 将 `notes/evidence-map.md` 作为 recommended artifact 检查；
- 将 `pdf.extract_text_evidence` 写入 timeline；
- 将 `notes/evidence-map.md` 写入 artifacts；
- Streamlit 页面增加 `Extract PDF Text Evidence` 按钮；
- `scripts/run_pipeline.py` 在 deep note planning 之前执行 PDF text evidence extraction。

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
pytest: 25 passed
compileall: app.py paperforge tests scripts passed
真实样例: https://arxiv.org/abs/1706.03762 -> pdf.extract_text_evidence completed
输出: paper-vault/attention-is-all-you-need/notes/evidence-map.md
```

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动生成深度论文解释；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- clone 或分析第三方代码仓库；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Step 13: Deep Note Writer MVP**：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只填充 ready 章节
  -> 保留页码证据和人工复查标记
```

## Step 13: Deep Note Writer MVP

### 目标

在 readiness gate 和 PDF text evidence map 之后，先做一个保守版深度笔记写入器：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只处理 ready 的 TL;DR 和 Paper Overview
  -> 更新 notes/README.md
  -> 保留页码证据和人工复查标记
```

本阶段仍然不生成完整深度报告，不解释 Core Method、Experiments、Deep Q&A 或 Practical Takeaways。

### 为什么这样做

Step 12 已经把 PDF 正文提取为页码级 evidence map，但如果直接让系统写完整深度笔记，仍然容易产生无证据支撑的总结。

所以 Step 13 只做最小可验证写入：

- 读取 `notes/deep-note-plan.md`，确认章节是否 ready；
- 读取 `notes/evidence-map.md`，提取可引用的页码文本；
- 只替换主笔记中的 TL;DR 和 Paper Overview；
- 更新主笔记 Draft status，避免仍显示 scaffold only；
- 每段草稿都保留页码来源；
- 明确写入 `needs human review`；
- 跳过明显版权/授权声明页，避免把 PDF boilerplate 当作论文内容。

### 已完成文件

新增核心模块：

- `paperforge/deep_note_writer.py`

修改工作台：

- `app.py`

修改流水线脚本：

- `scripts/run_pipeline.py`

新增测试：

- `tests/test_deep_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`

### 当前能力

已支持：

- 读取 `notes/deep-note-plan.md` 的 section readiness table；
- 读取 `notes/evidence-map.md` 的 page evidence excerpt；
- 只处理标记为 `ready` 的目标章节；
- 当前只写入 TL;DR 和 Paper Overview；
- 更新 `notes/README.md`；
- 将 Draft status 更新为 conservative deep note MVP；
- 写入 `note.write_deep_note_mvp` timeline step；
- 将更新后的 `notes/README.md` 写入 artifacts；
- 缺少输入时标记为 `partial`；
- 目标章节都 blocked 时不改 README，并标记为 `partial`；
- 跳过明显版权/授权声明页。

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
pytest: 29 passed
compileall: app.py paperforge tests scripts passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_deep_note_mvp completed
输出: paper-vault/attention-is-all-you-need/notes/README.md
```

验证时修复过两个问题：

- 初版会把 PDF 第 1 页版权/授权声明写入 TL;DR，已增加 boilerplate page 过滤和回归测试。
- 章节替换使用 regex replacement string 时会破坏 `\alpha` 这类反斜杠文本，已改为函数式 replacement 并增加回归测试。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 完整深度论文解释；
- Core Method 自动解释；
- Experiments 自动解读；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- clone 或分析第三方代码仓库；
- RAG / 向量检索。

### 下一步建议

下一步建议继续做 **Deep Note Writer Background MVP**：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只处理 ready 的 Background and Motivation
  -> 保留 page evidence 和人工复查标记
```

Core Method 和 Experiments 需要更细的证据选择规则，建议不要和 Background 一次性混在一起做。

## Step 14: Deep Note Writer Background MVP

### 目标

在 Step 13 已经验证 TL;DR 和 Paper Overview 写入链路后，继续保守扩展到 Background and Motivation：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只处理 ready 的 Background and Motivation
  -> 更新 notes/README.md
  -> 保留 page evidence 和人工复查标记
```

本阶段仍然不生成 Core Method、Experiments、Code Mapping、Deep Q&A 或 Practical Takeaways。

### 为什么这样做

Background and Motivation 比 Core Method 和 Experiments 风险更低，因为它主要依赖 introduction / motivation / background 相关文本证据，不需要先解析公式、方法图或实验表格。

但它仍然不能直接复用“前两页 evidence”：

- PDF 前几页可能包含版权/授权声明；
- introduction 后面可能紧跟 Figure caption；
- 图注页不应该被写成 motivation evidence；
- 输出仍然必须标注人工复查。

所以 Step 14 只做一个 Background 专用页筛选：

- 优先选择包含 introduction、motivation、background 的证据页；
- 避开明显以 `Figure ` 开头的图注页；
- 找不到匹配页时再回退到非图注页；
- 每条内容保留 `notes/evidence-map.md` 页码。

### 已完成文件

修改核心模块：

- `paperforge/deep_note_writer.py`

新增测试：

- `tests/test_deep_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 将 Background and Motivation 加入 Deep Note Writer 的目标章节；
- 只在 readiness table 标记为 `ready` 时写入 Background；
- 保持 TL;DR、Paper Overview blocked 时不改；
- Background 输出 primary background evidence pages；
- Background 输出 page-level motivation evidence；
- Background 避开明显图注页；
- Core Method 仍然保持 `Not generated yet.`。

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
pytest: 31 passed
compileall: app.py paperforge tests scripts passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_deep_note_mvp completed
输出: paper-vault/attention-is-all-you-need/notes/README.md
```

真实样例中，Background and Motivation 只引用 page 2 的 introduction 证据，未把 `Figure 1` 图注页写入 motivation evidence。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- Core Method 自动解释；
- Experiments 自动解读；
- 代码到论文方法的真实映射；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Deep Note Writer Core Method MVP**：

```text
notes/deep-note-plan.md + notes/evidence-map.md + images/manifest.md + notes/README.md
  -> 只处理 ready 的 Core Method
  -> 保留 page evidence、figure evidence 和人工复查标记
```

Core Method 需要同时引用文本证据和图片 manifest，建议继续保守实现，不一次性扩展 Experiments。

## Step 15: Deep Note Writer Core Method MVP

### 目标

在 TL;DR、Paper Overview、Background and Motivation 已经验证写入链路后，继续保守扩展到 Core Method：

```text
notes/deep-note-plan.md + notes/evidence-map.md + images/manifest.md + notes/README.md
  -> 只处理 ready 的 Core Method
  -> 更新 notes/README.md
  -> 保留 page evidence、figure evidence 和人工复查标记
```

本阶段仍然不生成 Experiments、Code Mapping、Deep Q&A、Limitations 或 Practical Takeaways。

### 为什么这样做

Core Method 比 Background 更容易误写，因为它通常同时依赖正文方法页和架构图。为了避免把未验证解释包装成结论，本阶段只做 evidence-grounded seed：

- 从 `notes/evidence-map.md` 选择 method、model、architecture、attention 等方法证据页；
- 从 `images/manifest.md` 读取图片条目，保留 figure evidence 入口；
- 如果 Core Method 已标记 ready 但图片 manifest 缺失，则步骤返回 `partial`，不改写主笔记；
- 输出仍然明确要求人工复查。

### 已完成文件

修改核心模块：

- `paperforge/deep_note_writer.py`

新增测试：

- `tests/test_deep_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 将 Core Method 加入 Deep Note Writer 的目标章节；
- 只在 readiness table 标记为 `ready` 时写入 Core Method；
- Core Method 输出 primary method evidence pages；
- Core Method 输出 page-level method evidence；
- Core Method 输出来自 `../images/manifest.md` 的 figure evidence；
- manifest 缺失时返回 `partial`，并保持 README 不变；
- Experiments 仍然保持 `Not generated yet.`。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 33 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_deep_note_mvp completed
输出: paper-vault/attention-is-all-you-need/notes/README.md
```

真实样例中，Core Method 写入了 page 2、page 3 的 method evidence，并引用 `fig001_page3_img1.png` 和 `fig002_page4_img1.png` 的 figure evidence。Experiments 和 Limitations 仍保持 `Not generated yet.`。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- Experiments 自动解读；
- Limitations 自动生成；
- 代码到论文方法的真实映射；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Deep Note Writer Experiments MVP**：

```text
notes/deep-note-plan.md + notes/evidence-map.md + images/manifest.md + notes/README.md
  -> 只处理 ready 的 Experiments
  -> 保留 page evidence、table/figure evidence 和人工复查标记
```

Experiments 需要区分实验表格、训练设置、结果页和正文解释，建议继续保守实现，不一次性扩展 Code Mapping。

## Step 16: Deep Note Writer Experiments MVP

### 目标

在 TL;DR、Paper Overview、Background and Motivation、Core Method 已经验证写入链路后，继续保守扩展到 Experiments：

```text
notes/deep-note-plan.md + notes/evidence-map.md + images/manifest.md + notes/README.md
  -> 只处理 ready 的 Experiments
  -> 更新 notes/README.md
  -> 保留 page evidence、table/result evidence、training detail evidence、figure/table evidence 和人工复查标记
```

本阶段仍然不生成 Code Mapping、Deep Q&A、Limitations 或 Practical Takeaways，也不把实验表格证据包装成完整实验解读。

### 为什么这样做

Experiments 比前面的章节更容易误写，因为 PDF page excerpt 里可能混有方法页、图注页和结果表格。为了保持证据约束，本阶段只做 evidence-grounded seed：

- 从 `notes/evidence-map.md` 选择 experiment、evaluation、benchmark、result、ablation、table 等实验证据页；
- 单独列出 table/result evidence pages；
- 单独列出 training detail evidence pages；
- 从 `images/manifest.md` 读取图片条目，保留 figure/table evidence 入口；
- 使用词边界匹配，避免把 `resulting` 误判成 result，把 `interpretable` 误判成 table；
- 输出仍然明确要求人工复查。

### 已完成文件

修改核心模块：

- `paperforge/deep_note_writer.py`

新增测试：

- `tests/test_deep_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 将 Experiments 加入 Deep Note Writer 的目标章节；
- 只在 readiness table 标记为 `ready` 时写入 Experiments；
- Experiments 输出 primary experiment evidence pages；
- Experiments 输出 page-level experiment evidence；
- Experiments 输出 table/result evidence pages；
- Experiments 输出 training detail evidence pages；
- Experiments 输出来自 `../images/manifest.md` 的 figure/table evidence；
- 使用词边界匹配减少 substring 误选；
- Limitations 仍然保持 `Not generated yet.`。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 35 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_deep_note_mvp completed
输出: paper-vault/attention-is-all-you-need/notes/README.md
```

真实样例中，Experiments 写入了 page 6、page 8 的 table/result evidence，并引用 `fig001_page3_img1.png` 和 `fig002_page4_img1.png` 的 figure/table evidence。Deep Q&A、Limitations 和 Practical Takeaways 仍保持 `Not generated yet.`。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- Limitations 自动生成；
- Deep Q&A 自动生成；
- Practical Takeaways 自动生成；
- 代码到论文方法的真实映射；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Deep Note Writer Limitations MVP**：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只处理 ready 的 Limitations
  -> 保留 page evidence 和人工复查标记
```

Limitations 不需要代码仓库证据，可以继续沿用 evidence-grounded seed 的保守策略。Deep Q&A 和 Practical Takeaways 依赖方法、实验和限制部分的质量，建议继续单独设计。

## Step 17: Deep Note Writer Limitations MVP

### 目标

在 TL;DR、Paper Overview、Background and Motivation、Core Method、Experiments 已经验证写入链路后，继续保守扩展到 Limitations：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只处理 ready 的 Limitations
  -> 更新 notes/README.md
  -> 保留 page evidence 和人工复查标记
```

本阶段仍然不生成 Deep Q&A、Practical Takeaways 或 Code Mapping，也不把限制证据包装成完整批判性分析。

### 为什么这样做

Limitations 可以继续沿用 page-level evidence map，不需要图片 manifest 或代码仓库证据。但限制类证据容易被误选，例如 `unlimited` 不能算作 limitation 证据。因此本阶段只做 conservative evidence seed：

- 从 `notes/evidence-map.md` 选择 limitation、future work、failure、constraint、risk 等限制/风险证据页；
- 避开明显图注页；
- 使用词边界匹配，避免 substring 误判；
- 没有命中时回退到非图注正文页；
- 输出仍然明确要求人工复查。

### 已完成文件

修改核心模块：

- `paperforge/deep_note_writer.py`

新增测试：

- `tests/test_deep_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 将 Limitations 加入 Deep Note Writer 的目标章节；
- 只在 readiness table 标记为 `ready` 时写入 Limitations；
- Limitations 输出 primary limitation evidence pages；
- Limitations 输出 page-level limitation evidence；
- Limitations 不要求 `images/manifest.md`；
- 使用词边界匹配减少 substring 误选；
- Deep Q&A 和 Practical Takeaways 仍然保持 `Not generated yet.`。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 37 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_deep_note_mvp completed
```

真实样例中，Limitations 写入了 page 2、page 7 的限制/约束证据。Deep Q&A 和 Practical Takeaways 仍保持 `Not generated yet.`。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- Deep Q&A 自动生成；
- Practical Takeaways 自动生成；
- 代码到论文方法的真实映射；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Deep Note Writer Deep Q&A MVP**：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 从已写入的 Core Method、Experiments、Limitations 证据草稿派生问题
  -> 保留 page evidence、问题来源章节和人工复查标记
```

Deep Q&A 不应该直接从 PDF 泛泛生成问题，而应该依赖已经写入主笔记的方法、实验和限制证据草稿。

## Step 18: Deep Note Writer Deep Q&A MVP

### 目标

在 Core Method、Experiments、Limitations 已经能写入保守证据草稿后，继续保守扩展到 Deep Q&A：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只处理 readiness 允许的 Deep Q&A
  -> 从 Core Method、Experiments、Limitations 证据草稿派生问题
  -> 更新 notes/README.md
  -> 保留来源章节、page evidence 和人工复查标记
```

本阶段仍然不生成 Practical Takeaways、Code Mapping 或 Interview Project Mapping，也不直接从 PDF 泛泛生成开放问题。

### 为什么这样做

Deep Q&A 应该服务后续学习复盘，而不是凭空提出看似合理的问题。当前已有 Core Method、Experiments、Limitations 的 evidence-grounded seed，因此 Deep Q&A 可以先做确定性派生：

- Deep Note Planner 在 evidence map 和 image manifest 可用时，允许 Deep Q&A 进入写入阶段；
- Deep Note Writer 先按顺序写入 Core Method、Experiments、Limitations；
- Deep Q&A 从这些已写入章节中抽取页码证据；
- 每个问题标明来源章节和 page；
- 输出仍然明确要求人工复查。

### 已完成文件

修改核心模块：

- `paperforge/deep_note_planner.py`
- `paperforge/deep_note_writer.py`

新增测试：

- `tests/test_deep_note_planner.py`
- `tests/test_deep_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- Deep Note Planner 将 Deep Q&A 标记为 ready，前提是 PDF text evidence map 和 image manifest 都存在；
- Deep Note Writer 将 Deep Q&A 加入目标章节；
- Deep Q&A 从 Core Method、Experiments、Limitations 的 page evidence 派生问题；
- Deep Q&A 输出来源章节和页码；
- Practical Takeaways 仍然保持 `Not generated yet.`。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 38 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_deep_note_mvp completed
```

真实样例中，Deep Q&A 生成了 3 个来源问题，分别引用 Core Method page 2、Experiments page 6、Limitations page 2。Practical Takeaways 仍保持 `Not generated yet.`。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- Practical Takeaways 自动生成；
- 代码到论文方法的真实映射；
- 自动抽取和解释术语；
- 自动生成疑难点；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Deep Note Writer Practical Takeaways MVP**：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 从已写入的 Core Method、Experiments、Limitations、Deep Q&A 证据草稿派生 takeaways
  -> 保留来源章节、page evidence 和人工复查标记
```

Practical Takeaways 不应该直接变成完整项目建议；面试项目适配度仍然应交给后续 Interview Mapper 阶段。

## Step 19: Deep Note Writer Practical Takeaways MVP

### 目标

在 Core Method、Experiments、Limitations 和 Deep Q&A 已经能写入保守证据草稿后，继续保守扩展到 Practical Takeaways：

```text
notes/deep-note-plan.md + notes/evidence-map.md + notes/README.md
  -> 只处理 readiness 允许的 Practical Takeaways
  -> 从 Core Method、Experiments、Limitations、Deep Q&A 证据草稿派生 takeaways
  -> 更新 notes/README.md
  -> 保留来源章节、page evidence 和人工复查标记
```

本阶段仍然不生成 Code Mapping、Interview Project Mapping 或完整项目建议，也不判断论文是否适合做面试项目。

### 为什么这样做

Practical Takeaways 容易被写成“项目方案”或“落地建议”，这会越过当前证据边界。当前系统只有页码级 evidence map、图片 manifest 和前面章节的保守草稿，还没有代码仓库证据、项目约束或适配度判断。

所以 Step 19 只做学习型 takeaway：

- 从 Core Method 提醒后续解释应绑定方法证据；
- 从 Experiments 提醒后续实践结论必须先核对实验度量；
- 从 Limitations 提醒应用前要检查限制和风险；
- 从 Deep Q&A 提醒先回答生成的问题，再转成项目或面试表述；
- 输出明确标注这些 takeaways 是 evidence prompts，不是 project recommendations。

### 已完成文件

修改核心模块：

- `paperforge/deep_note_planner.py`
- `paperforge/deep_note_writer.py`

新增测试：

- `tests/test_deep_note_planner.py`
- `tests/test_deep_note_writer.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- Deep Note Planner 在 PDF text evidence map 和 image manifest 都存在时，将 Practical Takeaways 标记为 ready；
- Deep Note Writer 将 Practical Takeaways 加入目标章节；
- Practical Takeaways 从 Core Method、Experiments、Limitations 的 page evidence 派生学习型 takeaway；
- Practical Takeaways 读取 Deep Q&A 生成状态，提醒先回答问题再转成项目或面试表述；
- Practical Takeaways 输出来源章节和页码；
- 输出明确保留人工复查标记，并说明不是项目建议。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 39 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
真实样例: https://arxiv.org/abs/1706.03762 -> note.write_deep_note_mvp completed
```

真实样例中，Practical Takeaways 从 Core Method、Experiments、Limitations 和 Deep Q&A 派生学习型 takeaway，不生成项目建议或适配度判断。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动抽取和解释术语；
- 自动生成疑难点；
- 代码到论文方法的真实映射；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Terminology Evidence MVP**：

```text
notes/evidence-map.md + notes/README.md + notes/terminology.md
  -> 从 evidence map 和 README 的保守证据草稿中抽取候选术语
  -> 只写入有页码证据的术语条目
  -> 保留 first seen page、来源章节和人工复查标记
```

这一步仍然不应该生成完整术语百科，也不应该从标题或摘要机械列词。

## Step 20: Terminology Evidence MVP

### 目标

在主笔记已经有保守证据草稿后，继续扩展术语库：

```text
notes/evidence-map.md + notes/README.md + notes/terminology.md
  -> 从 README 的 page evidence 行抽取术语候选
  -> 用 evidence-map 校验 page evidence 存在
  -> 更新 notes/terminology.md
  -> 保留 first seen page、来源章节和人工复查标记
```

本阶段仍然不生成完整术语百科，也不从论文标题、摘要或无页码内容中机械列词。

### 为什么这样做

术语库应该服务学习复盘，但如果直接从标题或摘要中抓名词，会很容易生成看似有用但没有证据定位的词表。当前项目已经有 `notes/evidence-map.md` 和 `notes/README.md` 的证据草稿，所以 Step 20 只做一个可验证的最小版本：

- 只读取 README 中 `Page N ... evidence` 格式的证据行；
- 只写入 evidence map 中存在的页码；
- 写入候选术语、来源章节和 first seen page；
- 不自动写完整解释，只标注 human explanation required；
- Practical Takeaways 这类没有 `Page N ... evidence` 的提示行不会成为术语来源。
- 抽取规则需要过滤句子碎片，避免把 `Introduction Recurrent`、`per-layer complexity and`、`state-of-the-art models on` 这类上下文片段当成术语。

### 已完成文件

修改核心模块：

- `paperforge/terminology_agent.py`

修改工作台和脚本：

- `app.py`
- `scripts/run_pipeline.py`

新增测试：

- `tests/test_terminology_agent.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 保留 `run_terminology_scaffold` 的骨架生成行为；
- 新增 `run_terminology_evidence`，作为独立 evidence writer；
- 缺少 `notes/evidence-map.md`、`notes/README.md` 或 `notes/terminology.md` 时返回 `partial`；
- 从 README 的页码证据行抽取候选术语；
- 用 evidence map 校验页码，避免写入无证据术语；
- 写入 `notes/terminology.md`，每个术语包含 Category、Short explanation、Why it matters、Related terms、First seen in 和 Follow-up reading；
- 将 `knowledge.write_terminology_evidence` 写入 timeline 和 artifacts；
- Streamlit 增加 `Write Terminology Evidence` 按钮；
- 真实流水线在 deep note writing 后继续执行 terminology evidence。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 42 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
真实样例: https://arxiv.org/abs/1706.03762 -> knowledge.write_terminology_evidence completed
```

真实样例中，`notes/terminology.md` 写入了带 first seen page 和来源章节的术语候选，并保留人工复查标记。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动生成完整术语解释；
- 自动生成疑难点；
- 代码到论文方法的真实映射；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Doubts Evidence MVP**：

```text
notes/README.md + notes/terminology.md + notes/doubts.md
  -> 从方法、实验、限制、Deep Q&A、Practical Takeaways 和术语条目派生疑难点
  -> 保留来源章节、page evidence 和人工复查标记
  -> 更新 notes/doubts.md
```

这一步仍然不应该泛泛生成开放问题，也不应该把未验证的问题包装成最终结论。

## Step 21: Doubts Evidence MVP

### 目标

在主笔记和术语库已经有 evidence-backed 草稿后，继续扩展疑难点文件：

```text
notes/README.md + notes/terminology.md + notes/doubts.md
  -> 从已有证据草稿派生疑难点候选
  -> 更新 notes/doubts.md
  -> 保留来源章节、page evidence 和人工复查标记
```

本阶段仍然不生成完整疑难点百科，也不直接从 PDF 泛泛生成开放问题。

### 为什么这样做

疑难点文件应该帮助后续复盘，但如果没有证据边界，很容易变成通用问题清单。Step 21 只利用已经落盘并经过前面阶段约束的材料：

- `notes/README.md` 中 Core Method、Experiments、Limitations 和 Deep Q&A 的证据草稿；
- `notes/terminology.md` 中有 first seen page 的术语候选；
- `notes/doubts.md` 的既有结构。

因此输出的是可追溯的 question seed，而不是最终阅读结论。

### 已完成文件

修改核心模块：

- `paperforge/doubts_agent.py`

修改工作台和脚本：

- `app.py`
- `scripts/run_pipeline.py`

新增测试：

- `tests/test_doubts_agent.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/AI_LEARNING_PROMPT.md`
- `docs/self/learn.md`

### 当前能力

已支持：

- 保留 `run_doubts_scaffold` 的骨架生成行为；
- 新增 `run_doubts_evidence`，作为独立 evidence writer；
- 缺少 `notes/README.md`、`notes/terminology.md` 或 `notes/doubts.md` 时返回 `partial`；
- 从 README 的页码证据行读取方法、实验和限制证据；
- 从 README 的 Deep Q&A 章节复用已有来源问题；
- 从 terminology first-seen 条目生成术语 follow-up question；
- 写入 Open Questions、Confusing Formulas、Missing Implementation Details、Claims That Need Verification 和 Terminology Questions；
- 将 `knowledge.write_doubts_evidence` 写入 timeline 和 artifacts；
- Streamlit 增加 `Write Doubts Evidence` 按钮；
- 真实流水线在 terminology evidence 后继续执行 doubts evidence。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行真实流水线：

```powershell
uv run python scripts/run_pipeline.py https://arxiv.org/abs/1706.03762 https://github.com/harvardnlp/annotated-transformer
```

当前验证结果：

```text
pytest: 44 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
真实样例: https://arxiv.org/abs/1706.03762 -> knowledge.write_doubts_evidence completed
```

真实样例中，`notes/doubts.md` 写入了来自 Core Method、Experiments、Limitations、Deep Q&A 和 terminology 条目的疑难点候选，并保留来源章节、page evidence 和人工复查标记。

实现后修复过一个质量问题：

- Doubts Evidence 初版会把 Experiments 和 Limitations 来源的问题也标成 `Method question`；已改为按来源章节输出 `Method question`、`Experiment question` 或 `Limitation question`，并增加回归测试。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动生成完整疑难点解释；
- 代码到论文方法的真实映射；
- 自动判断面试项目适配度；
- RAG / 向量检索。

### 下一步建议

下一步建议做 **Code Mapping Evidence MVP**：

```text
notes/code-references.md + notes/README.md + optional code repo
  -> 在用户确认后读取或 clone 候选仓库
  -> 把论文方法点映射到具体代码文件或路径
  -> 更新 notes/code-references.md
```

这一步涉及第三方仓库读取或 clone，需要用户确认仓库来源和读取方式后再做。

## Step 22: Code Mapping Evidence MVP

### 目标

在不自动 clone 第三方仓库的前提下，给 `notes/code-references.md` 增加一个可追溯的代码映射证据入口：

```text
notes/code-references.md + notes/README.md + user-provided local code repo
  -> 扫描本地代码文件
  -> 按 Core Method 方法词重合度生成候选代码路径
  -> 更新 notes/code-references.md
```

本阶段只做文件级候选映射，不声明行级实现位置，也不把词面匹配包装成真实语义理解。

### 为什么这样做

前一阶段已经生成主笔记、术语和疑难点证据草稿。继续往面试项目映射走之前，需要先把论文方法和代码资产之间建立最小证据桥。

但自动 clone 仓库会扩大 scope，也可能遇到仓库过大、license 不清楚或访问权限问题。因此 Step 22 采用更保守的方式：

- 用户明确提供本地代码仓库路径；
- PaperForge 只扫描这个本地目录；
- 缺少本地路径时返回 `needs_user_input`；
- 输出只作为候选阅读路径，需要人工复查。

### 已完成文件

修改核心模块：

- `paperforge/code_linker.py`

修改工作台和脚本：

- `app.py`
- `scripts/run_pipeline.py`

新增测试：

- `tests/test_code_linker.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`

### 当前能力

已支持：

- 保留 `run_code_linking` 的候选仓库整理行为；
- 新增 `run_code_mapping_evidence`，作为独立 evidence writer；
- 读取 `notes/code-references.md` 和 `notes/README.md`；
- 从 `notes/README.md` 的 Core Method 章节提取方法证据词；
- 扫描用户提供的本地代码目录，过滤常见依赖、构建和缓存目录；
- 只读取常见代码文件扩展名，并限制文件数量和文件大小；
- 按方法词在路径和内容中的重合度排序候选代码文件；
- 更新 `notes/code-references.md` 的 `Code Mapping Evidence` 章节；
- 没有本地代码路径时将 `code.map_evidence` 标记为 `needs_user_input`；
- Streamlit 增加 `Write Code Mapping Evidence` 按钮和本地代码路径输入框；
- 真实流水线脚本支持通过 `PAPERFORGE_CODE_REPO` 环境变量启用本阶段，默认跳过。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 46 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

单元样例中，本地代码目录里的 `models/attention.py` 能根据 Core Method 中的 `attention`、`encoder` 等方法证据词写入 `notes/code-references.md`。缺少本地代码目录时，step 返回 `needs_user_input`，不会自动 clone。

### 这一阶段没有做什么

这些能力继续留到后续步骤：

- 自动 clone 仓库；
- 读取远端仓库文件；
- license 自动判断；
- 行级方法到代码映射；
- 语义级代码理解；
- 自动判断面试项目适配度。

### 下一步建议

下一步建议做 **Interview Project Mapping Assessment MVP**：

```text
notes/README.md + notes/code-references.md + notes/doubts.md + notes/interview-project.md
  -> 判断论文是否适合作为面试项目素材
  -> 输出 high / medium / low 适配度
  -> 给出最小 demo 范围和人工复查风险
  -> 更新 notes/interview-project.md
```

这一步仍然应该基于已有证据输出保守判断，不直接生成完整项目方案。

## Step 23: Interview Project Mapping Assessment MVP

### 目标

在代码映射、主笔记和疑难点证据已经具备后，继续更新 `notes/interview-project.md`：

```text
notes/README.md + notes/code-references.md + notes/doubts.md + notes/interview-project.md
  -> 判断论文是否适合作为面试项目素材
  -> 输出 high / medium / low / not recommended
  -> 给出最小 demo 范围、技术亮点和风险
  -> 更新 notes/interview-project.md
```

本阶段只做 assessment MVP，不生成完整项目方案、不承诺可直接用于面试。

### 为什么这样做

PaperForge 的核心目标之一是把论文研究转成面试项目素材。但如果直接生成完整项目方案，很容易越过当前证据边界。当前已经有：

- 主笔记中的方法、实验、限制和 practical takeaway 证据；
- `notes/code-references.md` 中的代码候选或文件级映射；
- `notes/doubts.md` 中的疑难点和风险；
- `notes/interview-project.md` 的结构化模板。

所以 Step 23 只做一个保守判断：这篇论文目前更像 high、medium、low 还是 not recommended 的面试项目候选，并说明最小 demo 应该如何收窄。

### 已完成文件

修改核心模块：

- `paperforge/interview_mapper.py`

修改工作台和脚本：

- `app.py`
- `scripts/run_pipeline.py`

新增测试：

- `tests/test_interview_mapper.py`

更新文档：

- `README.md`
- `docs/PROJECT_GUIDE.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`

### 当前能力

已支持：

- 保留 `run_interview_mapping_scaffold` 的骨架生成行为；
- 新增 `run_interview_mapping_assessment`，作为独立 assessment writer；
- 读取 `notes/README.md`、`notes/code-references.md`、`notes/doubts.md` 和 `notes/interview-project.md`；
- 根据信号输出 high / medium / low / not recommended：
  - Core Method page evidence；
  - Experiments page evidence；
  - Practical Takeaways 是否生成；
  - Code Mapping Evidence 是否来自本地扫描；
  - Doubts / Limitations 是否存在风险信号；
- 写入 Suitability、Why This Can Become a Project、Why This May Not Be Worth Building、Minimal Demo Version、Full Version、Technical Highlights、Risks、Connection to Existing Projects 和 Interview Talking Points；
- 缺少输入时返回 `partial`；
- Streamlit 增加 `Assess Interview Project` 按钮；
- 真实流水线脚本在 doubts evidence 和可选 code mapping evidence 后执行 interview assessment。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 48 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

单元样例中，当 `notes/README.md` 有方法、实验、限制和 practical takeaway 证据，且 `notes/code-references.md` 有本地代码映射时，`notes/interview-project.md` 会写入 `Suitability: high`、最小 demo 范围、代码证据和风险边界。缺少 code references 或 doubts 时，step 返回 `partial`。

### 这一阶段没有做什么

这些能力继续留到后续扩展：

- 完整项目方案生成；
- 自动生成项目代码；
- 自动 clone 第三方仓库；
- 行级代码映射；
- 完整深度论文解释；
- RAG / 向量检索；
- 多篇论文批处理。

### 下一步建议

核心 MVP 已完成。扩展路线已经单独整理到 `docs/EXTENSION_ROADMAP.md`。

```text
docs/EXTENSION_ROADMAP.md
```

如果继续学习和面试包装，优先建议做段落级 evidence map，因为它能直接提高后续深度笔记、术语解释和项目评估的证据质量。

## 2026-05-24: Extension 0 需求文档化

### 目标

根据最新需求，把两个后续扩展整理成可执行文档和可复制提示词：

```text
用户输入简称
  -> LLM Query Planner 先判断真正目标论文
  -> 生成 canonical title / search query
  -> 再查 arXiv
```

```text
PaperForge job artifacts
  -> notes/ai-paper-reader-prompt.md
  -> 另一个 Codex 对话读取 ai-paper-reader SKILL.md
  -> 生成专业阅读笔记
```

### 为什么这样做

当前 intake 直接搜索标题，遇到 `unet` 这类简称时容易拿到 U-Net 变体，而不是原始论文 `U-Net: Convolutional Networks for Biomedical Image Segmentation`。

同时，`ai-paper-reader` 是 Codex skill，不是 PaperForge Python 包。第一版更稳的接入方式是生成 prompt pack，明确要求另一个 Codex 对话读取：

```text
C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md
```

### 已完成文件

新增文档：

- `docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md`
- `docs/PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md`

更新文档：

- `README.md`
- `docs/EXTENSION_ROADMAP.md`
- `docs/PROGRESS.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/PROJECT_GUIDE.md`
- `docs/STATUS_REVIEW.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/BUILD_STEPS.md`

### 当前能力

本阶段只完成文档和提示词，没有改 Python 运行时代码。

文档已经明确：

- Extension 0 排在段落级 evidence map 之前；
- `unet` / `u-net` / `u net` 应稳定解析到原始 U-Net 论文；
- 第一版 query planner 需要 fallback 和确定性别名表；
- 第一版 `ai-paper-reader` 接入生成 `notes/ai-paper-reader-prompt.md`，不直接导入或调用本地 Codex skill。

### 验证方式

运行 diff 空白检查：

```powershell
git diff --check
```

这次是文档阶段，不需要运行 pytest。

## Step 24: LLM Query Planner 与 ai-paper-reader Prompt Pack

### 目标

把 Extension 0 从文档落到 Python + Streamlit 运行时：

```text
用户输入 unet / u-net / u net
  -> query planner 识别为原始 U-Net 论文
  -> arXiv 使用 canonical title 查询
  -> notes/query-plan.md 记录规划过程
```

```text
PaperForge job artifacts
  -> notes/ai-paper-reader-prompt.md
  -> 另一个 Codex 对话读取 ./docs/PAPER_SKILL.md
  -> 按 ai-paper-reader 结构继续写专业阅读笔记
```

### 为什么这样做

当前直接把用户输入交给 arXiv 标题搜索，遇到简称或俗称时容易找错论文。先做 query planning 可以把入口意图记录下来，也能让 fallback 行为可复盘。

`ai-paper-reader` 是 Codex skill，不是 PaperForge Python 包。第一版不在 Streamlit 内直接调用 skill，而是生成 prompt pack，让另一个 Codex 对话明确读取 `./docs/PAPER_SKILL.md` 和 canonical skill 路径。

### 已完成文件

新增核心模块：

- `paperforge/query_planner.py`
- `paperforge/ai_paper_reader_prompt.py`

修改 workflow 和工作台：

- `paperforge/intake_agent.py`
- `app.py`

新增测试：

- `tests/test_query_planner.py`
- `tests/test_ai_paper_reader_prompt.py`

更新文档：

- `README.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/PROGRESS.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- `QueryPlan` 数据结构；
- `QueryPlannerClient` 可注入接口；
- `plan_paper_query(raw_input, client=None)`；
- `write_query_plan_markdown(...)` 写入 `notes/query-plan.md`；
- `unet`、`u-net`、`u net` 确定性解析到 `U-Net: Convolutional Networks for Biomedical Image Segmentation`；
- author hint 记录为 `Ronneberger`，year hint 记录为 `2015`；
- arXiv ID、arXiv URL 和 PDF URL 不交给 LLM 改写；
- fake LLM 返回合法 JSON 时使用 canonical title / search query；
- fake LLM 返回空、坏 JSON 或异常时 fallback；
- intake workflow 在 arXiv 查询前增加 `query.plan_paper_identity`；
- Streamlit intake 区域增加 `Use LLM query planner` 复选框；
- `run_ai_paper_reader_prompt_pack(job)` 生成 `notes/ai-paper-reader-prompt.md`；
- Prompt 明确要求另一个 Codex 对话读取 `./docs/PAPER_SKILL.md`，并记录 canonical skill 路径；
- Prompt 写入 metadata、PDF、README、evidence map、image manifest 的绝对路径；
- 缺少 PDF、evidence map 或 image manifest 时仍生成 prompt，并标注 missing；
- 将 `note.prepare_ai_paper_reader_prompt` 写入 timeline，artifact label 为 `AI Paper Reader Prompt`。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 62 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有接入真实 OpenAI API 或其他 LLM provider；
- 没有把 Codex skill 当 Python 包导入；
- 没有生成完整自动论文报告；
- 没有引入 React、TypeScript、Express 或前后端分离框架。

### 下一步建议

下一步建议做 **Extension 1: 段落级 Evidence Map**：

```text
raw/paper.pdf + notes/evidence-map.md
  -> paragraph / chunk 级证据
  -> 后续 RAG、深度解释、术语解释和疑难点分析的更细来源定位
```

## Step 25: LLM Provider Config + ai-paper-reader Note Generation

### 目标

把 Step 24 的 handoff prompt 扩展成真正的 LLM 执行层：

```text
DeepSeek OpenAI-compatible config
  -> query planner 使用 deepseek-v4-flash
  -> ai-paper-reader note writer 使用 deepseek-v4-pro
  -> notes/ai-paper-reader-note.md
```

### 为什么这样做

Prompt Pack 只能把资料交给另一个 Codex 对话，不能算应用内自动生成论文笔记。当前阶段把 `docs/PAPER_SKILL.md` 接入真实 LLM 调用，但仍然保持几个边界：

- API key 从项目根目录 `.env` 或系统环境变量读取，不写入仓库、job 或 notes；
- 远端 LLM 不能直接打开本地 PDF，所以 prompt 重点使用 `notes/evidence-map.md`、`notes/README.md` 和 `images/manifest.md`；
- 测试仍然使用 fake client，不调用真实 DeepSeek，也不消耗额度。

### 已完成文件

新增核心模块：

- `paperforge/llm_client.py`
- `paperforge/ai_paper_reader_note.py`

修改核心模块和工作台：

- `paperforge/query_planner.py`
- `app.py`

新增测试：

- `tests/test_llm_client.py`
- `tests/test_ai_paper_reader_note.py`
- `tests/test_query_planner.py`

更新配置和文档：

- `.env.example`
- `README.md`
- `docs/PROGRESS.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- OpenAI-compatible `/chat/completions` 调用；
- 自动读取项目根目录 `.env`，并从 `.env` 或系统环境变量读取：
  - `PAPERFORGE_LLM_BASE_URL`
  - `PAPERFORGE_LLM_API_KEY`
  - `PAPERFORGE_QUERY_MODEL`
  - `PAPERFORGE_READER_MODEL`
  - `PAPERFORGE_LLM_TIMEOUT_SECONDS`
- `LlmConfig.__repr__` 隐藏 API key；
- query planner 在没有显式 fake client 且环境变量配置完整时使用 `PAPERFORGE_QUERY_MODEL`；
- 仍保留 deterministic alias 和 fallback；
- `run_ai_paper_reader_note_generation(job)` 读取 `docs/PAPER_SKILL.md` 和 job artifacts；
- 生成 `notes/ai-paper-reader-note.md`；
- 保存 `notes/ai-paper-reader-generation-prompt.md`；
- 缺少 LLM 配置时 step 为 `needs_user_input`；
- 缺少 PDF、evidence map 或 image manifest 时仍可生成，但 step 为 `partial`；
- Streamlit 增加 `Generate ai-paper-reader Note` 按钮。

### 配置方式

PowerShell 示例：

```powershell
$env:PAPERFORGE_LLM_BASE_URL="https://api.deepseek.com"
$env:PAPERFORGE_LLM_API_KEY="<your-deepseek-api-key>"
$env:PAPERFORGE_QUERY_MODEL="deepseek-v4-flash"
$env:PAPERFORGE_READER_MODEL="deepseek-v4-pro"
```

不要把真实 API key 写入 git。

也可以直接写入本地 `.env`，该文件已被 `.gitignore` 忽略：

```text
PAPERFORGE_LLM_BASE_URL=https://api.deepseek.com
PAPERFORGE_LLM_API_KEY=<your-deepseek-api-key>
PAPERFORGE_QUERY_MODEL=deepseek-v4-flash
PAPERFORGE_READER_MODEL=deepseek-v4-pro
```

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果会在本轮最终验证后记录。
当前验证结果：

```text
pytest: 73 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有在测试中调用真实 DeepSeek；
- 没有上传 PDF 文件给模型；
- 没有把 API key 写入 `.env` 或任何 tracked 文件；
- 没有引入 React、TypeScript、Express 或前后端分离框架。

### 下一步建议

下一步仍建议做 **Extension 1: 段落级 Evidence Map**。现在有真实 LLM 生成能力后，更细的 paragraph / chunk evidence 会直接提升生成质量和可核查性。

## Step 26: Paragraph / Chunk-level Evidence Map

### 目标

把已有的页码级证据文件继续细化：

```text
notes/evidence-map.md
  -> 解析 Page 1 / Page 2 等 page excerpt
  -> 按 paragraph 或合理长度切成 chunk
  -> notes/evidence-chunks.md
```

本阶段只做证据切分，不重新解析 PDF，不总结论文，不生成论文解释。

### 为什么这样做

前一阶段已经能生成 `notes/evidence-map.md`，但它只有页码级 excerpt。后续 RAG、深度解释、术语解释和疑难点分析需要更精确的来源定位，否则只能引用整页，证据粒度太粗。

Step 26 先用确定性规则把 page excerpt 切成 chunk：

- 复用现有 evidence map，不扩大 PDF 解析 scope；
- 每个 chunk 有稳定 id，例如 `p001-c001`；
- 保留 page、section guess、字符数和文本 excerpt；
- 缺少 evidence-map 或页面无文本时返回 partial，不阻塞 job。

### 已完成文件

新增核心模块：

- `paperforge/evidence_chunker.py`

修改核心模块和工作台：

- `paperforge/models.py`
- `app.py`
- `scripts/run_pipeline.py`

新增测试：

- `tests/test_evidence_chunker.py`

更新文档：

- `README.md`
- `docs/PROGRESS.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/EXTENSION_ROADMAP.md`
- `docs/STATUS_REVIEW.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 读取 `notes/evidence-map.md`；
- 解析 `### Page N` 下的 fenced text excerpt；
- 按空行切分 paragraph；
- 对过长 paragraph 按合理长度切分；
- 合并短 section heading 和后续正文；
- 生成稳定 chunk id：`p001-c001`、`p001-c002`；
- 为 chunk 标注 `introduction`、`method`、`experiment`、`limitation` 或 `unknown`；
- 生成 `notes/evidence-chunks.md`；
- Markdown 输出包含 chunk inventory 和 chunk evidence sections；
- 缺少 `notes/evidence-map.md` 时写 partial report；
- 有空页或没有 chunk 时标记 `partial`；
- 将 `pdf.extract_evidence_chunks` 写入 timeline；
- artifact label 为 `Evidence chunks`；
- Streamlit 增加 `Extract Evidence Chunks` 按钮；
- 真实流水线脚本在 PDF text evidence 后执行 evidence chunk extraction。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 77 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有重新解析 PDF；
- 没有做 OCR；
- 没有做 embedding 或向量数据库；
- 没有生成论文解释或总结；
- 没有修改 ai-paper-reader、terminology 或 doubts 的证据读取逻辑，这些留到后续 Step 28/29。

### 下一步建议

下一步建议做 **Step 27: RAG / 本地检索 MVP**：

```text
user query + notes/evidence-chunks.md
  -> deterministic keyword scoring
  -> notes/evidence-search.md
  -> 返回 chunk id、page、score、excerpt
```

## Step 27: RAG / 本地检索 MVP

### 目标

基于 Step 26 的 `notes/evidence-chunks.md` 做第一版本地检索：

```text
user query + notes/evidence-chunks.md
  -> deterministic keyword retrieval
  -> notes/evidence-search.md
```

本阶段不做向量数据库、不引入复杂依赖，也不生成答案。输出只是 evidence candidates。

### 为什么这样做

有了 paragraph / chunk 级证据后，需要先验证 chunks 能不能被稳定检索到。直接上 embedding 或语义检索会扩大 scope；第一版用确定性关键词评分即可覆盖演示和测试：

- 查询 method 相关词能命中 method chunk；
- 查询 experiment 相关词能命中 experiment chunk；
- 输出必须带 chunk id、page、score 和 excerpt；
- 缺少 chunks 文件时返回 partial，不阻塞 job。

### 已完成文件

新增核心模块：

- `paperforge/evidence_retriever.py`

修改核心模块和工作台：

- `paperforge/models.py`
- `app.py`
- `scripts/run_pipeline.py`

新增测试：

- `tests/test_evidence_retriever.py`

更新文档：

- `README.md`
- `docs/PROGRESS.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/EXTENSION_ROADMAP.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 解析 `notes/evidence-chunks.md` 的 chunk blocks；
- 输入用户查询；
- 使用确定性关键词匹配 / BM25-like 简单评分；
- 返回 chunk id、page、section guess、score 和 excerpt；
- 按分数降序、页码和 chunk id 稳定排序；
- 生成 `notes/evidence-search.md`；
- 缺少 `notes/evidence-chunks.md` 时写 partial report；
- 空查询时返回 `needs_user_input`；
- 将 `evidence.search_chunks` 写入 timeline；
- artifact label 为 `Evidence search results`；
- Streamlit 增加 `Evidence search query` 输入框和 `Search Evidence Chunks` 按钮；
- 真实流水线脚本支持 `PAPERFORGE_EVIDENCE_QUERY`，默认使用 `method experiment`。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 81 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有做 embedding；
- 没有做向量数据库；
- 没有做跨论文检索；
- 没有把检索结果包装成论文回答；
- 没有修改 ai-paper-reader、terminology 或 doubts 的 evidence chunk 使用逻辑。

### 下一步建议

下一步建议做 **Step 28: ai-paper-reader Note 使用 Evidence Chunks**：

```text
notes/evidence-chunks.md + notes/evidence-map.md
  -> ai-paper-reader generation prompt 优先包含 chunks excerpt
  -> 缺失 chunks 时 fallback 到 evidence-map
```

## Step 28: ai-paper-reader Note 使用 Evidence Chunks

### 目标

让 `notes/ai-paper-reader-note.md` 的生成 prompt 优先使用 Step 26 产出的 `notes/evidence-chunks.md`：

```text
notes/evidence-chunks.md + docs/PAPER_SKILL.md + job artifacts
  -> notes/ai-paper-reader-generation-prompt.md
  -> notes/ai-paper-reader-note.md
```

本阶段只改变 ai-paper-reader note generation 的 evidence 输入优先级，不改变 API key 管理方式，不扩大到 terminology / doubts。

### 为什么这样做

Step 27 已经验证 `notes/evidence-chunks.md` 可以被本地关键词检索命中。ai-paper-reader note generation 如果仍主要使用页码级 `notes/evidence-map.md`，LLM 只能引用粗粒度 page excerpt。Step 28 把更细的 chunk evidence 放进 generation prompt：

- chunks 存在时优先携带 chunk excerpt 和 chunk id；
- chunks 缺失时保持 `notes/evidence-map.md` fallback；
- prompt 明确要求优先引用 chunk id；
- 无法从 chunk 验证的内容必须标注为待核查；
- 不允许凭模型记忆补全论文细节。

### 已完成文件

修改核心模块：

- `paperforge/ai_paper_reader_note.py`

更新测试：

- `tests/test_ai_paper_reader_note.py`

更新文档：

- `README.md`
- `docs/PROGRESS.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/EXTENSION_ROADMAP.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- `notes/evidence-chunks.md` 存在时，generation prompt 包含该文件路径和截断后的 chunk excerpt；
- `notes/evidence-chunks.md` 缺失时，自动 fallback 到 `notes/evidence-map.md`；
- artifact inventory 只把当前实际使用的 primary evidence 文件标为 present；
- prompt 要求优先引用 `p001-c001` 这类 chunk id；
- prompt 要求无法从 chunk 验证的内容标注为待核查；
- prompt 要求不得仅凭模型记忆补全论文细节；
- prompt 截断策略保留，不把完整超长 chunks 文件塞入 LLM 请求；
- API key 仍只从 `.env` 或系统环境变量读取，不写入 job、notes 或 prompt 文件。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 83 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有修改 LLM API key 读取方式；
- 没有把完整超长 chunks 文件无截断塞入 prompt；
- 没有改 terminology / doubts 的 evidence 派生逻辑；
- 没有生成完整深度论文解释；
- 没有引入向量数据库或新依赖。

### 下一步建议

下一步建议做 **Step 29: Terminology / Doubts 使用 Evidence Chunks**：

```text
notes/evidence-chunks.md
  -> terminology candidates with chunk id + page
  -> doubts candidates with chunk id + page
```

## Step 29: Terminology / Doubts 使用 Evidence Chunks

### 目标

让术语候选和疑难点候选优先使用 Step 26 产出的 `notes/evidence-chunks.md`：

```text
notes/evidence-chunks.md
  -> notes/terminology.md with chunk id + page
  -> notes/doubts.md with chunk id + page
```

本阶段不生成完整术语解释，不生成完整疑难点分析，只把 evidence source 从粗页码优先升级为 chunk id/page 优先。

### 为什么这样做

Step 28 已经让 ai-paper-reader note generation 优先携带 chunk evidence，但 terminology 和 doubts 仍主要从 README 的页码证据行派生。这样来源粒度不够细，也不利于后续 RAG 或人工复查。Step 29 保持原有 fallback，同时在 chunks 存在时改用更精确来源：

- terminology 从 chunk excerpt 抽取候选术语；
- doubts 从 method、experiment、limitation chunks 派生问题；
- 每条 chunk-backed 输出保留 chunk id 和 page；
- chunks 缺失时旧的 README + evidence-map 逻辑仍可用。

### 已完成文件

修改核心模块：

- `paperforge/terminology_agent.py`
- `paperforge/doubts_agent.py`

更新测试：

- `tests/test_terminology_agent.py`
- `tests/test_doubts_agent.py`

更新文档：

- `README.md`
- `docs/PROGRESS.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/EXTENSION_ROADMAP.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- `notes/evidence-chunks.md` 存在时，Terminology Agent 只从 chunk excerpt 抽取候选术语；
- terminology 输出 `notes/evidence-chunks.md`、chunk id、page 和 section guess；
- `notes/evidence-chunks.md` 缺失时，Terminology Agent fallback 到旧的 README + evidence-map 页码证据逻辑；
- `notes/evidence-chunks.md` 存在时，Doubts Agent 从 method、experiment、limitation chunks 派生 implementation / experiment / limitation questions；
- Doubts Agent 复用 chunk-backed terminology 条目生成术语 follow-up question；
- doubts 输出 chunk id 和 page；
- chunks 存在但没有可用术语或疑难点来源时返回 `partial`，不写入无 evidence 的候选；
- Streamlit 现有 `Write Terminology Evidence` 和 `Write Doubts Evidence` 按钮可直接复用。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 87 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有生成完整术语解释；
- 没有生成完整疑难点分析；
- 没有使用 LLM 生成 terminology/doubts；
- 没有引入 embedding 或向量数据库；
- 没有修改 code mapping 逻辑。

### 下一步建议

下一步建议做 **Step 30: Code Mapping Function-level MVP**：

```text
local code repo path
  -> scan Python function / class symbols
  -> notes/code-references.md symbol-level candidates
```

## Step 30: Code Mapping Function-level MVP

### 目标

在现有文件级代码映射基础上，增加 Python function / class 级候选映射：

```text
local code repo path + notes/README.md Core Method evidence
  -> scan Python functions/classes
  -> notes/code-references.md symbol-level candidates
```

本阶段仍然要求用户提供本地代码仓库路径；不自动 clone，不做语义理解，不声明真实实现对应。

### 为什么这样做

Step 22 的 code mapping 只能输出候选文件。对阅读论文和准备项目来说，文件级候选仍然偏粗；如果能标出可能相关的 Python function / class，用户可以更快进入人工复查。Step 30 选择 AST 解析 Python 文件，而不是字符串猜测或引入复杂依赖：

- 只扫描本地用户提供的 repo；
- 只识别 Python function / class symbol；
- 仍基于 Core Method 方法词做确定性匹配；
- confidence 只表示词面候选强弱；
- 输出明确标记为 candidate，不承诺真实实现对应。

### 已完成文件

修改核心模块：

- `paperforge/code_linker.py`

更新测试：

- `tests/test_code_linker.py`

更新文档：

- `README.md`
- `docs/PROGRESS.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/EXTENSION_ROADMAP.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 在用户提供本地代码仓库路径后扫描代码；
- 对 Python 文件使用 `ast` 识别 `class`、`def` 和 `async def`；
- 输出 symbol-level candidate，包含 file path、symbol name、symbol type、matched terms 和 confidence；
- 同时保留原有文件级 candidate；
- confidence 只分 `low` / `medium`，不伪装成真实语义匹配；
- 继续过滤 `.venv`、`venv`、`node_modules`、`.git`、`dist`、`build`、`__pycache__` 等目录；
- 缺少本地 repo 路径时仍返回 `needs_user_input`；
- Streamlit 现有 `Write Code Mapping Evidence` 按钮可复用。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 88 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有自动 clone 仓库；
- 没有扫描远端 GitHub；
- 没有做 line-level mapping；
- 没有做语义代码理解；
- 没有把 symbol candidate 包装成真实论文实现对应。

### 下一步建议

下一步建议做 **Step 31: 多篇论文批处理 MVP**：

```text
multi-line paper inputs
  -> sequential run_paper_intake
  -> .paperforge-data/batches/<batch-id>.json
```

## Step 31: 多篇论文批处理 MVP

### 目标

支持用户输入多行论文标题、arXiv ID 或 URL，顺序创建多个 intake jobs：

```text
multi-line paper inputs
  -> sequential run_paper_intake
  -> .paperforge-data/batches/<batch-id>.json
  -> .paperforge-data/batches/<batch-id>-summary.md
```

本阶段只做 batch intake，不做并发、不下载资产、不做跨论文综述总结。

### 为什么这样做

前面阶段已经把单篇论文 research package 的主要 scaffold 和 evidence workflow 跑通。多篇论文批处理的第一步不应该直接做综述或跨论文 RAG，而是先解决“多行输入顺序创建多个 jobs，并记录每篇状态”：

- 批处理失败项不能阻塞后续论文；
- batch summary 要能帮助用户重试失败项；
- 所有生成数据继续放在 `.paperforge-data/`；
- 不引入数据库或调度系统。

### 已完成文件

新增核心模块：

- `paperforge/batch_runner.py`

修改工作台：

- `app.py`

新增测试：

- `tests/test_batch_runner.py`

更新文档：

- `README.md`
- `docs/PROGRESS.md`
- `docs/WORKFLOW_SPEC.md`
- `docs/EXTENSION_ROADMAP.md`
- `docs/STATUS_REVIEW.md`
- `docs/DOCUMENTATION_GUIDE.md`
- `docs/BUILD_STEPS.md`

### 当前能力

已支持：

- 多行论文输入；
- 空行跳过；
- 每行顺序调用现有 `run_paper_intake`；
- 单篇异常会记录为 failed，并继续处理后续输入；
- batch JSON 记录 batch id、created_at、status、total_inputs 和每篇 input/job id/slug/status/error；
- batch Markdown summary 保存同样信息，方便人工查看；
- 空输入返回 `needs_user_input`；
- Streamlit 增加 Batch Intake 区域和 `Run Batch Intake` 按钮。

### 验证方式

运行测试：

```powershell
uv run python -m pytest
```

运行编译检查：

```powershell
uv run python -m compileall app.py paperforge tests scripts
```

运行 diff 空白检查：

```powershell
git diff --check
```

当前验证结果：

```text
pytest: 92 passed
compileall: app.py paperforge tests scripts passed
git diff --check: passed
```

### 这一阶段没有做什么

- 没有并发；
- 没有批量下载 PDF/TeX；
- 没有跨论文总结；
- 没有引入数据库；
- 没有改变单篇 intake 行为。

### 后续建议

当前 Step 26-31 请求清单已完成。下一轮建议先做真实样例验证、demo script / evaluation 文档，或者重新确认是否进入语义 / 向量检索扩展。
