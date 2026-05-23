# PaperForge Agent 深度学习笔记

---

# 阶段一：项目全景理解

## 1. 核心叙事——这是什么，解决什么问题？

**一句话**：PaperForge Agent 不是"论文总结器"，而是把一篇 AI 论文从零整理成**可复用的结构化研究包**的 agentic workflow 系统。

**真实痛点**（这个你要能讲出来）：
- 读论文时，PDF、arXiv 页面、TeX 源码、GitHub 仓库、社区教程分散在各处
- 论文方法和代码实现之间的映射关系难以建立
- 读完论文后，不知道能不能把它变成面试项目
- 笔记质量没标准——到底"读懂"了没有，缺少可检验的证据链

**它做了什么**：把"研究一篇论文"拆成 13 个当前已实现的 agent stage，每个 stage 有明确的输入、输出、状态，最终落盘成一个规范的目录结构。


## 2. 为什么它是 Agent 项目，不是普通脚本？

这是面试必问题。核心区别在**架构层面**，有五个关键差异：

| 维度 | 普通脚本 | PaperForge Agent |
|------|---------|-----------------|
| **任务分解** | 一次性执行，无显式计划 | 将"研究论文"拆成多个命名 step/stage，每个有独立 ID、状态、时间线 |
| **状态管理** | 成功/崩溃，无中间状态 | 每个 step 有 pending/running/completed/partial/failed/skipped/needs_user_input 七种状态 |
| **可观测性** | 出错了不知道哪一步失败 | Agent Timeline 记录每个 step 的 started_at、ended_at、inputs、outputs、error |
| **部分容错** | 一个环节失败，整个流程崩溃 | PDF 下载失败不影响 metadata 写入；TeX 缺失自动切换到 PDF-based processing |
| **产物持久化** | 输出到 stdout 或临时文件 | 每个 artifact 落盘到规范化目录，有 kind/label/path 追踪 |

面试时这样说：

> "我不会说这是一个多智能体系统。它是一个 agentic workflow——我把研究任务建模为有状态的步骤序列，每个步骤有独立生命周期和容错策略，产物持久化到文件系统，中间失败不阻塞下游。这比一个线性脚本多了 planning、observability 和 graceful degradation。"


## 3. Agent 工作流阶段

13 个当前已实现 stage，按依赖关系形成一条带分支的流水线：

```
用户输入
  → ① Paper Intake（解析 arXiv 元信息，创建 workspace）
  → ② Asset Collector（下载 PDF + TeX 源码）
  → ③ PDF Image Extractor（从 PDF 提取图片）
  → ④ Source Enrichment（整理外部资料和资产状态）
  → ⑤ Code Linker（整理 GitHub 候选仓库）
  → ⑥ Note Writer（生成笔记骨架）
  → ⑦ Terminology Agent（术语库骨架）
  → ⑧ Doubts Agent（疑难点骨架）
  → ⑨ Interview Mapper（面试项目映射骨架）
  → ⑩ Package Validator（研究包完整性检查）
  → ⑪ PDF Text Evidence Extractor（PDF 文本证据）
  → ⑫ Deep Note Planner（深度笔记准备度计划）
  → ⑬ Deep Note Writer MVP（保守版 TL;DR / Paper Overview 写入）
```

步骤 ②-⑨ 之间耦合很弱——除了都需要 ① 的 metadata 作为前置，它们彼此之间基本独立。⑥⑦⑧⑨ 甚至可以并行执行。⑩、⑪、⑫ 和 ⑬ 更像验收、证据提取、规划与保守写入阶段：它们读取前面落盘的产物，判断研究包是否齐全、提取 PDF 文本证据、规划后续哪些深度笔记章节可以进入生成，并把 ready 的轻量章节写回主笔记。


## 4. 为什么三层分离？

```
paperforge/          ← 应用代码（你的 Agent 逻辑）
.paperforge-data/    ← 研究资产（运行时产出）
  ├── jobs/          ← JSON 序列化的 ResearchJob
  └── paper-vault/   ← 论文 PDF、图片、笔记
code-vault/          ← 第三方代码仓库（计划中，暂未实现）
```

三层设计的理由：
- **Git 干净**：应用代码和运行数据分离，`.paperforge-data/` 在 `.gitignore` 中，不会把大 PDF 提交到仓库
- **可迁移**：换存储后端时（比如换 SQLite 或 S3），只需改 `storage.py`，agent 模块零改动
- **面试可讲**：这是典型的 "separation of concerns"，体现了工程意识


## 5. 当前进度：Step 13 已跑通

