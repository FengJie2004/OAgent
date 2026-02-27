/**
 * TypeScript types for OAgent Desktop API
 * Aligned with backend Pydantic models
 */

// ============================================================================
// LLM Types
// ============================================================================

export interface LLMConfig {
  id?: string
  name?: string
  provider: string
  model_name: string
  api_key?: string
  base_url?: string
  temperature: number
  max_tokens: number
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
  stream?: boolean
  is_default: boolean
}

export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
  name?: string
  tool_call_id?: string
  tool_calls?: ToolCall[]
}

export interface ToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
}

export interface ChatRequest {
  messages: Message[]
  config?: LLMConfig
  stream: boolean
}

export interface ChatResponse {
  content: string
  model: string
  provider: string
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  finish_reason?: string
}

export interface EmbeddingRequest {
  texts: string[]
  model?: string
  provider?: string
}

export interface EmbeddingResponse {
  embeddings: number[][]
  model: string
  provider: string
  dimension: number
}

export interface ProviderResponse {
  providers: string[]
  default: string
}

export interface ModelResponse {
  provider: string
  models: string[]
}

// ============================================================================
// Agent Types
// ============================================================================

export interface AgentConfig {
  id?: string
  name?: string
  agent_type: string
  llm_provider: string
  llm_model: string
  llm_config_id?: string
  system_prompt?: string
  tools: string[]
  max_iterations: number
  memory_enabled: boolean
  memory_type: string
  memory_window: number
  temperature: number
  max_tokens: number
  is_default: boolean
  metadata?: Record<string, unknown>
}

export interface AgentState {
  thread_id: string
  messages: Record<string, unknown>[]
  current_step: string
  metadata?: Record<string, unknown>
}

export interface AgentRunRequest {
  input: string
  config?: AgentConfig
  config_id?: string
  thread_id?: string
  stream: boolean
}

export interface AgentRunResponse {
  output: string
  thread_id: string
  agent_type: string
  tool_calls: ToolCall[]
  metadata?: Record<string, unknown>
}

export interface AgentTypeResponse {
  types: string[]
  descriptions: Record<string, string>
}

export interface ToolInfo {
  name: string
  description: string
  parameters?: Record<string, unknown>
}

export interface ToolsResponse {
  tools: ToolInfo[]
}

// ============================================================================
// Chat Session Types
// ============================================================================

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  tool_name?: string
  tool_args?: Record<string, unknown>
  tool_result?: string
  created_at: string
}

export interface ChatSession {
  id: string
  title?: string
  agent_config_id?: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
}

export interface CreateSessionRequest {
  title?: string
  agent_config_id?: string
}

export interface SessionListResponse {
  sessions: ChatSession[]
  total: number
}

// ============================================================================
// Vector Store Types
// ============================================================================

export interface VectorStoreConfig {
  id?: string
  name: string
  provider: 'chroma' | 'milvus' | 'faiss' | 'pinecone'
  collection_name: string
  connection_string?: string
  api_key?: string
  embedding_model?: string
  embedding_provider?: string
  dimension?: number
  metadata?: Record<string, unknown>
  is_default: boolean
}

export interface VectorStoreInfo {
  id: string
  name: string
  provider: string
  collection_name: string
  document_count: number
  created_at: string
  updated_at: string
}

export interface VectorStoreResponse {
  stores: VectorStoreInfo[]
  total: number
}

// ============================================================================
// Knowledge/RAG Types
// ============================================================================

export interface Document {
  id: string
  content: string
  metadata: Record<string, unknown>
  embedding?: number[]
  source?: string
  created_at: string
}

export interface UploadDocumentRequest {
  content: string
  metadata?: Record<string, unknown>
  vector_store_id: string
}

export interface UploadDocumentResponse {
  document: Document
  message: string
}

export interface SearchRequest {
  query: string
  vector_store_id: string
  limit?: number
  filter?: Record<string, unknown>
}

export interface SearchResult {
  document: Document
  score: number
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  query: string
}

// ============================================================================
// Config Types
// ============================================================================

export interface AppConfig {
  app_name: string
  app_version: string
  default_llm_provider: string
  default_llm_model: string
  default_embedding_provider: string
  default_embedding_model: string
  default_agent_type: string
}

export interface LLMConfigCreate {
  name: string
  provider: string
  model_name: string
  api_key?: string
  base_url?: string
  temperature?: number
  max_tokens?: number
  is_default?: boolean
}

export interface LLMConfigUpdate {
  name?: string
  provider?: string
  model_name?: string
  api_key?: string
  base_url?: string
  temperature?: number
  max_tokens?: number
  is_default?: boolean
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
  success: boolean
}

export interface ApiError {
  status: number
  message: string
  details?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

// ============================================================================
// Streaming Types
// ============================================================================

export interface StreamEvent {
  type: 'token' | 'done' | 'error' | 'tool_call' | 'thought'
  data: string | unknown
  timestamp: number
}

export type StreamHandler = (event: StreamEvent) => void

export interface StreamOptions {
  onToken?: (token: string) => void
  onComplete?: (content: string) => void
  onError?: (error: Error) => void
  onToolCall?: (toolCall: ToolCall) => void
}
