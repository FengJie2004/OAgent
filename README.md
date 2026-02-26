# OAgent

**开源可插拔式通用 Agent 框架** - 基于 LangChain v1.0 生态的全栈 AI Agent 平台

## 简介

OAgent 是一个基于 LangChain v1.0 + LangGraph + DeepAgents 构建的通用 Agent 框架，支持：

- **可插拔架构**: LLM、向量库、RAG框架、Agent类型均可自由替换
- **全栈能力**: Python 后端 + Tauri 桌面端
- **LangChain 原生**: 充分利用 LangChain 生态最新特性

## 功能特性

### LLM 支持
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 系列)
- Google (Gemini)
- Ollama (本地模型)
- 国产模型 (通义千问、文心一言、智谱GLM、DeepSeek)

### Agent 类型
- LangChain Agent
- LangGraph StateGraph Agent
- DeepAgents
- ReAct Agent
- Plan-and-Execute Agent

### 向量数据库
- ChromaDB (开发推荐)
- FAISS (高性能本地)
- Milvus (生产级分布式)
- Qdrant
- pgvector

### RAG 框架
- LangChain RAG
- LlamaIndex
- Haystack

## 项目结构

```
OAgent/
├── docs/                          # 文档
│   ├── PRD.md                     # 产品需求文档
│   ├── TECHNICAL_SPECIFICATION.md # 技术规格文档
│   └── ARCHITECTURE.md            # 架构设计文档
├── oagent-backend/                # Python 后端
│   ├── src/oagent/               # 源代码
│   ├── tests/                    # 测试
│   ├── pyproject.toml           # 项目配置
│   └── README.md
├── oagent-desktop/               # Tauri 桌面端
│   ├── src-tauri/               # Rust 后端
│   ├── src/                     # React 前端
│   ├── package.json
│   └── README.md
└── README.md                     # 本文件
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Rust 1.70+
- pnpm (推荐)

### 后端启动

```bash
cd oagent-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
uvicorn oagent.main:app --reload
```

### 桌面端启动

```bash
cd oagent-desktop
pnpm install
pnpm tauri dev
```

## 开发路线

- [x] 项目规划与文档
- [ ] 后端核心架构
- [ ] LLM 插件系统
- [ ] Agent 插件系统
- [ ] RAG 能力集成
- [ ] 桌面端开发
- [ ] 测试与文档

## 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详情。

## 许可证

MIT License