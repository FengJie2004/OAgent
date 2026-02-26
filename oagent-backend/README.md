# OAgent Backend

Python 后端服务，基于 LangChain v1.0 生态构建。

## 快速开始

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Keys
```

### 启动服务

```bash
# 开发模式
uvicorn oagent.main:app --reload

# 或直接运行
python -m oagent.main
```

### 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
src/oagent/
├── api/            # API 路由
│   └── v1/        # v1 版本 API
├── config/        # 配置管理
├── core/          # 核心模块
│   ├── exceptions.py
│   ├── plugin_base.py
│   └── registry.py
├── models/        # Pydantic 模型
├── plugins/       # 插件实现
│   ├── llm/      # LLM 插件
│   ├── embedding/ # Embedding 插件
│   ├── vectorstore/ # 向量库插件
│   ├── rag/      # RAG 插件
│   └── agent/    # Agent 插件
├── services/      # 业务服务层
├── tools/         # Agent 工具
├── utils/         # 工具函数
└── main.py        # 应用入口
```

## API 端点

### LLM
- `GET /api/v1/llm/providers` - 获取 LLM 提供商列表
- `GET /api/v1/llm/models/{provider}` - 获取模型列表
- `POST /api/v1/llm/chat` - 聊天请求
- `POST /api/v1/llm/embed` - 生成嵌入向量

### Agent
- `GET /api/v1/agent/types` - 获取 Agent 类型
- `POST /api/v1/agent/run` - 运行 Agent
- `GET /api/v1/agent/tools` - 获取可用工具

### Chat
- `GET /api/v1/chat/sessions` - 获取会话列表
- `POST /api/v1/chat/sessions` - 创建会话
- `GET /api/v1/chat/sessions/{id}` - 获取会话
- `DELETE /api/v1/chat/sessions/{id}` - 删除会话

### Config
- `GET /api/v1/config` - 获取配置
- `GET /api/v1/config/llm` - 获取 LLM 配置列表
- `POST /api/v1/config/llm` - 创建 LLM 配置
- `DELETE /api/v1/config/llm/{id}` - 删除 LLM 配置

## 开发

### 运行测试

```bash
pytest
```

### 代码检查

```bash
# Linting
ruff check .

# Type checking
mypy .
```

## 许可证

MIT License