# PaperForge Agent 流程规范

## 1. 总体流程

PaperForge Agent 把一个论文输入转换成一个完整研究包。

```text
论文输入
  -> 论文身份识别
  -> 原始资产收集
  -> 外部资料增强
  -> 代码关联分析
  -> 图表和文本提取
  -> 深度笔记生成
  -> 术语和疑难点提取
  -> 面试项目映射
  -> 最终研究包
```

每个阶段都应该产生持久化产物。某个阶段失败时，如果不影响后续步骤，后续步骤应该继续执行。

## 2. 论文输入流程

### 支持输入

- 论文标题；
- arXiv ID；
- arXiv URL；
- OpenReview URL；
- PDF URL；
- Hugging Face Papers URL；
- GitHub URL 加可选论文标题。

### 必须输出

创建 `metadata.json`：

```json
{
  "slug": "paper-slug",
  "title": "Paper Title",
  "authors": [],
  "year": null,
  "venue": null,
  "abstract": null,
  "canonical_url": null,
  "pdf_url": null,
  "source_url": null,
  "github_candidates": [],
  "created_at": "ISO-8601 timestamp",
  "status": "intake_completed"
}
```

### 规则

- 优先使用 arXiv、OpenReview、会议官网、作者主页、官方项目页。
- 不优先使用来源不明的 PDF 镜像站。
- 如果多个论文标题相似，必须让用户确认。
- slug 使用简短论文名或常见缩写，不直接使用超长标题。
- 原始标题必须完整保存到 metadata。

## 3. 原始资产收集流程

### 目标目录

```text
paper-vault/<paper-slug>/raw/
```

### 资产结构

```text
raw/
├── paper.pdf
├── source.tar.gz
└── tex-source/
```

### 规则

- 主论文 PDF 统一命名为 `paper.pdf`。
- TeX Source 压缩包统一命名为 `source.tar.gz`。
- 解压后的 TeX 文件放入 `tex-source/`。
- 不覆盖已有文件，除非用户确认或系统记录版本。
- 下载失败必须写入任务 timeline。

### 失败处理

PDF 下载失败时：

- 保留 metadata；
- 保存候选 URL；
- 将资产收集状态标记为 `partial`；
- 允许用户后续手动提供 PDF。

TeX Source 不存在时：

- 标记为 `unavailable`；
- 不视为任务失败；
- 继续基于 PDF 生成笔记。

## 4. 外部资料增强流程

### 支持来源

- 官方项目页；
- GitHub 仓库；
- Hugging Face Papers；
- 技术博客；
- 知乎文章；
- CSDN 文章；
- B 站视频元信息或用户提供的字幕；
- 公众号文章文本；
- 用户自己的笔记。

### MVP 规则

对登录、反爬、版权限制明显的平台，MVP 只支持：

- 用户粘贴文本；
- 用户提供摘要；
- 公开元信息；
- 手动记录 URL。

第一版不要依赖脆弱爬虫。

当前 Python MVP 先做轻量版 Source Enrichment：

- 不自动抓取正文；
- 记录 canonical paper、PDF URL、TeX Source URL；
- 记录本地 `raw/paper.pdf` 和 `raw/tex-source/` 是否可用；
- 支持用户手动提供外部资料 URL；
- TeX Source 缺失时不阻塞流程，继续保留 PDF 作为后续处理输入。

### 必须输出

创建：

```text
notes/external-sources.md
```

内容包括：

- 来源标题；
- URL；
- 来源类型；
- 为什么有用；
- 提取出的关键点；
- 可靠性标签。

可靠性标签：

- `official`
- `author`
- `implementation`
- `community`
- `unknown`

## 5. 代码关联流程

### 目标

判断这篇论文是否需要结合代码阅读，以及是否需要 clone 相关仓库。

### 建议 clone 的情况

- 论文方法强依赖实现细节；
- 公式很难脱离代码理解；
- 官方仓库规模可控；
- 用户希望复现或改造成项目；
- 核心逻辑分散在多个文件中。