**已完整实现**（有真实数据验证过）：
- ① Paper Intake：arXiv API 调用 → metadata 解析 → workspace 创建 ✅
- ② Asset Collector：PDF 下载 + TeX 源码下载 + 解压 ✅
- ③ PDF Image Extractor：PyMuPDF 提取图片 + 生成 manifest ✅
- ④ Source Enrichment：整理外部资料 markdown ✅
- ⑤ Code Linker：从 metadata 和 external sources 提取 GitHub URL ✅
- ⑪ PDF Text Evidence Extractor：从 PDF 提取页码级文本证据 ✅
- ⑫ Deep Note Planner：根据 package status 和 evidence 文件判断深度笔记章节准备度 ✅
- ⑬ Deep Note Writer MVP：写入 TL;DR / Paper Overview 的保守证据草稿 ✅

**骨架实现**（生成的是带占位符的模板文件，不是真实内容）：
- ⑥ Note Writer：生成 `notes/README.md` 框架，所有章节标注 "Not generated yet"
- ⑦ Terminology Agent：生成 `notes/terminology.md` 模板
- ⑧ Doubts Agent：生成 `notes/doubts.md` 模板
- ⑨ Interview Mapper：生成 `notes/interview-project.md` 模板
- ⑩ Package Validator：文件存在性检查
- ⑪ PDF Text Evidence Extractor：evidence map，不总结、不解释
- ⑫ Deep Note Planner：readiness gate，不生成深度正文
- ⑬ Deep Note Writer MVP：只写 ready 的 TL;DR / Paper Overview，不生成完整深度报告

**暂不做**：
- clone 仓库、完整深度 LLM 笔记生成、自动适配度判断、FastAPI 后端、React 前端

**Scaffold vs 完整实现的关键区别**：scaffold 生成的是**结构正确的空模板**，内容字段写了但值是 "Not generated yet"——它验证了"文件能落盘、路径正确、artifact 追踪正常"，但没有真正调用 LLM 去理解和生成内容。这其实是一个聪明的设计：先把管道跑通，确认数据流没问题，再往里面灌 LLM 生成的内容。


# 阶段二：Agent 模块深度拆解

我把当前模块逐一过。先看共性，再看个性。

## 共性设计模式

所有 agent 模块遵循同一个模式，你读任意一个模块都能看到：

```python
def run_xxx(job: ResearchJob) -> ResearchJob:
    # 1. 前置检查
    if job.metadata is None: raise ValueError(...)

    # 2. 确定输出路径
    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"

    # 3. 创建 step（状态机起点）
    step = start_step(create_step("xxx.id", "描述", ["inputs"]))

    # 4. 追加到 job 的 timeline
    job.steps.append(step)

    # 5. 执行业务逻辑（try/except）
    try:
        output_path.write_text(content)
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"  # 不阻塞
        save_job(job)
        return job

    # 6. 更新 artifacts
    _add_artifact(job, output_path)

    # 7. 标记完成，持久化
    finish_step(step, "completed", [output_path])
    job.updated_at = now_iso()
    save_job(job)
    return job
```

这个模式的精妙之处：
- `save_job(job)` 是每个模块的共同出口——无论成功、失败、部分完成，都持久化
- 失败后 `return job` 而非 `raise`——下游不会被打断
- `job` 作为参数传入并返回——**纯函数式的状态流转**，便于测试


## 模块 1: Paper Intake Agent

**输入**：用户字符串（arXiv URL / ID / 论文标题）
**输出**：`ResearchJob` 对象（含 metadata、3 个完成/partial 的 step、2 个 artifact）

**状态机**：3 个子步骤
```
intake.resolve_identity  →  workspace.create_paper_folder  →  workspace.write_metadata
```

**关键设计**：`_fallback_metadata()`——如果 arXiv API 调用失败，不会抛异常让用户看到错误堆栈。而是创建一个 `status="intake_partial"` 的 metadata，让用户知道"解析没完全成功，但 workspace 已经建好了，你可以手动补信息"。这是 graceful degradation。

**依赖**：无，这是所有 agent 的起点。

**当前状态**：完整实现。arXiv API 调用 + XML 解析 + workspace 创建 + metadata 落盘全部可跑。


## 模块 2: Asset Collector Agent

**输入**：`ResearchJob`（需要 `job.metadata.pdf_url` 和 `job.metadata.source_url`）
**输出**：下载的 `raw/paper.pdf`、`raw/source.tar.gz`、解压的 `raw/tex-source/`

**状态机**：3 个步骤
```
asset.collect_pdf  →  asset.collect_source  →  asset.extract_source
```

**关键设计 1**：`Downloader` 是一个 `Callable[[str], bytes]` 类型别名。通过依赖注入（`downloader` 参数），测试时可以用 mock 替换真实的网络请求。

**关键设计 2**：`_asset_collection_status()` 的逻辑：
- PDF 没成功 → 整体状态 `partial`（不是 `failed`）
- TeX 下载或解压失败 → 也是 `partial`
- 只有三个都完成 → `completed`

这意味着"TeX 源码没拿到"不阻碍整个流程——你仍然可以基于 PDF 做后续处理。

