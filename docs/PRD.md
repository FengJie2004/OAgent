# OAgent - 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 项目名称
**OAgent** - 开源可插拔式通用 Agent 框架

### 1.2 项目愿景
打造一个基于 LangChain v1.0 生态的全栈通用 Agent 平台，让用户能够像搭积木一样自由组合各种 AI 能力组件，实现高度定制化的智能应用。

### 1.3 核心价值主张
- **可插拔架构**: 所有组件（LLM、向量库、RAG框架、Agent类型等）均可自由替换
- **开箱即用**: 预置主流配置模板，快速启动使用
- **全栈能力**: 后端 Python + 桌面端 Tauri，覆盖完整开发链路
- **LangChain 原生**: 充分利用 LangChain v1.0 + LangGraph + DeepAgents 新特性

---

## 2. 目标用户

### 2.1 主要用户群体
| 用户类型 | 描述 | 核心需求 |
|---------|------|---------|
| **开发者** | AI应用开发者、后端工程师 | 快速构建Agent应用、灵活定制组件 |
| **研究人员** | AI研究者、算法工程师 | 对比实验、模型评测、框架研究 |
| **企业用户** | 需要私有化部署的企业 | 数据安全、定制化、成本控制 |
| **爱好者** | AI技术爱好者 | 学习探索、个人项目 |

### 2.2 用户画像
**开发者张三**：
- 3年后端开发经验，Python熟练
- 想快速搭建一个客服机器人
- 需要支持多种LLM（OpenAI、本地模型）
- 希望有图形界面管理配置

---

## 3. 功能需求

### 3.1 核心功能模块

#### 3.1.1 LLM 模块 (可插拔)
- [ ] 支持多种 LLM 提供商
  - OpenAI (GPT-4, GPT-4o, GPT-3.5)
  - Anthropic (Claude 系列)
  - Google (Gemini)
  - 本地模型 (Ollama, vLLM)
  - 国产模型 (通义千问、文心一言、智谱GLM、DeepSeek)
- [ ] 统一的模型接口抽象
- [ ] 模型参数配置 (temperature, max_tokens, top_p 等)
- [ ] 流式输出支持
- [ ] 多模型负载均衡

#### 3.1.2 Agent 模块 (可插拔)
- [ ] 支持多种 Agent 类型
  - LangChain Agent (create_agent)
  - LangGraph StateGraph Agent
  - DeepAgents (高级特性)
  - ReAct Agent
  - Plan-and-Execute Agent
  - Conversational Agent
- [ ] Agent 工具管理
- [ ] Agent 记忆系统
- [ ] 人机协作 (Human-in-the-loop)
- [ ] 子Agent调用

#### 3.1.3 RAG 模块 (可插拔)
- [ ] 多种 RAG 框架支持
  - LangChain RAG
  - LlamaIndex
  - Haystack
- [ ] 文档加载器
  - PDF, Word, Markdown, TXT
  - Web 页面抓取
  - 数据库连接
- [ ] 文本分割策略
  - 递归字符分割
  - 语义分割
  - 按段落/章节分割

#### 3.1.4 Embedding 模块 (可插拔)
- [ ] 多种嵌入模型支持
  - OpenAI Embeddings
  - HuggingFace 模型
  - 本地模型 (sentence-transformers)
  - 国产嵌入模型
- [ ] 批量嵌入处理
- [ ] 嵌入缓存

#### 3.1.5 向量数据库模块 (可插拔)
- [ ] 多种向量库支持
  - ChromaDB (轻量级，适合开发)
  - FAISS (高性能，本地部署)
  - Milvus (分布式，生产级)
  - Pinecone (云服务)
  - Weaviate (混合搜索)
  - Qdrant (高性能过滤)
  - pgvector (PostgreSQL 扩展)
- [ ] 统一的向量操作接口
- [ ] 索引管理
- [ ] 相似度搜索

#### 3.1.6 工具/中间件模块
- [ ] 内置工具
  - 文件操作 (读写、搜索)
  - 网络请求 (HTTP, API调用)
  - 代码执行 (Python沙箱)
  - 数据库查询
  - 搜索引擎集成
- [ ] 自定义工具接口
- [ ] 工具权限控制
- [ ] 工具市场 (未来)

### 3.2 桌面端功能 (Tauri)

#### 3.2.1 核心界面
- [ ] 仪表盘 - 项目概览、快速操作
- [ ] 对话界面 - 与 Agent 交互
- [ ] 配置管理 - 组件配置中心
- [ ] 工作流编辑器 - 可视化 Agent 编排 (未来)

#### 3.2.2 管理功能
- [ ] LLM 配置管理
- [ ] 向量库管理
- [ ] 知识库管理
- [ ] Agent 模板管理
- [ ] 会话历史管理
- [ ] 日志查看

#### 3.2.3 用户体验
- [ ] 深色/浅色主题
- [ ] 多语言支持 (中/英)
- [ ] 快捷键支持
- [ ] 系统托盘
- [ ] 自动更新

### 3.3 后端 API 功能
- [ ] RESTful API 设计
- [ ] WebSocket 实时通信
- [ ] API 认证与授权
- [ ] 请求限流
- [ ] API 文档 (Swagger/OpenAPI)

---

## 4. 非功能需求

### 4.1 性能要求
| 指标 | 目标值 |
|-----|-------|
| 响应时间 | 首字节 < 500ms |
| 并发支持 | 100+ 并发请求 |
| 内存占用 | 空闲 < 200MB |
| 启动时间 | < 3s |

### 4.2 安全要求
- API Key 加密存储
- 敏感数据不落盘
- 本地模型支持 (数据不出域)
- 权限最小化原则

### 4.3 可扩展性
- 插件系统设计
- 自定义组件扩展
- Webhook 支持

### 4.4 兼容性
- Windows 10/11
- macOS 11+
- Linux (主流发行版)

---

## 5. 产品路线图

### Phase 1: MVP (v0.1.0)
- 基础 LLM 集成 (OpenAI, Ollama)
- 简单 Agent 对话
- 基础配置界面

### Phase 2: RAG 能力 (v0.2.0)
- 向量库集成 (ChromaDB)
- 文档上传与处理
- 基础 RAG 对话

### Phase 3: 完整框架 (v0.3.0)
- 多 Agent 类型支持
- 工具系统
- LangGraph 工作流

### Phase 4: 生产就绪 (v1.0.0)
- 多向量库支持
- 多 LLM 支持
- 完善的桌面端
- API 服务
- 文档完善

---

## 6. 成功指标

| 指标 | 目标 |
|-----|-----|
| GitHub Stars | 1000+ (半年内) |
| 活跃用户 | 500+ 月活 |
| 社区贡献 | 10+ 贡献者 |
| 文档完整度 | 100% API 覆盖 |

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|-----|-----|---------|
| LangChain API 变动 | 高 | 抽象层隔离，版本锁定 |
| 性能瓶颈 | 中 | 异步架构，缓存策略 |
| 依赖冲突 | 中 | 虚拟环境，Docker 化 |
| 用户学习曲线 | 中 | 完善文档，示例项目 |

---

## 8. 附录

### 8.1 参考项目
- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Dify](https://github.com/langgenius/dify)
- [LangFlow](https://github.com/langflow-ai/langflow)

### 8.2 技术栈
- **后端**: Python 3.11+, FastAPI, LangChain v1.0
- **桌面端**: Tauri 2.0, React/TypeScript
- **数据库**: SQLite (本地), PostgreSQL (可选)
- **向量库**: ChromaDB, FAISS, Milvus 等