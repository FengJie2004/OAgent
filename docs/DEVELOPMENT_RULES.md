# OAgent 开发规则

> 本文档定义了 OAgent 项目的开发规范和流程，所有开发者必须遵守。

---

## 1. 环境管理

### 1.1 Python 环境 (强制)

**只能使用 Conda 管理 Python 环境，禁止使用 venv/pipenv/poetry 等其他工具。**

```bash
# 检查现有环境
conda env list

# 创建环境 (首次)
conda create -n oagent python=3.11 -y

# 激活环境
conda activate oagent

# 安装项目依赖
cd oagent-backend
pip install -e ".[dev]"

# 安装额外依赖（按需）
pip install -e ".[milvus,qdrant,pinecone,chinese]"
```

### 1.2 Node.js 环境

```bash
# 推荐使用 pnpm
npm install -g pnpm
cd oagent-desktop
pnpm install
```

---

## 2. Agent Teams 开发流程

### 2.1 核心原则

**开发任何功能时，必须使用 Claude Code 的 Agent Teams 功能，禁止直接手动编码。**

### 2.2 功能开发流程

```
1. 需求分析 → planner agent (规划)
2. 架构设计 → architect agent (设计)
3. 测试驱动 → tdd-guide agent (测试先行)
4. 代码实现 → subagent-driven-development (并行开发)
5. 代码审查 → code-reviewer agent (审查)
6. 安全检查 → security-reviewer agent (安全)
7. 提交代码 → commit (提交)
```

### 2.3 可用 Agent 列表

| Agent | 用途 | 调用时机 |
|-------|------|---------|
| `planner` | 功能规划 | 开始新功能前 |
| `architect` | 架构设计 | 复杂功能/重构 |
| `tdd-guide` | 测试驱动开发 | 编写新功能 |
| `code-reviewer` | 代码审查 | 完成代码后 |
| `security-reviewer` | 安全检查 | 处理敏感数据 |
| `build-error-resolver` | 构建错误修复 | 构建失败 |
| `e2e-runner` | E2E 测试 | 关键流程 |
| `refactor-cleaner` | 代码清理 | 重构阶段 |

### 2.4 Agent 调用示例

```markdown
# 开发新功能时
请使用 planner agent 规划 [功能名称] 的实现方案

# 代码审查
请使用 code-reviewer agent 审查刚才的代码变更

# 安全检查
请使用 security-reviewer agent 检查 API Key 存储的安全性
```

---

## 3. Git Worktree 工作流

### 3.1 原则

**使用 Agent Teams 开发功能时，必须在独立的 worktree 中进行，禁止直接在 main 分支开发。**

### 3.2 Worktree 创建规范

```bash
# 创建新功能的 worktree
git worktree add ../oagent-feat-<feature-name> -b feat/<feature-name>

# 示例：开发 LLM 插件系统
git worktree add ../oagent-feat-llm-plugins -b feat/llm-plugins

# 进入 worktree 开发
cd ../oagent-feat-llm-plugins

# 开发完成后合并
git checkout main
git merge feat/llm-plugins

# 删除 worktree
git worktree remove ../oagent-feat-llm-plugins
```

### 3.3 Worktree 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `feat/<name>` | `feat/llm-plugins` |
| 修复 | `fix/<name>` | `fix/streaming-bug` |
| 重构 | `refactor/<name>` | `refactor/plugin-system` |
| 文档 | `docs/<name>` | `docs/api-reference` |

### 3.4 Worktree 目录结构

```
OAgent/
├── oagent/                          # main 分支 (主工作区)
├── oagent-feat-llm-plugins/         # feat/llm-plugins worktree
├── oagent-feat-vector-store/        # feat/vector-store worktree
└── oagent-fix-streaming/            # fix/streaming worktree
```

---

## 4. Skills 使用规范

### 4.1 查找 Skills

**遇到问题时，优先使用 find-skills 查找可用的 skills。**

```markdown
# 查找相关 skills
请使用 find-skills 查找与 [问题领域] 相关的 skills

# 示例
请使用 find-skills 查找与 Python 测试相关的 skills
请使用 find-skills 查找与 React 状态管理相关的 skills
```