**关键设计 3**：idempotent——`if target_path.exists(): return`，重复执行不会重复下载。

**依赖**：需要 Paper Intake 先跑完（需要 metadata 里的 pdf_url 和 source_url）。

**当前状态**：完整实现。已验证对多篇论文的实际下载。


## 模块 3: Source Enrichment Agent

**输入**：`ResearchJob` + 可选的用户提供的 URL 列表
**输出**：更新 `notes/external-sources.md`，记录 PDF/TeX 资产状态和外部链接

**关键设计**：`_pdf_status()` 和 `_tex_source_status()` 两个函数**从 job.artifacts 列表推断资产状态**，而不是直接检查文件系统。但同时也做了 fallback 检查文件系统——双重保险。

**`_add_artifact()` 的去重逻辑**：不重复添加同一个 path 的 artifact，而是更新已有 artifact 的 kind/label。这避免了 artifacts 列表膨胀。

**依赖**：需要 metadata + 建议先跑 Asset Collector（否则资产状态都是 "missing"）。

**当前状态**：完整实现。规则驱动的 markdown 生成，不需要 LLM。


## 模块 4: Code Linker Agent

**输入**：`ResearchJob`（数据来源：`metadata.github_candidates` + `external-sources.md` 中的 URL）
**输出**：`notes/code-references.md`

**关键设计**：正则提取 GitHub URL——`GITHUB_REPOSITORY_PATTERN` 从文本中匹配 `github.com/owner/repo` 格式。这个方法不完美（可能在教程网站中提到 GitHub 但不是代码仓库），但 MVP 够用，且比调用 GitHub Search API 简单可靠。

**为什么 partial 而非 failed**：没有找到 GitHub 候选仓库时，step 标记为 `partial` 而非 `failed`。因为"这篇论文没有公开代码实现"不等于"这一步执行失败"——这是一种合理的结果。

**依赖**：需要 metadata（论文标题）+ 建议先跑 Source Enrichment（获取 external sources 中的 GitHub URL）。

**当前状态**：完整实现（轻量版）。不做全网搜索，不做自动 clone。


## 模块 5: PDF Image Extractor Agent

**输入**：`ResearchJob`（需要 `raw/paper.pdf` 存在）
**输出**：`images/fig001_*.png` 等图片文件 + `images/manifest.md`

**关键设计 1**：两种提取策略的 fallback——
1. 先尝试提取 PDF 内嵌图片（`page.get_images(full=True)`），过滤小于 160x120 的小图标
2. 如果没有内嵌图片，渲染前 12 页作为整页截图（`page.get_pixmap()`）

**关键设计 2**：`PdfImageExtractor` 类型别名 + 依赖注入——和 Asset Collector 一样，测试时可以注入 mock 提取器。

**关键设计 3**：`_safe_extension()` 白名单——防止恶意构造的 PDF 产生异常的扩展名。

**依赖**：需要 PDF 已下载（Asset Collector 先跑）。

**当前状态**：完整实现。已对 DDPM 论文提取 22 张图片。


## 模块 6-9: 四个骨架 Agent

Note Writer、Terminology Agent、Doubts Agent、Interview Mapper——这四个模块结构几乎相同，合并讲解。

**共性**：
- 每个都生成一个 `.md` 文件到 `notes/` 目录
- 文件包含完整的章节结构但内容全是 "Not generated yet"
- 明确标注 `Draft status: scaffold only`
- 都在 `_add_artifact` 中有去重逻辑

**区别**：

| 模块 | 输出文件 | 引用上游 |
|------|---------|---------|
| Note Writer | `notes/README.md` | external-sources.md, manifest.md, code-references.md |
| Terminology | `notes/terminology.md` | README.md |
| Doubts | `notes/doubts.md` | README.md |
| Interview Mapper | `notes/interview-project.md` | README.md, code-references.md |

**为什么先做 scaffold 而不是直接让 LLM 出全文？**

这是一个重要的架构决策，面试时会被问到。三个原因：
1. **验证数据管道**：先确认"文件能落盘、路径正确、artifact 追踪正常"，再往里面灌内容。如果管道都有 bug，生成的内容也存不对
2. **控制 LLM 成本**：每个骨架文件都标注了 "Not generated yet"——这是给下一阶段的 prompt 留的"锚点"，LLM 知道该往哪里填内容
3. **分阶段迭代**：scaffold → 简单 LLM 生成 → 多步推理生成，每一步都可以独立验证


## 模块 10: Package Validator Agent

**输入**：`ResearchJob`（检查整个 paper workspace）
**输出**：`notes/package-status.md`（三层分类的检查报告）

**关键设计**：三层分类
```python
REQUIRED   = [metadata, external-sources, code-references, README, terminology, doubts, interview-mapping]
RECOMMENDED = [paper.pdf, images/manifest]
OPTIONAL    = [source.tar.gz, tex-source/]
```

