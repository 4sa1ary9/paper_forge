# PaperForge Agent 文档规范

## 1. 为什么需要这份文档

PaperForge Agent 不是一个只有代码的项目。它是一个 agent workflow 产品，重要的不只是页面和接口，还有：

- 为什么做；
- 要解决什么真实问题；
- 每一步 agent 产出什么；
- 失败时如何处理；
- 生成内容如何追溯来源；
- 面试时如何讲清楚。

这份文档用于规定项目后续应该准备哪些 Markdown 文档。

当前文档状态应以 `docs/PROGRESS.md` 和 `docs/STATUS_REVIEW.md` 为准。截至 Step 27，项目已经完成 scaffold MVP + PDF text evidence map + paragraph / chunk evidence map + local evidence search MVP + deep note readiness gate + conservative deep note writing MVP（含 Core Method、Experiments、Limitations、Deep Q&A 和 Practical Takeaways 证据草稿）+ ai-paper-reader note generation + terminology evidence MVP + doubts evidence MVP + code mapping evidence MVP + interview project assessment MVP；完整深度笔记正文生成、完整术语解释、完整疑难点分析、完整项目方案、chunk-grounded LLM 生成、语义/向量检索、远端仓库读取和行级代码分析仍属于后续规划。

## 2. 当前必须文档

### README.md

作用：

- 说明项目是什么；
- 说明为什么做；
- 给出 MVP 目标；
- 链接主要文档；
- 后续补充启动方式和技术栈。

当前状态：

- 已创建。

### docs/PROJECT_GUIDE.md

作用：

- 定义项目方向；
- 说明真实需求；
- 解释为什么这是 agent 项目；
- 定义目标用户、范围、MVP 和面试价值。

使用场景：

- 面试时介绍项目；
- 判断某个功能是否应该做；
- 写项目介绍；
- 防止项目范围失控。

### docs/WORKFLOW_SPEC.md

作用：

- 定义端到端论文研究流程；
- 定义每一步产物；
- 定义目录和命名规则；
- 定义 agent step 状态；
- 定义失败处理和人工确认点。

使用场景：

- 实现 Python agent workflow；
- 设计 Streamlit timeline；
- 测试一个论文任务是否完成；
- 约束 agent 输出格式。

### docs/EXTENSION_ROADMAP.md

作用：

- 独立记录核心 MVP 之后的扩展路线；
- 说明每个扩展阶段的目标、输入、输出、边界和验证方式；
- 防止下一步方向散落在多个文档里。

使用场景：

- Step 23 核心 MVP 完成后选择下一阶段；
- 判断扩展功能优先级；
- 面试时解释“当前完成了什么，后续还能怎么扩展”。

### docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md

作用：

- 记录 LLM Query Planner 与 `ai-paper-reader` Prompt Pack 的变更设计；
- 明确为什么 `unet` 这类简称需要先做论文身份规划；
- 明确 `ai-paper-reader` 的准确 skill 文件路径；
- 约束第一版只生成 prompt pack，不把本地 Codex skill 当作 Python 包调用。

使用场景：

- 实现 Extension 0 前先看这里；
- 判断 query planner、arXiv 查询和阅读笔记 prompt 的边界；
- 防止把“复用 skill”误实现成运行时强耦合。

### docs/PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md

作用：

- 保存可复制给另一个 Codex 对话的实现提示词；
- 明确实现文件、测试要求、验证命令和禁止扩 scope 的边界；
- 要求另一个对话读取 `C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md`。

使用场景：

- 需要让新的 Codex 对话继续实现 Extension 0；
- 当前对话不直接改代码，只把需求整理成可执行提示词。

### docs/PROGRESS.md

作用：

- 记录项目当前做到第几步；
- 记录已完成、正在做、下一步要做什么；
- 记录当前技术栈和关键决策；
- 方便后续中断后继续开发。

使用场景：

- 每次重新打开项目时先看这里；
- 面试前快速回顾项目演进；
- 和 AI 协作时让上下文不断线。

更新频率：

- 每次开发结束都要更新。
- 如果中途切换技术栈、当前步骤、下一步目标，也要更新。

### docs/BUILD_STEPS.md

作用：

- 按阶段记录开发过程；
- 说明每一步为什么做；
- 记录关键文件、验证方式和踩过的问题；
- 方便后续复盘和面试讲项目演进。

使用场景：

- 一个阶段完成后更新；
- 面试前复盘“我是怎么一步步做出来的”；
- 和 `PROGRESS.md` 对照，理解当前状态从哪里来。

更新频率：

- 不需要每改一个小文件都更新。
- 完成一个明确阶段时更新，例如 Step 1 intake、Step 2 asset collector。

