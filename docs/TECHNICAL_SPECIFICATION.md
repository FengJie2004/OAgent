# OAgent - 技术规格文档 (Technical Specification)

## 1. 技术架构概览

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      OAgent Desktop (Tauri)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Dashboard  │  │   Chat UI   │  │   Configuration Center  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                           │                                      │
│                    ┌──────┴──────┐                               │
│                    │ Tauri IPC   │                               │
│                    └──────┬──────┘                               │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OAgent Backend (Python)                      │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                    API Layer (FastAPI)                      ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   ││
│  │  │ REST API │ │ WebSocket│ │  Auth    │ │  Middleware  │   ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                  Core Engine (LangChain)                    ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   ││
│  │  │   Agent  │ │   RAG    │ │  Tools   │ │   Memory     │   ││
│  │  │  Engine  │ │  Engine  │ │ Registry │ │   Manager    │   ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                   Plugin Architecture                       ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   ││
│  │  │ LLM Plugin│ │Emb Plugin│ │ Vec DB  │ │ RAG Plugin   │   ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │   LLM    │ │ Vector DB│ │ Storage  │ │  Other Services  │   │
│  │Providers │ │          │ │          │ │                  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈详情

| 层级 | 技术选型 | 版本要求 | 说明 |
|-----|---------|---------|------|
| **桌面端框架** | Tauri | 2.0+ | Rust 后端 + Web 前端 |
| **前端框架** | React | 18+ | UI 组件开发 |
| **前端语言** | TypeScript | 5.0+ | 类型安全 |
| **UI 组件库** | shadcn/ui | latest | 基于 Radix UI |
| **状态管理** | Zustand | 4.0+ | 轻量状态管理 |
| **后端框架** | FastAPI | 0.109+ | 异步 API 框架 |
| **后端语言** | Python | 3.11+ | 核心 Agent 引擎 |
| **Agent 框架** | LangChain | 1.0+ | 核心 Agent 能力 |
| **工作流引擎** | LangGraph | 0.2+ | 复杂 Agent 工作流 |
| **高级 Agent** | DeepAgents | latest | 增强 Agent 能力 |
| **本地数据库** | SQLite | 3.40+ | 配置存储 |
| **日志系统** | Loguru | 0.7+ | 结构化日志 |

---

## 2. 后端架构设计

### 2.1 目录结构