**状态判定逻辑**：
- `required` 缺失 → step 记 `partial`，报告中列出 "missing required"
- `recommended` 缺失 → step 记 `partial`，报告中列出 "warnings"
- `optional` 缺失 → 报告中列出但**不改变 step 状态**
- 只有 report 文件本身写失败 → step 记 `failed`

这个设计体现了"检查器不应该比被检查物更脆弱"的原则。

**面试价值**：这展示了你对"验收标准"的工程化思考。不是凭感觉说"做好了"，而是有一套可复现的检查清单。

**当前状态**：完整实现。文件存在性检查全部可跑。


## 模块 11: PDF Text Evidence Extractor Agent

**输入**：`ResearchJob`（需要 `raw/paper.pdf` 存在）
**输出**：`notes/evidence-map.md`

**关键设计**：它只提取页码级文本证据，不生成总结。`evidence-map.md` 记录每页字符数和 text excerpt，后续 Deep Note Writer 必须引用这里的页码证据。

**为什么 partial report 有价值**：如果 PDF 缺失或没有可抽取文本，agent 仍然写出 `notes/evidence-map.md`，把问题显式记录到 timeline 和 artifact。这样后续可以选择补 PDF、OCR 或 TeX Source 解析，而不是静默失败。

**当前状态**：轻量实现。能从 PDF 提取分页文本 excerpt，但还没有段落切分、公式定位、语义 chunk 或向量索引。


## 模块 12: Deep Note Planner Agent

**输入**：`ResearchJob`（检查 `notes/package-status.md`、`notes/README.md`、`raw/paper.pdf`、`images/manifest.md` 等 readiness 输入）
**输出**：`notes/deep-note-plan.md`

**关键设计**：它是深度生成前的 readiness gate，而不是内容生成器。它只回答"哪些章节现在有足够基础证据可以进入下一阶段"，并把 Deep Q&A、Practical Takeaways 这类依赖前置内容的章节保持为 `blocked`。

**为什么这一步重要**：它避免了刚完成 scaffold 就直接让 LLM 写完整深度笔记。当前系统已经有页码级 evidence map，但还没有段落级语义索引和人工复查，所以 planner 仍然必须保守。

**当前状态**：骨架实现。能生成章节准备度计划，但不提取 PDF 正文、不生成深度解释。


## 模块 13: Deep Note Writer MVP

**输入**：`ResearchJob`（需要 `notes/deep-note-plan.md`、`notes/evidence-map.md` 和 `notes/README.md` 存在）
**输出**：更新后的 `notes/README.md`

**关键设计**：它只处理 readiness table 中标记为 `ready` 的目标章节。当前 MVP 只写 TL;DR 和 Paper Overview，并且每段都引用 `notes/evidence-map.md` 的页码，同时保留 `needs human review` 标记。

**为什么仍然保守**：它不是完整深度笔记生成器。当前输出更像 evidence-grounded seed，目的是验证“按证据写入主笔记”的管道，而不是自动解释 Core Method 或实验结果。

**真实修复**：真实 Attention 样例中，PDF 第 1 页是版权/授权声明。初版会把它写入 TL;DR，后来增加了 boilerplate page 过滤和回归测试，避免把 PDF 前置声明当成论文内容。另一个细节是 regex replacement string 会破坏 `\alpha` 这类反斜杠证据文本，后来改成函数式 replacement。

**当前状态**：MVP 完成。能写入 TL;DR / Paper Overview，但还没有段落级证据选择、LLM 生成、Core Method 或 Experiments 深度解释。


# 阶段三：代码级深读

## 1. `models.py`——数据模型

```python
StepState = Literal[
    "pending", "running", "completed",
    "partial", "failed", "skipped", "needs_user_input",
]
```

**为什么用 `Literal`？**

`Literal` 是 Python 3.8+ 的类型系统特性。这里用它而不是 `str` 或 `Enum`，原因：
- 比 `str` 更严格——IDE 和 mypy 会检查你只能传这 7 个值，打错字就报错
- 比 `Enum` 更轻量——序列化到 JSON 时直接是字符串 `"completed"`，不要额外转换
- **面试时这是加分点**——说明你对 Python 类型系统的掌握不止于基础

```python
@dataclass
class AgentStep:
    id: str
    name: str
    state: StepState = "pending"
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    started_at: str | None = None
    ended_at: str | None = None
    error: str | None = None
```

**为什么是 dataclass 而不是普通 dict？**

- 字段有类型注解 → IDE 自动补全
- `field(default_factory=list)` 避免可变默认参数的经典坑
- `asdict()` 一行序列化到 JSON（在 `to_dict` 函数中）
- 时间字段用 `str | None` 而非 `datetime`——因为 JSON 不能直接存 datetime 对象，存 ISO 字符串更简单