和 `PROGRESS.md` 的区别：

- `PROGRESS.md` 是当前状态快照；
- `BUILD_STEPS.md` 是历史开发记录。
- 两者可以有少量重复，但不要整段复制。

### docs/STATUS_REVIEW.md

作用：

- 对照文档规划和当前代码实现；
- 明确项目是 scaffold MVP completed，还是 full vision completed；
- 列出已经完成、尚未完成和下一步建议；
- 防止面试或后续开发时夸大当前能力。

使用场景：

- 需要判断“项目有没有完成”时先看这里；
- 每次完成大阶段后更新；
- 面试前校准项目边界。

### docs/AI_LEARNING_PROMPT.md

作用：

- 作为后续请 AI 带学项目时的提示词；
- 明确当前项目阶段、模块列表和面试追问范围；
- 防止学习材料把 scaffold 能力说成深度研究能力。

使用场景：

- 让 AI 分阶段讲解 PaperForge；
- 做代码深读；
- 做面试模拟。

### docs/self/learn.md

作用：

- 保存已经整理过的项目学习笔记；
- 从架构、代码和面试视角复盘项目；
- 跟随项目阶段更新当前能力边界。

使用场景：

- 面试前快速复习；
- 继续开发前校准设计取舍；
- 对照 `STATUS_REVIEW.md` 检查表达是否夸大。

### docs/self/idea.md

作用：

- 记录暂不进入当前 scope 的想法；
- 保存用户在开发中提出的改进方向；
- 作为后续阶段设计的候选输入。

使用场景：

- 避免临时想法打断当前阶段；
- 后续写 spec 或实现计划前回看。

## 3. 后续应补充文档

### docs/ARCHITECTURE.md

选择技术栈后补充。

应该包含：

- Streamlit 页面结构；
- Python 核心模块结构；
- agent runtime；
- 存储设计；
- 任务状态设计；
- 模型 provider 设计；
- 外部工具集成方式。

### docs/DATA_MODEL.md

实现数据库前补充。

应该包含：

- 实体定义；
- 数据库 schema；
- 文件 artifact schema；
- Paper、ResearchJob、AgentStep、Source、Repository、Note 之间的关系。

### docs/API_SPEC.md

如果后续从 Streamlit 迁移到 FastAPI，再补充。

应该包含：

- REST 或 RPC 接口；
- 请求示例；
- 响应示例；
- 错误结构；
- 分页规则；
- 如果使用 streaming，需要定义事件格式。

### docs/AGENT_DESIGN.md

实现 agent 编排前补充。

应该包含：

- agent 角色；
- tool 定义；
- prompt 结构；
- planner 行为；
- retry 规则；
- evidence tracking；
- output validation。

### docs/EVALUATION.md

开始提升输出质量前补充。

应该包含：

- 笔记质量 rubric；
- 来源可靠性 rubric；
- 代码映射质量 rubric；
- 面试项目映射 rubric；
- 用于测试的样例论文。

### docs/DEMO_SCRIPT.md

准备拿项目面试前补充。

应该包含：

- demo 用论文；
- 预期演示流程；
- 截图或录屏计划；
- 面试讲解顺序；
- 已知局限和诚实解释方式。

## 4. 文档维护规则

- 文档要服务决策，不要为了形式写空文档。
- 不确定的地方要明确标注为待决策事项。
- 尽量写具体文件路径、产物和流程，不写空泛描述。
- 项目范围变化时，先改文档再改实现。
- 第一篇论文 workflow 跑通后，要把真实例子补进文档。
- 面试表达必须和项目真实能力一致，不夸大。

## 5. 当前文档状态

```text
README.md                         已创建
docs/PROJECT_GUIDE.md             已创建
docs/WORKFLOW_SPEC.md             已创建
docs/EXTENSION_ROADMAP.md         已创建
docs/CHANGE_REQUEST_LLM_QUERY_AND_AI_READER.md 已创建
docs/PROMPT_IMPLEMENT_LLM_QUERY_AND_AI_READER.md 已创建
docs/DOCUMENTATION_GUIDE.md       已创建
docs/PROGRESS.md                  已创建
docs/BUILD_STEPS.md               已创建
docs/STATUS_REVIEW.md             已创建
docs/AI_LEARNING_PROMPT.md        已创建
docs/self/learn.md                已创建
docs/self/idea.md                 已创建
docs/ARCHITECTURE.md              未开始
docs/DATA_MODEL.md                未开始
docs/API_SPEC.md                  暂缓，等 FastAPI 化后再写
docs/AGENT_DESIGN.md              未开始
docs/EVALUATION.md                未开始
docs/DEMO_SCRIPT.md               未开始
```