### 4.2 项目内置 Skills

以下 skills 已配置，可直接使用：

| Skill | 用途 |
|-------|------|
| `everything-claude-code:python-reviewer` | Python 代码审查 |
| `everything-claude-code:go-reviewer` | Go 代码审查 |
| `superpowers:tdd` | TDD 工作流 |
| `superpowers:systematic-debugging` | 系统性调试 |
| `superpowers:brainstorming` | 创意头脑风暴 |
| `superpowers:writing-plans` | 编写计划 |

---

## 5. 提交规范

### 5.1 提交时机

**每完成一个完整的功能点，必须立即 commit，禁止积攒多个功能一次提交。**

### 5.2 提交粒度

| 粒度 | 示例 |
|------|------|
| ✅ 合适 | `feat: add OpenAI LLM plugin` |
| ✅ 合适 | `fix: resolve streaming response issue` |
| ❌ 太大 | `feat: add LLM plugins, vector stores, and RAG` |
| ❌ 太小 | `fix: typo in comment` |

### 5.3 Commit Message 格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 重构
- `docs`: 文档
- `test`: 测试
- `chore`: 构建/工具
- `perf`: 性能优化

**Scopes:**
- `backend`: 后端代码
- `frontend`: 前端代码
- `docs`: 文档
- `plugin`: 插件系统
- `api`: API 相关

**示例:**

```bash
feat(backend): add Anthropic LLM plugin

- Implement Claude 3 support via Anthropic API
- Add streaming response support
- Include token usage tracking

Closes #123
```

### 5.4 提交命令

```bash
# 使用 Skill 提交
/commit

# 或手动提交
git add <specific-files>
git commit -m "feat(backend): add Anthropic LLM plugin"
```

---

## 6. 功能开发清单

### 6.1 新功能开发前

- [ ] 使用 `planner` agent 规划功能
- [ ] 创建对应的 worktree
- [ ] 创建功能分支
- [ ] 更新相关文档

### 6.2 开发过程中

- [ ] 使用 `tdd-guide` agent 编写测试
- [ ] 使用相关 agent 实现功能
- [ ] 使用 `code-reviewer` agent 审查代码
- [ ] 运行测试确保通过

### 6.3 开发完成后

- [ ] 使用 `security-reviewer` agent 检查安全
- [ ] 更新文档
- [ ] 提交代码
- [ ] 合并到主分支
- [ ] 清理 worktree

---

## 7. 项目功能清单

基于 LangChain v1.0 + LangGraph + DeepAgents 的完整功能实现：

### 7.1 LLM 支持 (Priority: P0)

| 功能 | 状态 | 负责模块 |
|------|------|---------|
| OpenAI | ✅ 基础完成 | `plugins/llm/openai.py` |
| Ollama | ✅ 基础完成 | `plugins/llm/ollama.py` |
| Anthropic | 🔲 待开发 | `plugins/llm/anthropic.py` |
| Google Gemini | 🔲 待开发 | `plugins/llm/google.py` |
| 智谱 GLM | 🔲 待开发 | `plugins/llm/zhipu.py` |
| DeepSeek | 🔲 待开发 | `plugins/llm/deepseek.py` |
| 通义千问 | 🔲 待开发 | `plugins/llm/qwen.py` |

### 7.2 Agent 类型 (Priority: P0)

| 功能 | 状态 | 负责模块 |
|------|------|---------|
| LangChain Agent | 🔲 待开发 | `plugins/agent/langchain_agent.py` |
| LangGraph StateGraph | 🔲 待开发 | `plugins/agent/langgraph_agent.py` |
| DeepAgents | 🔲 待开发 | `plugins/agent/deep_agent.py` |
| ReAct Agent | 🔲 待开发 | `plugins/agent/react_agent.py` |
| Plan-and-Execute | 🔲 待开发 | `plugins/agent/plan_execute_agent.py` |

### 7.3 RAG 能力 (Priority: P1)