**`ArtifactKind` 的分类**：当前列出 12 种类型，覆盖了现有 scaffold workflow 会产生的文件类型。不是随手写的——每个 kind 对应一类 agent 产出物，例如 metadata、pdf、figure、note、code_reference、package_status、evidence_map。Step 13 更新的是主笔记，所以继续复用 `note` kind。

**`PaperMetadata` 的 `status` 字段**：只有两个值 `intake_completed` / `intake_partial`。这是一个有意思的设计——它不在 `PaperMetadata` 上做更多状态区分，而是把更细粒度的状态放在 `ResearchJob.status` 和每个 `AgentStep.state` 上。

**`ResearchJob` 是聚合根**：它持有 `metadata`、`steps`（timeline）、`artifacts` 三者的引用，是整个系统的中心数据结构。所有 agent 函数签名为 `(ResearchJob) -> ResearchJob`。


## 2. `storage.py`——存储层

**核心设计抉择：本地文件系统 vs 数据库**

当前选择本地文件系统的理由：
- **零依赖**：不需要安装数据库、不需要启动服务
- **可审计**：打开 `jobs/xxx.json` 就能看完整状态，对学习和调试友好
- **可迁移**：`save_job` 和 `list_jobs` 是两个唯一暴露的接口，换后端只需改这两个函数

**序列化/反序列化**：

```python
def save_job(job: ResearchJob) -> None:
    path = get_jobs_dir() / f"{job.id}.json"
    path.write_text(json.dumps(to_dict(job), ...))

def list_jobs() -> list[ResearchJob]:
    for path in get_jobs_dir().glob("*.json"):
        jobs.append(research_job_from_dict(json.loads(path.read_text())))
```

这是一个简单的 **JSON file-per-record** 模式。优点是直接、可读、可 grep。缺点是并发写不安全——但当前是单用户 Streamlit，够用。

**向前兼容**：
```python
input_text=data.get("input_text") or data.get("input") or "",
```
注意这行！它同时检查 `input_text`（新格式）和 `input`（旧 TypeScript 格式）——因为早期测试时遗留了 camelCase 的 job 文件。这是一个真实的兼容性需求。


## 3. `steps.py`——状态流转

文件很短（34 行），但设计很精确：

```python
def create_step(step_id, name, inputs) -> AgentStep  # 创建，默认状态 pending
def start_step(step) -> AgentStep                      # 标记 running + 记录开始时间
def finish_step(step, state, outputs, error) -> AgentStep  # 标记终态 + 记录结束时间
```

**为什么独立成文件而不是写在 models 里？**

这是关注点分离。`models.py` 定义"数据是什么"，`steps.py` 定义"数据如何流转"。当状态流转逻辑变复杂时（比如加入重试、超时、回滚），只改 `steps.py`。

**时间戳用 `now_iso()` 而不是 `datetime.now()`**：
```python
def now_iso() -> str:
    return datetime.now(UTC).isoformat()
```
- `UTC` 时区——避免时区混乱
- `.isoformat()` 返回字符串——直接存入 dataclass，JSON 序列化无需额外处理


## 4. `arxiv_client.py`——外部 API 调用

**arXiv ID 解析**：
```python
def parse_arxiv_id(text: str) -> str | None:
    # 支持三种输入格式：
    # 1. URL: arxiv.org/abs/1706.03762
    # 2. Modern ID: 1706.03762 或 1706.03762v7
    # 3. Legacy ID: hep-th/9711200
```

正则表达式处理三种格式，最终提取干净的 ID。如果没有匹配到 ID，返回 `None`，上层会把它当标题去搜索。

**HTTP 429 的故事**：
```python
headers={"User-Agent": "PaperForgeAgent/0.1 contact=local-dev"}
```

这是 PROGRESS.md 里记录的真实修复——arXiv API 没有 User-Agent 时会返回 HTTP 429（Too Many Requests）。arxiv.org 的速率限制策略是：没有 User-Agent 的请求会被当作爬虫限流，加上 User-Agent 后恢复正常。这是一个在实际开发中才遇到的坑。

**XML 解析**：arXiv API 返回 Atom XML，用 Python 标准库 `xml.etree.ElementTree` 解析，零第三方依赖。`ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}` 是 Atom namespace，不传 namespace 就找不到元素——又一个容易踩的坑。


## 5. `app.py`——Streamlit 工作台

**为什么是 Streamlit 而不是 FastAPI + React？**

这是一个面试常见的"你为什么选这个技术"问题。理由：
1. **学习成本**：你不需要同时学前端框架和后端框架，Streamlit 是纯 Python
2. **Agent 工作台天然适合 Streamlit**：Agent 的 step-by-step 执行、状态展示、产物预览——Streamlit 的按钮 + spinner + 三列布局直接满足
3. **后续可迁移**：核心逻辑在 `paperforge/` 包里，与 UI 完全解耦，换 FastAPI 只需重写 `app.py`