### 不建议 clone 的情况

- 仓库巨大且对笔记生成帮助有限；
- 只需要少量文件，远程读取即可；
- license 或访问权限不明确；
- 论文偏理论，代码价值不高。

当前 Python MVP 先做轻量版 Code Linker：

- 只从 `metadata.github_candidates` 和 `notes/external-sources.md` 中整理 GitHub URL；
- 生成 `notes/code-references.md`；
- 不自动搜索全网；
- 不自动 clone 仓库；
- clone 决策统一记录为 `not cloned`；
- 后续是否 clone 需要用户确认。

### 目标目录

```text
code-vault/<owner>__<repo>/
```

### 必须输出

创建：

```text
notes/code-references.md
```

内容包括：

- 仓库 URL；
- 是否 clone；
- license；
- 主要技术栈；
- 核心文件；
- 方法到代码的映射；
- 复现难度；
- 建议优先阅读路径。

## 6. 图片提取流程

### 目标目录

```text
paper-vault/<paper-slug>/images/
```

### 命名规则

```text
fig<index>_<type>_<short-name>.png
```

示例：

```text
fig1_arch_overall.png
fig2_method_attention.png
fig3_result_scaling.png
fig4_ablation_context_length.png
```

### 图片类型

- `arch`
- `method`
- `result`
- `ablation`
- `compare`
- `data`
- `other`

### 提取要求

- 优先提取架构图和方法图。
- 提取关键实验结果图和消融图。
- 保留图片文件和论文页码的映射。
- 自动提取效果差时，标记为需要人工复查。

当前 Python MVP 使用 PyMuPDF：

- 先尝试提取 PDF 内嵌图片；
- 过滤过小图片，减少图标和装饰图；
- 如果没有可用内嵌图片，渲染前几页作为 fallback；
- 生成 `images/manifest.md`，记录文件名、页码、尺寸和来源；
- 将图片文件和 manifest 写入 artifacts；
- 缺少 PDF 时跳过本步骤并记录 timeline，不阻塞已有 metadata、source log 和后续人工处理。

## 7. 深度笔记生成流程

### 主输出

```text
notes/README.md
```

### 推荐结构

```markdown
# Paper Title

> Paper:
> Authors:
> Venue:
> Year:
> Reading time:
> Difficulty:
> Prerequisites:

## TL;DR

## Paper Overview

## Background and Motivation

## Core Method

## Code Mapping

## Experiments

## Deep Q&A

## Limitations

## Practical Takeaways
```

当前 Python MVP 先做 Note Writer 骨架版：

- 生成 `notes/README.md`；
- 写入论文元信息；
- 写入完整章节结构；
- 引用 `notes/external-sources.md`、`images/manifest.md`、`notes/code-references.md`；
- 明确标注 `Draft status: scaffold only; deep explanation not generated yet.`；
- 不生成 TL;DR、方法解释、实验结论或 practical takeaway 的深度内容。

### 质量规则

- 先讲直觉，再讲公式。
- 重要公式必须解释变量含义。
- 图表要和正文解释互相对应。
- 代码片段只在能帮助理解方法时使用。
- 区分论文事实、社区解释和 agent 推测。
- 不确定内容必须显式标注。
- 避免空泛的 AI 总结句式。

## 8. 专业术语流程

### 输出

```text
notes/terminology.md
```

### 推荐结构

```markdown
# Terminology

## Term Name

- Category:
- Short explanation:
- Why it matters in this paper:
- Related terms:
- First seen in:
- Follow-up reading:
```

### 规则

术语库应该服务后续学习，不只是把论文里所有名词机械列出来。

当前 Python MVP 先做 Terminology Agent 骨架版：

- 生成 `notes/terminology.md`；
- 写入论文标题和来源 note；
- 写入标准术语条目字段；
- 明确标注 `Draft status: scaffold only; terms not extracted yet.`；
- 不自动从标题或摘要中机械抽取术语。