```
oagent-backend/
├── src/
│   └── oagent/
│       ├── __init__.py
│       ├── main.py                    # FastAPI 入口
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py            # Pydantic Settings
│       │   └── logging.py             # 日志配置
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py                # 依赖注入
│       │   ├── v1/
│       │   │   ├── __init__.py
│       │   │   ├── router.py          # 路由聚合
│       │   │   ├── llm.py             # LLM API
│       │   │   ├── agent.py           # Agent API
│       │   │   ├── rag.py             # RAG API
│       │   │   ├── tools.py           # Tools API
│       │   │   ├── chat.py            # Chat API
│       │   │   └── config.py          # Config API
│       │   └── websocket/
│       │       ├── __init__.py
│       │       └── chat.py            # WebSocket 聊天
│       ├── core/
│       │   ├── __init__.py
│       │   ├── plugin_base.py         # 插件基类
│       │   ├── registry.py            # 组件注册中心
│       │   └── exceptions.py          # 自定义异常
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # LLM 插件基类
│       │   │   ├── openai.py          # OpenAI 实现
│       │   │   ├── anthropic.py       # Anthropic 实现
│       │   │   ├── ollama.py          # Ollama 实现
│       │   │   ├── zhipu.py           # 智谱实现
│       │   │   └── deepseek.py        # DeepSeek 实现
│       │   ├── embedding/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # Embedding 插件基类
│       │   │   ├── openai.py
│       │   │   ├── huggingface.py
│       │   │   └── local.py
│       │   ├── vectorstore/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # VectorStore 插件基类
│       │   │   ├── chroma.py
│       │   │   ├── faiss.py
│       │   │   ├── milvus.py
│       │   │   └── qdrant.py
│       │   ├── rag/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # RAG 插件基类
│       │   │   ├── simple.py          # 简单 RAG
│       │   │   └── advanced.py        # 高级 RAG
│       │   └── agent/
│       │       ├── __init__.py
│       │       ├── base.py            # Agent 插件基类
│       │       ├── langchain_agent.py # LangChain Agent
│       │       ├── langgraph_agent.py # LangGraph Agent
│       │       └── deep_agent.py      # DeepAgent
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm_service.py         # LLM 服务层
│       │   ├── agent_service.py       # Agent 服务层
│       │   ├── rag_service.py         # RAG 服务层
│       │   ├── chat_service.py        # Chat 服务层
│       │   └── tool_service.py       # Tool 服务层
│       ├── models/
│       │   ├── __init__.py
│       │   ├── llm.py                 # LLM 配置模型
│       │   ├── agent.py               # Agent 配置模型
│       │   ├── chat.py                # Chat 消息模型
│       │   └── config.py              # 配置模型
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── base.py                # Tool 基类
│       │   ├── file_tools.py         # 文件工具
│       │   ├── web_tools.py          # 网络工具
│       │   ├── code_tools.py         # 代码工具
│       │   └── search_tools.py       # 搜索工具
│       └── utils/
│           ├── __init__.py
│           ├── crypto.py              # 加密工具
│           └── helpers.py             # 辅助函数
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_llm/
│   ├── test_agent/
│   └── test_rag/
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 2.2 核心接口设计

#### 2.2.1 LLM 插件接口

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from pydantic import BaseModel

class LLMConfig(BaseModel):
    """LLM 配置模型"""
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    stream: bool = True

class Message(BaseModel):
    """消息模型"""
    role: str  # system, user, assistant
    content: str

class LLMPluginBase(ABC):
    """LLM 插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """支持的模型列表"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """聊天接口 (支持流式)"""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        config: LLMConfig
    ) -> List[List[float]]:
        """嵌入接口"""
        pass

    def validate_config(self, config: LLMConfig) -> bool:
        """验证配置"""
        return True
```

#### 2.2.2 VectorStore 插件接口

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class VectorStoreConfig(BaseModel):
    """向量库配置"""
    provider: str
    persist_directory: Optional[str] = None
    collection_name: str = "default"
    embedding_dimension: int = 1536

class Document(BaseModel):
    """文档模型"""
    id: str
    content: str
    metadata: dict = {}
    embedding: Optional[List[float]] = None

class VectorStorePluginBase(ABC):
    """向量库插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        config: VectorStoreConfig
    ) -> List[str]:
        """添加文档，返回文档ID列表"""
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        config: VectorStoreConfig
    ) -> List[Document]:
        """相似度搜索"""
        pass

    @abstractmethod
    async def delete_documents(
        self,
        ids: List[str],
        config: VectorStoreConfig
    ) -> bool:
        """删除文档"""
        pass

    @abstractmethod
    async def get_document(
        self,
        id: str,
        config: VectorStoreConfig
    ) -> Optional[Document]:
        """获取单个文档"""
        pass
```

#### 2.2.3 Agent 插件接口

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Dict, Any
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Agent 配置"""
    agent_type: str
    llm_provider: str
    llm_model: str
    system_prompt: Optional[str] = None
    tools: List[str] = []
    memory_enabled: bool = True
    max_iterations: int = 10

class AgentState(BaseModel):
    """Agent 状态"""
    thread_id: str
    messages: List[Dict[str, Any]] = []
    current_step: str = "idle"
    metadata: Dict[str, Any] = {}