**session_state 管理**：
```python
st.session_state["active_job_id"] = job.id  # 创建时
active_job_id = st.session_state.get("active_job_id", jobs[0].id)  # 读取时
```

只有两个 session state 变量：`active_job_id`（当前选中的 job）和 Streamlit 内部的 widget 状态。Agent workflow 的复杂状态全部在 `ResearchJob` 的 dataclass 里，session_state 只是"指向当前 job"的指针。

**界面设计**：三列布局
```
[Paper Workspace 1.3x] | [Agent Timeline 1x] | [Artifacts 1x]
```
- 左列：论文概览（标题、作者、摘要）
- 中列：步骤时间线（每个 step 的状态图标 + 错误信息）
- 右列：产物列表（文件路径 + 可展开预览）


# 阶段四：面试视角——如何包装这个项目

## 项目介绍

### 电梯演讲版（30 秒）

> "PaperForge 是一个论文研究 Agent——你把论文 URL 给它，它自动完成身份识别、PDF 下载、图片提取、代码关联、笔记生成、术语提取、面试项目映射、PDF 文本证据提取、深度笔记准备度计划，并写入带页码证据的保守版 TL;DR / Paper Overview。当前 Python 版已跑通完整 scaffold 闭环，29 个测试通过。"

### 深度介绍版（2 分钟）

> "我做 PaperForge 的出发点是：我读 AI 论文时，最花时间的不是理解，而是整理——把 PDF、arXiv 页面、GitHub 实现、社区教程和笔记串联起来。我看了市面上很多'论文总结器'，它们都是 ChatGPT 套壳，输入论文、输出一段总结，没有持久化、没有追踪、没有容错。
>
> 所以我设计了 PaperForge，它是一个 agentic workflow 系统。核心设计是把'研究一篇论文'拆成多个可追踪的步骤，每个步骤有独立的状态机——pending、running、completed、partial、failed 等七种状态。PDF 下载失败不影响 metadata 写入，TeX 源码缺失自动切换到 PDF-based processing。所有中间产物——metadata、PDF、图片、笔记——都持久化到一个规范的目录结构里。
>
> 技术栈是 Python + Streamlit + PyMuPDF，数据模型用了 dataclass + Literal 类型。当前完整的 intake、资产下载、图片提取、代码关联、PDF 文本证据、包验证和深度笔记 readiness gate 已经跑通，笔记生成等模块做了 scaffold——也就是生成了完整的章节框架和数据管道，后续可以基于 evidence map 引入 LLM 生成内容。
>
> 我真正做的设计决策包括：状态机的七种状态而非简单的成功/失败、纯函数式的 job 状态流转、scaffold-first 的开发策略——先验证管道再引入 LLM。这些让系统在对 LLM 依赖最小的前提下，获得了完整的可观测性和容错能力。"


## 10 个常见面试追问

### 1. "你为什么说这是一个 Agent 项目，而不是普通的 Python 脚本流水线？"

**要点**：
- 不是看有没有 LLM——是看有没有 **planning + state + observability + graceful degradation**
- 每个 step 有独立 ID、输入列表、输出列表、开始/结束时间、错误信息
- 有 7 种状态（不是 2 种），其中有 `partial`——"完成了但不完美"
- 失败不阻塞下游——Agent 知道"什么可以跳过，什么必须重试"
- 对比普通脚本：`download_pdf()` 失败了就 `sys.exit(1)`，用户不知道哪步出了问题

### 2. "你的 Agent 是怎么做 planning 的？"

**诚实回答**：当前是静态的、预定义的步骤序列，不是 LLM 动态生成的 plan。PROJECT_GUIDE.md 和 WORKFLOW_SPEC.md 定义好了当前 scaffold workflow 的步骤排列。Deep Note Planner 是规则驱动的 readiness plan，用来判断章节准备度；Deep Note Writer MVP 只按 ready 状态写入保守草稿。后续 LLM 动态 planning 还没实现。

**但要补一句**：这个设计是有意的——在引入 LLM 做动态 planning 之前，先把确定性的流程跑通。后续如果要加 LLM planning，会在 intake 阶段让 LLM 判断"这篇论文理论上需要哪些步骤"，与预定义模板合并。

### 3. "每篇论文的处理流程是有向无环图（DAG）还是线性流水线？"

**回答**：介于两者之间。严格来说是一个 DAG——步骤 ②-⑨ 都依赖 ①，但它们彼此之间基本独立；⑩、⑪ 和 ⑫ 依赖前面产物的文件状态和 PDF 资产。当前 Streamlit 界面是手动触发的线性执行，但代码层面各模块的耦合主要围绕 `ResearchJob` 和落盘 artifact。

**如果要并行化**：只需把 `app.py` 中的按钮改成批量执行，因为每个 `run_xxx(job)` 都是纯函数，可以串成链 `run_b(run_a(job))`。

