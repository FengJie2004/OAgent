# OAgent 开发指南

## 快速开始

### 1. 创建 Conda 环境

```bash
# 检查现有环境
conda env list

# 创建环境 (首次)
conda create -n oagent python=3.11 -y

# 激活环境
conda activate oagent
```

### 2. 安装依赖

```bash
# 后端依赖
cd oagent-backend
pip install -e ".[dev]"

# 前端依赖 (新终端)
cd oagent-desktop
pnpm install
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp oagent-backend/.env.example oagent-backend/.env

# 编辑 .env 文件，填入你的 API Keys
# 已配置阿里百炼 DashScope：
# - API Key: sk-e6fb13a44d6c460893abc75a612e7041
# - Chat Model: qwen3.5-plus
# - Embedding Model: text-embedding-v4
```

### 4. 启动开发服务器

```bash
# 后端 (终端 1)
conda activate oagent
cd oagent-backend
uvicorn oagent.main:app --reload

# 前端 (终端 2)
cd oagent-desktop
pnpm tauri:dev
```

---

## 开发规范

请阅读 [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md) 了解完整的开发规范。

### 核心原则

1. **必须使用 Conda 管理 Python 环境**
2. **必须使用 Agent Teams 开发功能**
3. **必须在 Worktree 中开发新功能**
4. **必须及时提交代码**

### Agent Teams 使用

开发新功能时的标准流程：

```markdown
1. 创建 worktree: git worktree add ../oagent-feat-xxx -b feat/xxx
2. 使用 planner agent 规划功能
3. 使用 tdd-guide agent 编写测试
4. 使用 subagent-driven-development 实现功能
5. 使用 code-reviewer agent 审查代码
6. 使用 security-reviewer agent 检查安全
7. 提交代码: /commit
8. 合并并清理 worktree
```

---

## 项目结构

```
OAgent/
├── docs/                    # 文档
│   ├── PRD.md              # 产品需求
│   ├── TECHNICAL_SPECIFICATION.md
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT_RULES.md
├── scripts/                # 脚本
│   ├── setup_env.sh        # 环境初始化
│   └── setup_env.bat
├── oagent-backend/          # Python 后端
│   ├── src/oagent/
│   ├── tests/
│   └── pyproject.toml
├── oagent-desktop/          # Tauri 桌面端
│   ├── src/                # React 前端
│   ├── src-tauri/          # Rust 后端
│   └── package.json
└── README.md
```

---

## 功能开发清单

参见 [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md#7-项目功能清单)

---

## 常用命令

```bash
# 环境管理
conda activate oagent
conda deactivate

# Git Worktree
git worktree add ../oagent-feat-xxx -b feat/xxx
git worktree list
git worktree remove ../oagent-feat-xxx

# 测试
pytest

# 代码检查
ruff check .
mypy .

# 提交
/commit
```