class AgentPluginBase(ABC):
    """Agent 插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def run(
        self,
        input: str,
        config: AgentConfig,
        state: Optional[AgentState] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """运行 Agent (支持流式)"""
        pass

    @abstractmethod
    async def get_state(self, thread_id: str) -> AgentState:
        """获取 Agent 状态"""
        pass

    @abstractmethod
    async def update_state(
        self,
        thread_id: str,
        updates: Dict[str, Any]
    ) -> AgentState:
        """更新 Agent 状态"""
        pass

    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        pass
```

### 2.3 API 接口设计

#### 2.3.1 RESTful API 规范

```
基础路径: /api/v1

# LLM 管理
GET    /llm/providers          # 获取支持的 LLM 提供商
GET    /llm/models             # 获取支持的模型列表
POST   /llm/chat               # 发送聊天请求
POST   /llm/embed              # 生成嵌入向量

# Agent 管理
GET    /agent/types            # 获取 Agent 类型
POST   /agent/create           # 创建 Agent
POST   /agent/{id}/run         # 运行 Agent
GET    /agent/{id}/state       # 获取 Agent 状态
DELETE /agent/{id}             # 删除 Agent

# RAG 管理
POST   /rag/upload             # 上传文档
POST   /rag/embed              # 嵌入文档
POST   /rag/search             # 搜索文档
GET    /rag/collections        # 获取知识库列表
DELETE /rag/collection/{id}    # 删除知识库

# Tools 管理
GET    /tools                  # 获取可用工具
POST   /tools/custom           # 添加自定义工具
DELETE /tools/{id}             # 删除工具

# 配置管理
GET    /config                 # 获取当前配置
PUT    /config                 # 更新配置
POST   /config/llm             # 添加 LLM 配置
DELETE /config/llm/{id}        # 删除 LLM 配置

# 会话管理
GET    /sessions               # 获取会话列表
POST   /sessions               # 创建会话
GET    /sessions/{id}/messages # 获取会话消息
DELETE /sessions/{id}          # 删除会话
```

#### 2.3.2 WebSocket 接口

```python
# 连接: ws://localhost:8000/ws/chat/{session_id}

# 客户端消息格式
{
    "type": "chat" | "stop" | "update_config",
    "payload": {
        "message": "用户消息",
        "config": {...}  # 可选，更新配置
    }
}

# 服务端消息格式
{
    "type": "token" | "tool_call" | "error" | "done",
    "payload": {
        "content": "内容",
        "tool_name": "工具名",
        "tool_args": {...},
        "error": "错误信息"
    }
}
```

---

## 3. 桌面端架构设计 (Tauri)

### 3.1 目录结构

```
oagent-desktop/
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── build.rs
│   ├── src/
│   │   ├── main.rs
│   │   ├── lib.rs
│   │   ├── commands/          # Tauri Commands
│   │   │   ├── mod.rs
│   │   │   ├── llm.rs
│   │   │   ├── agent.rs
│   │   │   └── config.rs
│   │   ├── tray.rs            # 系统托盘
│   │   └── updater.rs         # 自动更新
│   └── icons/
├── src/                       # React 前端
│   ├── main.tsx
│   ├── App.tsx
│   ├── vite-env.d.ts
│   ├── components/
│   │   ├── ui/               # shadcn/ui 组件
│   │   ├── chat/
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── MessageItem.tsx
│   │   ├── config/
│   │   │   ├── LLMConfig.tsx
│   │   │   ├── AgentConfig.tsx
│   │   │   └── VectorStoreConfig.tsx
│   │   └── layout/
│   │       ├── Sidebar.tsx
│   │       ├── Header.tsx
│   │       └── MainLayout.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Chat.tsx
│   │   ├── Config.tsx
│   │   └── Knowledge.tsx
│   ├── stores/               # Zustand Stores
│   │   ├── chatStore.ts
│   │   ├── configStore.ts
│   │   └── sessionStore.ts
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useConfig.ts
│   │   └── useAgent.ts
│   ├── services/
│   │   ├── api.ts            # API 调用
│   │   └── websocket.ts       # WebSocket 连接
│   ├── types/
│   │   ├── llm.ts
│   │   ├── agent.ts
│   │   └── chat.ts
│   └── utils/
│       ├── format.ts
│       └── storage.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

### 3.2 Tauri 与 Python 后端通信

```rust
// src-tauri/src/commands/llm.rs
use tauri::command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct LLMConfig {
    pub provider: String,
    pub model: String,
    pub api_key: Option<String>,
}

#[command]
pub async fn get_llm_providers() -> Result<Vec<String>, String> {
    // 调用 Python 后端
    let response = reqwest::get("http://localhost:8000/api/v1/llm/providers")
        .await
        .map_err(|e| e.to_string())?;

    let providers: Vec<String> = response.json().await.map_err(|e| e.to_string())?;
    Ok(providers)
}

#[command]
pub async fn chat(config: LLMConfig, message: String) -> Result<String, String> {
    // WebSocket 或 HTTP 调用 Python 后端
    todo!()
}
```

### 3.3 前端状态管理 (Zustand)

```typescript
// src/stores/chatStore.ts
import { create } from 'zustand';
import { Message, AgentConfig } from '../types';

interface ChatState {
  messages: Message[];
  currentAgent: AgentConfig | null;
  isStreaming: boolean;

  // Actions
  addMessage: (message: Message) => void;
  updateMessage: (id: string, content: string) => void;
  setAgent: (agent: AgentConfig) => void;
  setStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  currentAgent: null,
  isStreaming: false,

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateMessage: (id, content) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, content } : m
      ),
    })),

  setAgent: (agent) => set({ currentAgent: agent }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  clearMessages: () => set({ messages: [] }),
}));
```

---

## 4. 插件系统设计

### 4.1 插件注册机制

```python
# src/oagent/core/registry.py
from typing import Dict, Type, Any
from pydantic import BaseModel

class PluginRegistry:
    """插件注册中心"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins: Dict[str, Dict[str, Type]] = {
                "llm": {},
                "embedding": {},
                "vectorstore": {},
                "rag": {},
                "agent": {},
                "tool": {},
            }
        return cls._instance

    def register(self, plugin_type: str, name: str, plugin_class: Type):
        """注册插件"""
        if plugin_type not in self._plugins:
            raise ValueError(f"Unknown plugin type: {plugin_type}")
        self._plugins[plugin_type][name] = plugin_class

    def get(self, plugin_type: str, name: str) -> Type:
        """获取插件类"""
        if plugin_type not in self._plugins:
            raise ValueError(f"Unknown plugin type: {plugin_type}")
        if name not in self._plugins[plugin_type]:
            raise ValueError(f"Plugin not found: {name}")
        return self._plugins[plugin_type][name]

    def list(self, plugin_type: str) -> Dict[str, Type]:
        """列出所有插件"""
        return self._plugins.get(plugin_type, {})

    def list_all(self) -> Dict[str, Dict[str, Type]]:
        """列出所有插件"""
        return self._plugins.copy()


