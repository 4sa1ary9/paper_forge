# PaperForge Agent

**PaperForge Agent** 是一个用 Python 实现的 AI 论文研究 Agent。

它的目标不是再做一个“论文总结聊天框”，而是把一篇论文从零整理成一个可复用的研究工作区：

1. 自动识别论文标题、作者、摘要、PDF 地址和 TeX Source 地址。
2. 创建规范化论文目录，保存元信息和外部来源记录。
3. 用 timeline 记录 agent 每一步做了什么、产出了什么、哪里失败。
4. 下载 PDF 和 TeX Source，尝试解压论文源码。
5. 整理官方论文链接、本地资产状态和用户补充的外部资料 URL。
6. 从 PDF 提取图片并生成图片 manifest。
7. 记录 GitHub 代码仓库候选并生成 code references。
8. 生成论文笔记骨架，保留证据入口但不伪造深度解释。
9. 生成术语库骨架。
10. 生成疑难点骨架。
11. 生成面试项目映射骨架，保留项目判断入口但不自动下结论。

## 为什么做这个项目

学习 AI 论文时，真正耗时的地方通常不是“让 AI 总结一篇论文”，而是整个资料处理链路：

- 找正确的 PDF、arXiv 页面、OpenReview 页面、TeX Source 和官方仓库很麻烦。
- 论文、源码、图表、教程、笔记经常散落在不同地方。
- 单独看论文容易卡在公式、方法细节和实现对应关系上。
- 单独看代码又容易不知道它对应论文里的哪一部分。
- 社区教程有帮助，但来源分散，质量不稳定，很难和论文原文互相校验。
- 读完论文后，常常不知道它能不能变成自己的面试项目。

PaperForge Agent 要解决的是这个完整工作流，而不是单点问答。

## 当前技术栈

当前版本故意保持简单：

- **Python**：核心业务和 agent workflow。
- **uv**：项目依赖和本地虚拟环境管理。
- **Streamlit**：本地可视化工作台。
- **PyMuPDF**：PDF 图片提取。
- **pytest**：基础测试。
- **本地文件系统**：保存 job、metadata、notes 和后续论文资产。

不再使用 TypeScript、React、Express。这样项目更适合你学习和面试包装。

## 当前可运行能力

当前版本已经具备 intake + asset collection + source enrichment + PDF image extraction + code linking + note scaffold + terminology scaffold + doubts scaffold + interview mapping scaffold 的最小闭环：

1. 输入论文标题、arXiv ID 或 URL。
2. Agent 调用 arXiv API 解析论文元信息。
3. 系统创建本地研究任务 `ResearchJob`。
4. 系统在 `.paperforge-data/paper-vault/` 下生成论文工作区。
5. 系统写入 `metadata.json` 和 `notes/external-sources.md`。
6. Asset Collector 下载 `raw/paper.pdf` 和 `raw/source.tar.gz`。
7. 系统尝试解压 `raw/tex-source/`。
8. Source Enrichment Agent 更新 `notes/external-sources.md`，记录本地 PDF/TeX 状态和用户补充 URL。
9. PDF Image Extractor 从 `raw/paper.pdf` 提取图片到 `images/` 并生成 `images/manifest.md`。
10. Code Linker Agent 生成 `notes/code-references.md`，记录 GitHub 候选仓库但不自动 clone。
11. Note Writer Agent 生成 `notes/README.md` 的结构化笔记骨架。
12. Terminology Agent 生成 `notes/terminology.md` 的术语库骨架。
13. Doubts Agent 生成 `notes/doubts.md` 的疑难点骨架。
14. Interview Mapper Agent 生成 `notes/interview-project.md` 的面试项目映射骨架。
15. Streamlit 页面展示论文摘要、任务状态、agent timeline 和 artifact 列表。

## 项目结构

```text
PaperForge-Agent/
├── app.py                         # Streamlit 页面入口
├── paperforge/                    # Python 核心代码
│   ├── arxiv_client.py             # arXiv 查询和解析
│   ├── asset_collector.py           # PDF / TeX Source 下载和解压
│   ├── code_linker.py               # GitHub 候选仓库整理
│   ├── doubts_agent.py              # 疑难点骨架生成
│   ├── interview_mapper.py           # 面试项目映射骨架生成
│   ├── intake_agent.py             # 论文 intake agent workflow
│   ├── models.py                   # ResearchJob / AgentStep / Artifact 数据结构
│   ├── note_writer.py               # 论文笔记骨架生成
│   ├── pdf_image_extractor.py       # PDF 图片提取
│   ├── source_enrichment.py         # 外部来源和本地资产状态整理
│   ├── terminology_agent.py         # 术语库骨架生成
│   ├── slug.py                     # 论文目录名生成
│   ├── steps.py                    # timeline step 状态流转
│   └── storage.py                  # 本地文件读写
├── tests/                         # pytest 测试
├── scripts/                       # 本地真实样例流水线脚本
├── docs/                          # 项目文档
└── .paperforge-data/              # 本地生成数据，不进入 git
```

## 本地运行

项目用 uv 管理依赖。虚拟环境目录是 `.venv/`，激活后显示 `(agent)`。

```powershell
uv venv --prompt agent .venv
uv sync
```

Git Bash 激活：

```bash
source .venv/Scripts/activate
```

启动应用：

```powershell
uv run streamlit run app.py
```

验证：

```powershell
uv run python -m pytest
```

## 文档入口

- [项目指南](docs/PROJECT_GUIDE.md)
- [流程规范](docs/WORKFLOW_SPEC.md)
- [文档规范](docs/DOCUMENTATION_GUIDE.md)
- [开发步骤记录](docs/BUILD_STEPS.md)
- [项目进度](docs/PROGRESS.md)

文档职责：

- `PROGRESS.md`：当前做到哪一步，适合每次重新打开项目时先看。
- `BUILD_STEPS.md`：阶段复盘，记录每一步为什么做、做了什么、如何验证。
- `PROJECT_GUIDE.md`：项目定位和面试叙事。
- `WORKFLOW_SPEC.md`：agent 流程和产物规范。
- `DOCUMENTATION_GUIDE.md`：说明文档如何维护。