### 4. "你的每一个 Agent 步骤是 LLM 驱动的还是规则驱动的？"

**诚实回答**：当前绝大部分是规则驱动的：
- Paper Intake：arXiv API + XML 解析
- Asset Collector：HTTP 下载 + tar 解压
- PDF Image Extractor：PyMuPDF 图片提取
- Source Enrichment / Code Linker：正则 + markdown 拼接
- Note Writer 等：模板字符串拼接（scaffold）

**如果要加入 LLM**：架构不需要大改。每个 `run_xxx()` 函数内部，把当前的字符串拼接替换成 LLM 调用即可——因为输入（`ResearchJob`）和输出（更新 `ResearchJob` + 持久化）的接口已经稳定。这就是 scaffold-first 策略的好处。

### 5. "你的状态机设计有什么考量？"

**要点**：
- `partial` 是关键创新——大多数系统只有 success/failure，但论文研究中很多情况是"完成了但不完整"：PDF 下载了但 TeX 没有，或 GitHub 候选找到了但不确认哪个是官方实现
- `skipped` 和 `failed` 有本质区别：TeX 源码不存在 → `skipped`（合理跳过）；下载中途网络断开 → `failed`（需要重试）
- `needs_user_input` 是预留的——当前 Streamlit 做到了"手动触发"，但还没有做到"Agent 主动停下来等输入"

### 6. "如果 PDF 下载失败，后续流程怎么办？"

**回答**：三层容错：
1. Asset Collector 中，PDF 下载失败 → step 标记 `failed`，但 job.status 变为 `partial`，不会抛异常
2. PDF Image Extractor 中，检测到 PDF 不存在 → step 标记 `skipped`，不阻塞
3. Note Writer 等模块不直接依赖 PDF，只依赖 metadata，不受影响

### 7. "为什么把笔记生成设计成 scaffold 而不是直接让 LLM 出全文？"

这个上面说过了，面试时强调三个词：**管道验证、成本控制、分阶段迭代**。

### 8. "这个项目的技术难点在哪？不是指用了什么库，而是架构设计上的取舍。"

这题考的是你有没有架构思维。你可以说：

> "最大的取舍是**什么时候引入 LLM，什么时候保持确定性**。如果一开始就所有步骤都调 LLM，成本高、速度慢、调试困难。我的策略是：先把所有确定性步骤（下载、解析、提取、文件管理）用规则实现，把 LLM 限定在内容生成环节（笔记、术语、疑难点）。这保证了系统的可靠性和可调试性。第二个取舍是**状态粒度**——用 7 种状态而不是 2 种，增加了复杂度，但换来了精确的可观测性。"

### 9. "如果要扩展成多篇论文并行处理，你的架构需要改什么？"

**回答**：
- **数据模型**：不需要改。`ResearchJob` 已经是一篇论文一个 job，天然隔离
- **存储层**：当前 JSON file-per-record 在并发写时不安全。需要换 SQLite（单机）或 PostgreSQL（多机），但 `save_job` 和 `list_jobs` 的接口不变
- **Agent 模块**：零改动。因为 `run_xxx(job)` 是纯函数，对单个 job 操作
- **UI**：`app.py` 需要改为支持多 job 并行触发的界面

### 10. "你觉得自己在这个项目里真正做的设计决策是什么，而不是 AI 帮你生成的？"

这是最锋利的一题。诚实地讲：

> "有几个决策是我主导的。第一，状态机的 7 种状态——尤其是 `partial` 这个状态，是因为我在实际跑 pipeline 时发现'PDF 下载成功但 TeX 失败'这种情况经常发生，用 binary 成功/失败表达不了。第二，三层目录分离——应用代码、研究数据、第三方仓库分开，这是从实际使用体验出发的，不是 AI 建议的。第三，scaffold-first 策略——先验证管道再引入 LLM，这是看了很多 AI 项目为了追求'智能感'而忽略基础工程可靠性之后的逆向选择。第四，依赖注入——`Downloader` 和 `PdfImageExtractor` 的类型别名，这个设计是为了让核心逻辑可测试，这个思路来自 Clean Architecture 的原则而非 AI 的随机生成。"


## 面试禁区

1. **不要说"从零手写了一个完整多智能体系统"**——你没有。你说的是"agentic workflow with state management and graceful degradation"

2. **不要夸大 LLM 参与度**——当前大部分是规则驱动，LLM 只在计划中。说"当前实现了确定性管道，LLM 内容生成是下一步"既诚实又有规划

3. **不要说"还没做完"**——说"做了骨架，后续会用 LLM 逐步增强"。骨架本身已经能跑通完整闭环

