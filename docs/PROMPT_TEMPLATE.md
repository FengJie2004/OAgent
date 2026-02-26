# OAgent 项目开发提示词

> 将此提示词用于新的 Claude Code 会话，以便快速进入开发状态。

---

## 项目概述

OAgent 是一个基于 **LangChain v1.0 + LangGraph + DeepAgents** 构建的**开源可插拔式通用 Agent 框架**，目标是实现 LangChain 生态中所有大模型开发方式，让用户可以自由选择使用哪种 Agent 模型、RAG 框架、向量数据库、嵌入模型、大模型等，实现完全可插拔的 Agent 效果。

**技术栈：**
- 后端：Python 3.11+ / FastAPI / LangChain v1.0 / LangGraph
- 桌面端：Tauri 2.0 / React 18 / TypeScript / Tailwind CSS / shadcn/ui

**项目目录：** `E:\Project\OAgent`

---

## 开发规则（必须遵守）

### 1. 环境管理
- **Python 环境必须使用 Conda**，禁止 venv/pipenv/poetry
- 环境名：`oagent`
- Python 版本：3.11+

```bash
conda create -n oagent python=3.11 -y
conda activate oagent
```

### 2. Agent Teams 工作流程（强制）

**开发任何功能时，必须使用 Agent Teams，禁止直接手动编码。**

标准开发流程：
```
1. 需求分析 → planner agent
2. 架构设计 → architect agent
3. 测试驱动 → tdd-guide agent
4. 代码实现 → subagent-driven-development
5. 代码审查 → code-reviewer agent
6. 安全检查 → security-reviewer agent
7. 提交代码 → /commit
```

可用 Agent：
- `planner` - 功能规划
- `architect` - 架构设计
- `tdd-guide` - 测试驱动开发
- `code-reviewer` - 代码审查
- `security-reviewer` - 安全检查
- `build-error-resolver` - 构建错误修复
- `everything-claude-code:python-reviewer` - Python 代码审查

### 3. Git Worktree 规范

**开发新功能必须在独立 worktree 中进行：**

```bash
# 创建 worktree
git worktree add ../oagent-feat-<name> -b feat/<name>

# 示例
git worktree add ../oagent-feat-dashscope-plugin -b feat/dashscope-plugin

# 开发完成后合并
git checkout main
git merge feat/dashscope-plugin
git worktree remove ../oagent-feat-dashscope-plugin
```

分支命名：
- `feat/<name>` - 新功能
- `fix/<name>` - Bug 修复
- `refactor/<name>` - 重构

### 4. 提交规范

**每完成一个功能点立即 commit：**

```
<type>(<scope>): <description>

Types: feat, fix, refactor, docs, test, chore
Scopes: backend, frontend, docs, plugin, api
```

示例：
```
feat(backend): add DashScope LLM plugin
fix(frontend): resolve chat streaming issue
```

### 5. Skills 使用

遇到问题时优先使用 `find-skills` 查找可用的 skills：

```markdown
请使用 find-skills 查找与 [问题领域] 相关的 skills
```

---

## API 配置

### 阿里百炼 (DashScope) - 默认使用

| 配置项 | 值 |
|-------|-----|
| API Key | `sk-e6fb13a44d6c460893abc75a612e7041` |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 聊天模型 | `qwen3.5-plus` |
| 嵌入模型 | `text-embedding-v4` |

**OpenAI 兼容模式：**
```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-e6fb13a44d6c460893abc75a612e7041",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen3.5-plus",
    messages=[{"role": "user", "content": "你好"}]
)
```

---

## 当前项目状态

### 已完成
- ✅ 项目文档（PRD、技术规格、架构设计、开发规则）
- ✅ 后端骨架（FastAPI + 插件系统 + API）
- ✅ 前端骨架（Tauri + React + Tailwind）
- ✅ OpenAI/Ollama LLM 插件（基础版）
- ✅ 配置管理（Pydantic Settings）

### 待开发（P0 优先级）
- 🔲 DashScope LLM 插件（阿里百炼）
- 🔲 LangChain Agent 实现
- 🔲 LangGraph StateGraph Agent
- 🔲 RAG 能力（文档加载、分割、嵌入）
- 🔲 ChromaDB 向量存储插件

### 待开发（P1 优先级）
- 🔲 其他 LLM 插件（Anthropic、Google、智谱、DeepSeek）
- 🔲 更多向量数据库（FAISS、Milvus、Qdrant）
- 🔲 工具系统（文件、网络、代码执行）
- 🔲 前端后端集成

---

## 关键文件路径

```
E:\Project\OAgent\
├── docs/
│   ├── PRD.md                    # 产品需求文档
│   ├── TECHNICAL_SPECIFICATION.md # 技术规格
│   ├── ARCHITECTURE.md           # 架构设计
│   ├── DEVELOPMENT_RULES.md      # 开发规则（详细版）
│   └── API_KEYS.md              # API 密钥配置
├── oagent-backend/
│   ├── src/oagent/
│   │   ├── config/settings.py   # 配置管理
│   │   ├── plugins/llm/        # LLM 插件
│   │   ├── api/v1/             # API 端点
│   │   └── main.py             # 入口
│   ├── .env                     # 环境变量
│   └── pyproject.toml          # 依赖配置
├── oagent-desktop/
│   ├── src/                    # React 前端
│   ├── src-tauri/              # Rust 后端
│   └── package.json
└── DEVELOPMENT.md              # 快速开始指南
```

---

## 开发命令速查

```bash
# 环境管理
conda activate oagent

# Git Worktree
git worktree add ../oagent-feat-xxx -b feat/xxx
git worktree list
git worktree remove ../oagent-feat-xxx

# 后端开发
cd oagent-backend
uvicorn oagent.main:app --reload

# 测试
pytest

# 代码检查
ruff check .
mypy .

# 前端开发
cd oagent-desktop
pnpm tauri:dev

# 提交
/commit
```

---

## 开始开发示例

当开始一个新功能时，使用以下提示词：

```markdown
我正在开发 OAgent 项目，这是一个基于 LangChain v1.0 的可插拔式通用 Agent 框架。

当前任务：开发 DashScope LLM 插件

请使用 planner agent 规划这个功能的实现方案，包括：
1. 需要创建哪些文件
2. 接口设计
3. 与现有插件系统的集成方式

项目信息：
- 后端目录：E:\Project\OAgent\oagent-backend\src\oagent
- 插件基类：plugins/llm/base.py
- 插件注册：core/registry.py
- API 配置：已配置 DashScope API Key 和 qwen3.5-plus 模型

开发规则：
- 必须使用 Agent Teams 工作流程
- 使用 TDD 先写测试
- 完成后使用 code-reviewer 审查
```

---

## 文档链接

- [LangChain 文档](https://docs.langchain.com/oss/python/langchain/overview)
- [LangGraph 文档](https://docs.langchain.com/oss/python/langgraph/overview)
- [DeepAgents 文档](https://docs.langchain.com/oss/python/deepagents/overview)
- [阿里百炼文档](https://help.aliyun.com/zh/dashsphere/)