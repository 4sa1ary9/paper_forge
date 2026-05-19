# PaperForge Agent 协作规则

这个项目是 **Python + Streamlit** 的 AI 论文研究 Agent。

项目目标不是炫复杂技术栈，而是用尽量清楚的 Python 代码实现一个可讲清楚、可演示、可逐步扩展的 agent workflow。

## 0. 当前项目约束

- 使用 Python，不使用 TypeScript、React、Express。
- 本机运行命令优先使用 uv 管理的 `.venv` 环境，激活名为 `agent`。
- Streamlit 是当前 UI，不额外引入前后端分离框架。
- 生成数据放在 `.paperforge-data/`，不要提交进 git。
- 大 PDF、TeX Source、第三方 repo 不放进应用代码目录。
- 每次完成一个开发阶段后，更新 `docs/PROGRESS.md`。
- 每次完成一个较大的阶段后，更新 `docs/BUILD_STEPS.md`。
- 不确定是否该做的功能，先写入文档或提问，不直接扩 scope。

## 1. 项目文档职责

- `README.md`：项目入口，说明是什么、怎么运行、当前能力。
- `docs/PROJECT_GUIDE.md`：项目定位、面试叙事、范围和长期模块。
- `docs/WORKFLOW_SPEC.md`：agent workflow 和产物规范。
- `docs/PROGRESS.md`：当前做到哪一步，下一步做什么。
- `docs/BUILD_STEPS.md`：按阶段记录“做了什么、为什么做、怎么验证”。
- `docs/DOCUMENTATION_GUIDE.md`：说明这些文档各自该怎么维护。

`PROGRESS.md` 和 `BUILD_STEPS.md` 允许少量重复：

- `PROGRESS.md` 方便快速接续；
- `BUILD_STEPS.md` 方便复盘学习和面试讲开发过程。

## 2. 推荐运行命令

安装依赖：

```powershell
uv venv --prompt agent .venv
uv sync
```

运行应用：

```powershell
uv run streamlit run app.py
```

运行测试：

```powershell
uv run python -m pytest
```

## 3. 代码修改原则

优先修改这些 Python 模块：

- `paperforge/intake_agent.py`：论文 intake workflow。
- `paperforge/arxiv_client.py`：arXiv 查询和解析。
- `paperforge/storage.py`：本地文件读写。
- `paperforge/models.py`：核心数据结构。
- `app.py`：Streamlit 页面。

新增能力时，遵循这个顺序：

1. 先定义要新增的 agent step。
2. 再定义产物路径和 artifact。
3. 实现 Python 函数。
4. 加测试。
5. 跑真实样例。
6. 更新 `PROGRESS.md`，必要时更新 `BUILD_STEPS.md`。

---

以下是通用编码规范，继续保留。

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