## 9. 疑难点提取流程

### 输出

```text
notes/doubts.md
```

### 推荐结构

```markdown
# Doubts and Follow-up Questions

## Open Questions

## Confusing Formulas

## Missing Implementation Details

## Claims That Need Verification

## Questions to Ask an Interviewer or Mentor
```

### 规则

疑难点不是失败产物，而是重要学习资产。

每个疑难点应该说明：

- 哪里不清楚；
- 出现在论文或代码的什么位置；
- 为什么重要；
- 可能如何解决。

当前 Python MVP 先做 Doubts Agent 骨架版：

- 生成 `notes/doubts.md`；
- 写入论文标题和来源 note；
- 写入推荐疑难点章节；
- 明确标注 `Draft status: scaffold only; doubts not generated yet.`；
- 不自动编造开放问题、公式疑问或实现疑问。

## 10. 面试项目映射流程

### 输出

```text
notes/interview-project.md
```

### 推荐结构

```markdown
# Interview Project Mapping

## Suitability

## Why This Can Become a Project

## Why This May Not Be Worth Building

## Minimal Demo Version

## Full Version

## Technical Highlights

## Risks

## Connection to Existing Projects

## Interview Talking Points
```

### 适配度标签

- `high`
- `medium`
- `low`
- `not recommended`

### 判断标准

- 能不能 demo；
- 能不能在合理时间内实现；
- 是否体现工程深度；
- 是否体现 AI/Agent 深度；
- 方法是否能讲清楚；
- 是否能串到已有项目经历；
- 计算资源是否现实。

当前 Python MVP 先做 Interview Mapper Agent 骨架版：

- 生成 `notes/interview-project.md`；
- 写入论文标题；
- 链接 `notes/README.md` 和 `notes/code-references.md`；
- 写入推荐项目映射章节；
- 明确标注 `Draft status: scaffold only; suitability not assessed yet.`；
- 不自动给出适配度结论、不设计完整项目方案。

## 11. Agent Timeline 流程

每个研究任务都要维护 timeline。

步骤状态：

- `pending`
- `running`
- `completed`
- `partial`
- `failed`
- `skipped`
- `needs_user_input`

示例：

```json
{
  "step_id": "asset.collect_pdf",
  "name": "Download PDF",
  "state": "completed",
  "started_at": "ISO-8601 timestamp",
  "ended_at": "ISO-8601 timestamp",
  "inputs": ["canonical_url"],
  "outputs": ["raw/paper.pdf"],
  "error": null
}
```

Streamlit 工作台应该把 timeline 渲染成可视化 plan 或任务时间线。

## 12. Git 和 Plan 可视化流程

### 目标

展示项目是否仍然按计划推进。

### 推荐视图

- 当前 agent plan；
- 已完成步骤；
- 失败或跳过步骤；
- 生成的文件；
- git changed files；
- recent commits；
- plan step 和文件变化之间的关系。

### 规则

这个功能不是替代 git，而是帮助用户理解 agent 到底改了什么、为什么改、是否跑偏。

## 13. 人工确认点

遇到以下情况时，agent 应该暂停并请求用户确认：

- 多篇论文匹配用户输入；
- 准备 clone 大型仓库；
- 生成笔记质量不足；
- 外部资料可靠性弱；
- 面试项目映射建议了过大的项目；
- 即将覆盖已有资产。

## 14. 完成度检查清单

一个论文研究包可接受的最低标准：

- `metadata.json` 存在；
- `raw/paper.pdf` 存在，或有明确失败原因；
- 关键图片已提取，或标记为需要人工复查；
- `notes/README.md` 包含深度方法解释；
- `notes/terminology.md` 包含可复用术语；
- `notes/doubts.md` 包含未解决问题；
- 如果代码相关，`notes/code-references.md` 必须存在；
- `notes/interview-project.md` 给出具体项目判断；
- 每个外部来源都有 URL 和可靠性标签。