# 装饰器方式注册
def register_plugin(plugin_type: str, name: str):
    """插件注册装饰器"""
    def decorator(cls):
        registry = PluginRegistry()
        registry.register(plugin_type, name, cls)
        return cls
    return decorator
```

### 4.2 插件使用示例

```python
# 注册 LLM 插件
@register_plugin("llm", "openai")
class OpenAILLMPlugin(LLMPluginBase):
    @property
    def name(self) -> str:
        return "openai"

    @property
    def supported_models(self) -> List[str]:
        return ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]

    async def chat(self, messages: List[Message], config: LLMConfig):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=config.api_key)
        # ... 实现聊天逻辑

# 使用插件
registry = PluginRegistry()
OpenAIPlugin = registry.get("llm", "openai")
llm = OpenAIPlugin()
async for token in llm.chat(messages, config):
    print(token, end="")
```

---

## 5. 数据模型设计

### 5.1 SQLite 数据库 Schema

```sql
-- LLM 配置
CREATE TABLE llm_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    api_key_encrypted TEXT,
    base_url TEXT,
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2048,
    top_p REAL DEFAULT 1.0,
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent 配置
CREATE TABLE agent_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    llm_config_id TEXT,
    system_prompt TEXT,
    tools TEXT,  -- JSON array
    memory_enabled BOOLEAN DEFAULT 1,
    max_iterations INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (llm_config_id) REFERENCES llm_configs(id)
);

-- 会话
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    agent_config_id TEXT,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_config_id) REFERENCES agent_configs(id)
);

-- 消息
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_calls TEXT,  -- JSON
    tool_call_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- 知识库
