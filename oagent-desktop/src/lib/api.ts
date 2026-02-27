/**
 * OAgent Desktop API Client
 *
 * Provides methods for interacting with the OAgent backend API.
 * Supports streaming responses, error handling, and TypeScript strict mode.
 */

import type {
  // LLM Types
  LLMConfig,
  ChatResponse,
  EmbeddingRequest,
  EmbeddingResponse,
  ProviderResponse,
  ModelResponse,
  Message,
  // Agent Types
  AgentConfig,
  AgentRunRequest,
  AgentRunResponse,
  AgentTypeResponse,
  ToolsResponse,
  // Chat Session Types
  ChatSession,
  ChatMessage,
  CreateSessionRequest,
  // Vector Store Types
  VectorStoreConfig,
  VectorStoreInfo,
  VectorStoreResponse,
  // Knowledge/RAG Types
  UploadDocumentRequest,
  UploadDocumentResponse,
  SearchRequest,
  SearchResponse,
  // Config Types
  AppConfig,
  LLMConfigCreate,
  LLMConfigUpdate,
  // Streaming Types
  StreamOptions,
  StreamEvent,
} from './types'

// ============================================================================
// Configuration
// ============================================================================

export interface ApiClientConfig {
  baseUrl: string
  timeout: number
  defaultHeaders?: Record<string, string>
}

const DEFAULT_CONFIG: ApiClientConfig = {
  baseUrl: 'http://localhost:8000/api/v1',
  timeout: 30000,
}

// ============================================================================
// Error Classes
// ============================================================================

export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'NetworkError'
  }
}

export class TimeoutError extends Error {
  constructor() {
    super('Request timed out')
    this.name = 'TimeoutError'
  }
}

// ============================================================================
// API Client Class
// ============================================================================

export class ApiClient {
  private baseUrl: string
  private timeout: number
  private defaultHeaders: Record<string, string>

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.baseUrl = config.baseUrl ?? DEFAULT_CONFIG.baseUrl
    this.timeout = config.timeout ?? DEFAULT_CONFIG.timeout
    this.defaultHeaders = config.defaultHeaders ?? {}
  }

  /**
   * Update the base URL
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url
  }

  /**
   * Generic request handler with error handling
   */
  public async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...this.defaultHeaders,
      ...options.headers,
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new ApiClientError(
          errorData.detail || errorData.message || `HTTP ${response.status}`,
          response.status,
          errorData
        )
      }

      // Handle empty responses
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return {} as T
      }

      return await response.json()
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof ApiClientError) {
        throw error
      }

      if (error instanceof Error && error.name === 'AbortError') {
        throw new TimeoutError()
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new NetworkError('Failed to connect to the server')
      }

      throw new NetworkError(error instanceof Error ? error.message : 'Unknown error')
    }
  }

  /**
   * Stream response handler for Server-Sent Events
   */
  public async *streamRequest(
    endpoint: string,
    options: RequestInit = {}
  ): AsyncGenerator<string, void, unknown> {
    const url = `${this.baseUrl}${endpoint}`

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...this.defaultHeaders,
      ...options.headers,
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new ApiClientError(
          errorData.detail || errorData.message || `HTTP ${response.status}`,
          response.status,
          errorData
        )
      }

      if (!response.body) {
        throw new NetworkError('Response body is null')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        buffer += decoder.decode(value, { stream: true })

        // Parse SSE format (data: {...}\n\n)
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              return
            }
            yield data
          }
        }
      }
    } catch (error) {
      clearTimeout(timeoutId)
      throw error
    }
  }
}

// ============================================================================
// LLM API
// ============================================================================

export class LlmApi {
  constructor(private client: ApiClient) {}

  /**
   * Get available LLM providers
   */
  async getProviders(): Promise<ProviderResponse> {
    return this.client.request<ProviderResponse>('/llm/providers')
  }

  /**
   * Get available models for a provider
   */
  async getModels(provider: string): Promise<ModelResponse> {
    return this.client.request<ModelResponse>(`/llm/models/${provider}`)
  }

  /**
   * Chat with LLM (non-streaming)
   */
  async chat(messages: Message[], config?: LLMConfig): Promise<ChatResponse> {
    return this.client.request<ChatResponse>('/llm/chat', {
      method: 'POST',
      body: JSON.stringify({ messages, config, stream: false }),
    })
  }

  /**
   * Chat with LLM (streaming)
   */
  async *chatStream(
    messages: Message[],
    config?: LLMConfig,
    options?: StreamOptions
  ): AsyncGenerator<StreamEvent, void, unknown> {
    try {
      for await (const chunk of this.client.streamRequest('/llm/chat', {
        method: 'POST',
        body: JSON.stringify({ messages, config, stream: true }),
      })) {
        try {
          const data = JSON.parse(chunk)
          yield {
            type: 'token',
            data: data.content || data,
            timestamp: Date.now(),
          }
          options?.onToken?.(data.content || data)
        } catch {
          // Non-JSON chunk (raw text)
          yield {
            type: 'token',
            data: chunk,
            timestamp: Date.now(),
          }
          options?.onToken?.(chunk)
        }
      }
      yield {
        type: 'done',
        data: null,
        timestamp: Date.now(),
      }
    } catch (error) {
      yield {
        type: 'error',
        data: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
      }
      options?.onError?.(error instanceof Error ? error : new Error(String(error)))
      throw error
    }
  }