4. **准备 2-3 个真实踩坑故事**：
   - arXiv API HTTP 429 → 加上 User-Agent header（一个正则就能解决的 debug，但学到了 API 规范）
   - 旧 TypeScript 版本的 camelCase JSON → 反序列化时兼容新旧格式
   - PDF 图片提取时内嵌图片可能是图标（16x16 的装饰元素）→ 加了 160x120 的最小尺寸过滤


# 阶段五：实战延伸——如何继续迭代

## 1. 下一步 Deep Note Writer Background MVP 设计

当前 Deep Note Writer MVP 已经能写入 TL;DR 和 Paper Overview，但不能一次性扩成完整深度报告。更稳的下一步是：

```
Step 14: Deep Note Writer Background MVP
  Input:  notes/README.md + notes/deep-note-plan.md + notes/evidence-map.md
  Process: 只填充 deep-note-plan 标记为 ready 的 Background and Motivation
  Output: notes/README.md
  Guard:  每段结论保留页码证据和人工复查标记
```

为什么先做 MVP：
- 现在已经有 `notes/evidence-map.md`，可以让生成内容引用页码；
- 已经从 TL;DR、Paper Overview 这类轻量章节开始验证了写入链路；
- Background and Motivation 仍然相对保守，适合继续扩展；
- Deep Q&A、Practical Takeaways 仍然依赖前置方法和实验笔记，不能提前生成。

## 2. 后续 Deep Note Generation 设计

**什么时候引入 LLM，什么时候不该**：
- **不该引入 LLM 的**：arxiv_client（API 调用）、asset_collector（下载）、pdf_image_extractor（PyMuPDF）、package_validator（文件检查）——这些都是确定的、可靠的、不需要"智能"的
- **该引入 LLM 的**：note_writer（读 PDF 文本 → 生成笔记）、terminology_agent（从全文中提取术语）、doubts_agent（从方法细节中找出疑点）、interview_mapper（判断适配度）

**设计建议**：
```
Step 14+: Deep Note Writer
  Input:  notes/README.md + notes/deep-note-plan.md + notes/evidence-map.md
  Process: LLM 只填充 deep-note-plan 标记为 ready 的章节
  Output: notes/README.md (updated, with content)
  Guard:  标注"AI 生成，人工校对"；不确定结论标注置信度和证据位置
```

**为什么要从 scaffold 出发，而不是让 LLM 从零写？** Scaffold 提供了结构和约束——LLM 知道"TL;DR 写在这，方法写在这"，而不是自由发挥。这增加了可控性和一致性。

## 3. 从 Streamlit 迁移到 FastAPI

**哪些模块零改动复用**：`paperforge/` 下所有 agent 模块——`run_xxx(job)` 是纯函数，不依赖 Streamlit。

只需改 `app.py`：
- Streamlit `st.button` → FastAPI `@app.post("/intake")`
- Streamlit `st.session_state` → FastAPI 依赖注入或简单的 dict
- Streamlit `st.spinner` → FastAPI `BackgroundTasks` 或返回 job ID 让前端轮询

`storage.py` 需要关注并发安全（当前 JSON file-per-record 不是线程安全的），但接口不变。

## 4. 如何加入 RAG

当前项目已经是 RAG 的绝佳数据基础：
- `notes/README.md` → 可检索的笔记文本
- `notes/terminology.md` → 可检索的术语定义
- `notes/doubts.md` → 可检索的未解决问题
- `images/manifest.md` → 图片索引
- PDF 文本（尚未提取）→ 原文检索

**最简方案**：用 ChromaDB（Python 库，零配置）对每个 paper workspace 的所有 `.md` 和 PDF 文本建向量索引，然后在 Note Writer 或 Doubts Agent 中，LLM 生成内容前先检索相关段落作为 context。

**面试关联**：RAG 是面试高频话题。你可以说"我的研究包目录结构天然支持 RAG——每个笔记文件都有明确的证据来源标注，可以按证据链接追溯到原文。"

## 5. 面试话题关联

| 面试话题 | 项目对应点 |
|---------|-----------|
| **Agent Architecture** | staged workflow + 7-state machine |
| **Tool Calling** | 每个 agent 模块都可以视为一个 tool，接收 `ResearchJob`，返回 `ResearchJob` |
| **Prompt Engineering** | WORKFLOW_SPEC.md 定义了每个 scaffold 的结构和内容规范，可直接转化为 structured prompt |
| **Evaluation** | Package Validator 是自动化验收——"什么是 done"有可检查的标准 |
| **Data Modeling** | dataclass + Literal + 聚合根模式 |
| **Error Handling** | partial/skipped/failed 的区分 + graceful degradation |
| **RAG** | 研究包目录结构天然支持向量检索 |
| **API Design** | `run_xxx(job) -> job` 纯函数接口，UI 和后端完全解耦 |

---

以上就是五个阶段的完整拆解。你可以随时指定某个阶段或具体模块深入，比如"帮我模拟一次面试追问"或者"带我精读 asset_collector 的容错逻辑"。