CREATE TABLE knowledge_bases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    vectorstore_provider TEXT NOT NULL,
    embedding_provider TEXT NOT NULL,
    collection_name TEXT NOT NULL,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    knowledge_base_id TEXT NOT NULL,
    filename TEXT,
    content TEXT,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id)
);

-- 配置
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. 安全设计

### 6.1 API Key 加密存储

```python
# src/oagent/utils/crypto.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class CryptoManager:
    """加密管理器"""

    def __init__(self, password: str = None):
        if password is None:
            password = os.environ.get("OAGENT_SECRET", "default_secret")
        self._fernet = self._derive_key(password)

    def _derive_key(self, password: str) -> Fernet:
        """从密码派生密钥"""
        salt = b"oagent_salt"  # 实际使用时应该安全存储
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """加密数据"""
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        return self._fernet.decrypt(encrypted_data.encode()).decode()
```

### 6.2 API 认证

```python
# src/oagent/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)):
    """验证 API Key"""
    # 从配置或环境变量获取有效的 API Keys
    valid_keys = os.environ.get("OAGENT_API_KEYS", "").split(",")
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key
```

---

## 7. 性能优化策略

### 7.1 异步架构

```python
# 全异步设计
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    # 异步 LLM 调用
    async for token in llm_service.stream_chat(request):
        yield token
```

### 7.2 连接池

```python
# 向量库连接池
from contextlib import asynccontextmanager

class VectorStorePool:
    def __init__(self, max_connections: int = 10):
        self._pool = asyncio.Queue(max_connections)

    async def get_connection(self):
        return await self._pool.get()

    async def return_connection(self, conn):
        await self._pool.put(conn)
```

### 7.3 缓存策略

```python
from functools import lru_cache
from cachetools import TTLCache

# 嵌入缓存
embedding_cache = TTLCache(maxsize=1000, ttl=3600)

@lru_cache(maxsize=100)
def get_llm_instance(provider: str, model: str):
    """LLM 实例缓存"""
    return create_llm_instance(provider, model)
```

---

## 8. 测试策略

### 8.1 单元测试

```python
# tests/test_llm/test_openai.py
import pytest
from unittest.mock import AsyncMock, patch

from oagent.plugins.llm.openai import OpenAILLMPlugin
from oagent.models.llm import LLMConfig, Message

@pytest.fixture
def llm_plugin():
    return OpenAILLMPlugin()

@pytest.fixture
def mock_config():
    return LLMConfig(
        provider="openai",
        model_name="gpt-4",
        api_key="test_key"
    )

@pytest.mark.asyncio
async def test_chat(llm_plugin, mock_config):
    messages = [Message(role="user", content="Hello")]

    with patch("openai.AsyncOpenAI") as mock_client:
        # Mock the response
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=MockResponse("Hello!")
        )

        response = await llm_plugin.chat(messages, mock_config)
        assert response is not None
```

### 8.2 集成测试

```python
# tests/test_api/test_chat.py
import pytest
from httpx import AsyncClient
from oagent.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_chat_endpoint(client):
    response = await client.post(
        "/api/v1/llm/chat",
        json={
            "provider": "openai",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }
    )
    assert response.status_code == 200
```

---

## 9. 部署方案

### 9.1 开发环境

```bash
# 后端
cd oagent-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
uvicorn oagent.main:app --reload

# 桌面端
cd oagent-desktop
npm install
npm run tauri dev
```

### 9.2 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/
RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "oagent.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.3 打包发布

```bash
# Tauri 打包
npm run tauri build

# 输出
# - Windows: .msi, .exe
# - macOS: .dmg, .app
# - Linux: .deb, .AppImage
```

---

## 10. 版本规划

| 版本 | 功能范围 | 预计时间 |
|-----|---------|---------|
| v0.1.0 | MVP: 基础对话、单一LLM | 2周 |
| v0.2.0 | 多LLM支持、向量库集成 | 2周 |
| v0.3.0 | RAG能力、工具系统 | 2周 |
| v0.4.0 | 多Agent类型、LangGraph | 2周 |
| v0.5.0 | 桌面端完善、配置管理 | 2周 |
| v1.0.0 | 生产就绪、文档完善 | 2周 |