  /**
   * Generate embeddings for texts
   */
  async embed(request: EmbeddingRequest): Promise<EmbeddingResponse> {
    return this.client.request<EmbeddingResponse>('/llm/embed', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }
}

// ============================================================================
// Agent API
// ============================================================================

export class AgentApi {
  constructor(private client: ApiClient) {}

  /**
   * Get available agent types
   */
  async getAgentTypes(): Promise<AgentTypeResponse> {
    return this.client.request<AgentTypeResponse>('/agent/types')
  }

  /**
   * Get available tools
   */
  async getTools(): Promise<ToolsResponse> {
    return this.client.request<ToolsResponse>('/agent/tools')
  }

  /**
   * Run an agent (non-streaming)
   */
  async run(request: AgentRunRequest): Promise<AgentRunResponse> {
    return this.client.request<AgentRunResponse>('/agent/run', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Run an agent (streaming)
   */
  async *runStream(
    request: AgentRunRequest,
    options?: StreamOptions
  ): AsyncGenerator<StreamEvent, void, unknown> {
    try {
      for await (const chunk of this.client.streamRequest('/agent/run', {
        method: 'POST',
        body: JSON.stringify({ ...request, stream: true }),
      })) {
        try {
          const data = JSON.parse(chunk)

          if (data.tool_call) {
            yield {
              type: 'tool_call',
              data: data.tool_call,
              timestamp: Date.now(),
            }
            options?.onToolCall?.(data.tool_call)
          } else if (data.thought) {
            yield {
              type: 'thought',
              data: data.thought,
              timestamp: Date.now(),
            }
          } else {
            yield {
              type: 'token',
              data: data.output || data,
              timestamp: Date.now(),
            }
            options?.onToken?.(data.output || data)
          }
        } catch {
          yield {
            type: 'token',
            data: chunk,
            timestamp: Date.now(),
          }
          options?.onToken?.(chunk)
        }
      }
      yield {
        type: 'done',
        data: null,
        timestamp: Date.now(),
      }
    } catch (error) {
      yield {
        type: 'error',
        data: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
      }
      options?.onError?.(error instanceof Error ? error : new Error(String(error)))
      throw error
    }
  }
}

// ============================================================================
// Chat API
// ============================================================================

export class ChatApi {
  constructor(private client: ApiClient) {}

  /**
   * List all chat sessions
   */
  async listSessions(): Promise<ChatSession[]> {
    return this.client.request<ChatSession[]>('/chat/sessions')
  }

  /**
   * Create a new chat session
   */
  async createSession(request: CreateSessionRequest): Promise<ChatSession> {
    return this.client.request<ChatSession>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Get a chat session by ID
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    return this.client.request<ChatSession>(`/chat/sessions/${sessionId}`)
  }

  /**
   * Get messages for a session
   */
  async getMessages(sessionId: string): Promise<ChatMessage[]> {
    const session = await this.getSession(sessionId)
    return session.messages || []
  }

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.client.request<void>(`/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    })
  }

  /**
   * Send a message to a session (non-streaming)
   */
  async sendMessage(
    sessionId: string,
    message: string,
    agentConfigId?: string
  ): Promise<ChatMessage> {
    return this.client.request<ChatMessage>('/chat/send', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        message,
        agent_config_id: agentConfigId,
        stream: false,
      }),
    })
  }

  /**
   * Send a message to a session (streaming)
   */
  async *sendMessageStream(
    sessionId: string,
    message: string,
    agentConfigId?: string,
    options?: StreamOptions
  ): AsyncGenerator<StreamEvent, ChatMessage, unknown> {
    let accumulatedContent = ''

    try {
      for await (const chunk of this.client.streamRequest('/chat/send', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          message,
          agent_config_id: agentConfigId,
          stream: true,
        }),
      })) {
        try {
          const data = JSON.parse(chunk)
          accumulatedContent += data.content || data

          yield {
            type: 'token',
            data: data.content || data,
            timestamp: Date.now(),
          }
          options?.onToken?.(data.content || data)
        } catch {
          accumulatedContent += chunk
          yield {
            type: 'token',
            data: chunk,
            timestamp: Date.now(),
          }
          options?.onToken?.(chunk)
        }
      }

      yield {
        type: 'done',
        data: null,
        timestamp: Date.now(),
      }
      options?.onComplete?.(accumulatedContent)

      // Return the final message
      return {
        id: Date.now().toString(),
        session_id: sessionId,
        role: 'assistant',
        content: accumulatedContent,
        created_at: new Date().toISOString(),
      }
    } catch (error) {
      yield {
        type: 'error',
        data: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
      }
      options?.onError?.(error instanceof Error ? error : new Error(String(error)))
      throw error
    }
  }
}

// ============================================================================
// Vector Store API
// ============================================================================

export class VectorStoreApi {
  constructor(private client: ApiClient) {}

  /**
   * List all vector stores
   */
  async listStores(): Promise<VectorStoreInfo[]> {
    const response = await this.client.request<VectorStoreResponse>('/vector/stores')
    return response.stores
  }

  /**
   * Get a vector store by ID
   */
  async getStore(storeId: string): Promise<VectorStoreInfo> {
    return this.client.request<VectorStoreInfo>(`/vector/stores/${storeId}`)
  }

  /**
   * Create a new vector store
   */
  async createStore(config: VectorStoreConfig): Promise<VectorStoreInfo> {
    return this.client.request<VectorStoreInfo>('/vector/stores', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  /**
   * Update a vector store
   */
  async updateStore(
    storeId: string,
    config: Partial<VectorStoreConfig>
  ): Promise<VectorStoreInfo> {
    return this.client.request<VectorStoreInfo>(`/vector/stores/${storeId}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    })
  }