| 功能 | 状态 | 负责模块 |
|------|------|---------|
| 文档加载器 | 🔲 待开发 | `plugins/rag/loaders/` |
| 文本分割器 | 🔲 待开发 | `plugins/rag/splitters/` |
| Embedding 模型 | 🔲 待开发 | `plugins/embedding/` |
| 向量存储 | 🔲 待开发 | `plugins/vectorstore/` |
| 检索器 | 🔲 待开发 | `plugins/rag/retrievers/` |

### 7.4 向量数据库 (Priority: P1)

| 功能 | 状态 | 负责模块 |
|------|------|---------|
| ChromaDB | 🔲 待开发 | `plugins/vectorstore/chroma.py` |
| FAISS | 🔲 待开发 | `plugins/vectorstore/faiss.py` |
| Milvus | 🔲 待开发 | `plugins/vectorstore/milvus.py` |
| Qdrant | 🔲 待开发 | `plugins/vectorstore/qdrant.py` |
| pgvector | 🔲 待开发 | `plugins/vectorstore/pgvector.py` |

### 7.5 工具系统 (Priority: P1)

| 功能 | 状态 | 负责模块 |
|------|------|---------|
| 文件操作工具 | 🔲 待开发 | `tools/file_tools.py` |
| 网络请求工具 | 🔲 待开发 | `tools/web_tools.py` |
| 代码执行工具 | 🔲 待开发 | `tools/code_tools.py` |
| 搜索工具 | 🔲 待开发 | `tools/search_tools.py` |
| 数据库工具 | 🔲 待开发 | `tools/db_tools.py` |

### 7.6 桌面端 (Priority: P2)

| 功能 | 状态 | 负责模块 |
|------|------|---------|
| 聊天界面 | ✅ 基础完成 | `pages/Chat.tsx` |
| 配置管理 | ✅ 基础完成 | `pages/Config.tsx` |
| 知识库管理 | ✅ 基础完成 | `pages/Knowledge.tsx` |
| WebSocket 实时通信 | 🔲 待开发 | `services/websocket.ts` |
| 后端集成 | 🔲 待开发 | `services/api.ts` |

---

## 8. 优先级定义

| 优先级 | 含义 | 时间要求 |
|--------|------|---------|
| P0 | 核心功能，必须完成 | 当前 Sprint |
| P1 | 重要功能，尽快完成 | 下一个 Sprint |
| P2 | 增强功能，按需完成 | 可延期 |
| P3 | 可选功能，有时间再做 | 低优先级 |

---

## 9. 检查清单

开发每个功能时，必须完成以下检查：

### 代码质量

- [ ] 代码符合项目编码规范
- [ ] 类型注解完整 (Python: type hints, TypeScript: strict mode)
- [ ] 文档字符串/注释完整
- [ ] 无硬编码的敏感信息

### 测试

- [ ] 单元测试覆盖核心逻辑
- [ ] 集成测试覆盖 API 端点
- [ ] 测试覆盖率 ≥ 80%

### 安全

- [ ] API Key 加密存储
- [ ] 输入验证完整
- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险

### 文档

- [ ] API 文档更新
- [ ] README 更新
- [ ] 代码注释清晰

---

## 10. 常见问题

### Q: 如何处理多个并行开发的功能？

```bash
# 创建多个 worktree 并行开发
git worktree add ../oagent-feat-a -b feat/a
git worktree add ../oagent-feat-b -b feat/b

# 分别在不同 worktree 中使用 agent teams 开发
```

### Q: 如何解决 worktree 之间的依赖冲突？

```bash
# 在各自的 worktree 中独立开发
# 完成后合并到 main，解决冲突
git checkout main
git merge feat/a
git merge feat/b
```

### Q: 如何回滚错误的提交？

```bash
# 回滚最近的提交（保留更改）
git reset --soft HEAD~1

# 回滚最近的提交（丢弃更改）
git reset --hard HEAD~1
```

---

## 附录：快速参考命令

```bash
# 环境管理
conda activate oagent
conda deactivate

# 创建 worktree
git worktree add ../oagent-feat-<name> -b feat/<name>

# 列出 worktrees
git worktree list

# 删除 worktree
git worktree remove ../oagent-feat-<name>

# 运行测试
pytest

# 运行后端
uvicorn oagent.main:app --reload

# 运行前端
cd oagent-desktop && pnpm tauri:dev

# 提交代码
/commit
```