  /**
   * Delete a vector store
   */
  async deleteStore(storeId: string): Promise<void> {
    await this.client.request<void>(`/vector/stores/${storeId}`, {
      method: 'DELETE',
    })
  }

  /**
   * Upload a document to a vector store
   */
  async uploadDocument(
    request: UploadDocumentRequest
  ): Promise<UploadDocumentResponse> {
    return this.client.request<UploadDocumentResponse>('/vector/documents', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Search documents in a vector store
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.client.request<SearchResponse>('/vector/search', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }
}

// ============================================================================
// Config API
// ============================================================================

export class ConfigApi {
  constructor(private client: ApiClient) {}

  /**
   * Get application configuration
   */
  async getConfig(): Promise<AppConfig> {
    return this.client.request<AppConfig>('/config')
  }

  /**
   * List LLM configurations
   */
  async listLLMConfigs(): Promise<{ configs: LLMConfig[]; default: string | null }> {
    return this.client.request('/config/llm')
  }

  /**
   * Create an LLM configuration
   */
  async createLLMConfig(config: LLMConfigCreate): Promise<{
    id: string
    message: string
    config: LLMConfig
  }> {
    return this.client.request('/config/llm', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  /**
   * Update an LLM configuration
   */
  async updateLLMConfig(
    id: string,
    config: LLMConfigUpdate
  ): Promise<{
    id: string
    message: string
    config: LLMConfig
  }> {
    return this.client.request(`/config/llm/${id}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    })
  }

  /**
   * Delete an LLM configuration
   */
  async deleteLLMConfig(id: string): Promise<void> {
    await this.client.request<void>(`/config/llm/${id}`, {
      method: 'DELETE',
    })
  }

  /**
   * Set an LLM configuration as default
   */
  async setDefaultLLMConfig(id: string): Promise<void> {
    await this.client.request<void>(`/config/llm/${id}/default`, {
      method: 'POST',
    })
  }

  /**
   * List Agent configurations
   */
  async listAgentConfigs(): Promise<{ configs: AgentConfig[]; default: string | null }> {
    return this.client.request('/config/agent')
  }

  /**
   * Create an Agent configuration
   */
  async createAgentConfig(config: Omit<AgentConfig, 'id'>): Promise<{
    id: string
    message: string
    config: AgentConfig
  }> {
    return this.client.request('/config/agent', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  /**
   * Update an Agent configuration
   */
  async updateAgentConfig(
    id: string,
    config: Partial<AgentConfig>
  ): Promise<{
    id: string
    message: string
    config: AgentConfig
  }> {
    return this.client.request(`/config/agent/${id}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    })
  }

  /**
   * Delete an Agent configuration
   */
  async deleteAgentConfig(id: string): Promise<void> {
    await this.client.request<void>(`/config/agent/${id}`, {
      method: 'DELETE',
    })
  }

  /**
   * Set an Agent configuration as default
   */
  async setDefaultAgentConfig(id: string): Promise<void> {
    await this.client.request<void>(`/config/agent/${id}/default`, {
      method: 'POST',
    })
  }
}

// ============================================================================
// Main API Client Export
// ============================================================================

/**
 * OAgent API Client
 *
 * @example
 * ```typescript
 * const api = createApiClient()
 *
 * // Get LLM providers
 * const providers = await api.llm.getProviders()
 *
 * // Chat with streaming
 * for await (const event of api.llm.chatStream(messages)) {
 *   console.log(event.data)
 * }
 *
 * // List sessions
 * const sessions = await api.chat.listSessions()
 * ```
 */
export function createApiClient(config?: Partial<ApiClientConfig>): {
  llm: LlmApi
  agent: AgentApi
  chat: ChatApi
  vector: VectorStoreApi
  config: ConfigApi
  setBaseUrl: (url: string) => void
} {
  const client = new ApiClient(config)

  return {
    llm: new LlmApi(client),
    agent: new AgentApi(client),
    chat: new ChatApi(client),
    vector: new VectorStoreApi(client),
    config: new ConfigApi(client),
    setBaseUrl: (url: string) => client.setBaseUrl(url),
  }
}

// ============================================================================
// Default Export
// ============================================================================

export const api = createApiClient()
export default api
