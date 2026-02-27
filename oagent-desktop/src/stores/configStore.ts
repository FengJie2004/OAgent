/**
 * Configuration Store with API Integration
 *
 * Manages LLM and Agent configurations with both local state
 * and backend API synchronization.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  LLMConfig as ApiLLMConfig,
  AgentConfig as ApiAgentConfig,
  VectorStoreConfig,
  VectorStoreInfo,
  LLMConfigCreate,
} from '../lib/types'
import { api } from '../lib/api'

// ============================================================================
// Type Aliases for Local Store (camelCase for consistency)
// ============================================================================

export interface LLMConfig {
  id: string
  name: string
  provider: string
  modelName: string
  apiKey?: string
  baseUrl?: string
  temperature: number
  maxTokens: number
  topP?: number
  frequencyPenalty?: number
  presencePenalty?: number
  stream?: boolean
  isDefault: boolean
}

export interface AgentConfig {
  id: string
  name: string
  agentType: string
  llmProvider: string
  llmModel: string
  llmConfigId?: string
  systemPrompt?: string
  tools: string[]
  maxIterations: number
  memoryEnabled: boolean
  memoryType: string
  memoryWindow: number
  temperature: number
  maxTokens: number
  isDefault: boolean
  metadata?: Record<string, unknown>
}

export interface VectorStoreState {
  id: string
  name: string
  provider: 'chroma' | 'milvus' | 'faiss' | 'pinecone'
  collectionName: string
  connectionString?: string
  apiKey?: string
  embeddingModel?: string
  embeddingProvider?: string
  dimension?: number
  documentCount?: number
  isDefault: boolean
}

// ============================================================================
// Store State Interface
// ============================================================================

interface ConfigState {
  // State
  llmConfigs: LLMConfig[]
  agentConfigs: AgentConfig[]
  vectorStores: VectorStoreState[]
  defaultLLMConfigId: string | null
  defaultAgentConfigId: string | null
  defaultVectorStoreId: string | null

  // Loading states
  isLoading: boolean
  isSaving: boolean
  error: string | null

  // LLM Config Actions
  fetchLLMConfigs: () => Promise<void>
  createLLMConfig: (config: Omit<LLMConfig, 'id' | 'isDefault'>) => Promise<LLMConfig>
  updateLLMConfig: (id: string, config: Partial<LLMConfig>) => Promise<void>
  deleteLLMConfig: (id: string) => Promise<void>
  setDefaultLLMConfig: (id: string) => Promise<void>
  getLLMConfig: (id: string) => LLMConfig | undefined

  // Agent Config Actions
  fetchAgentConfigs: () => Promise<void>
  createAgentConfig: (config: Omit<AgentConfig, 'id' | 'isDefault'>) => Promise<AgentConfig>
  updateAgentConfig: (id: string, config: Partial<AgentConfig>) => Promise<void>
  deleteAgentConfig: (id: string) => Promise<void>
  setDefaultAgentConfig: (id: string) => Promise<void>
  getAgentConfig: (id: string) => AgentConfig | undefined

  // Vector Store Actions
  fetchVectorStores: () => Promise<void>
  createVectorStore: (config: Omit<VectorStoreState, 'id' | 'isDefault'>) => Promise<VectorStoreState>
  updateVectorStore: (id: string, config: Partial<VectorStoreState>) => Promise<void>
  deleteVectorStore: (id: string) => Promise<void>
  setDefaultVectorStore: (id: string) => Promise<void>
  getVectorStore: (id: string) => VectorStoreState | undefined

  // Utility Actions
  clearError: () => void
  setLoading: (loading: boolean) => void
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Transform API LLMConfig to local store format
 */
function transformLLMConfig(config: ApiLLMConfig): LLMConfig {
  return {
    id: config.id || '',
    name: config.name || '',
    provider: config.provider,
    modelName: config.model_name,
    apiKey: config.api_key,
    baseUrl: config.base_url,
    temperature: config.temperature,
    maxTokens: config.max_tokens,
    topP: config.top_p,
    frequencyPenalty: config.frequency_penalty,
    presencePenalty: config.presence_penalty,
    stream: config.stream,
    isDefault: config.is_default,
  }
}

/**
 * Transform local LLMConfig to API format
 */
function transformLLMConfigToApi(config: Omit<LLMConfig, 'id' | 'isDefault'>): LLMConfigCreate {
  return {
    name: config.name || '',
    provider: config.provider,
    model_name: config.modelName,
    api_key: config.apiKey,
    base_url: config.baseUrl,
    temperature: config.temperature,
    max_tokens: config.maxTokens,
    is_default: false,
  }
}

/**
 * Transform API AgentConfig to local store format
 */
function transformAgentConfig(config: ApiAgentConfig): AgentConfig {
  return {
    id: config.id || '',
    name: config.name || '',
    agentType: config.agent_type,
    llmProvider: config.llm_provider,
    llmModel: config.llm_model,
    llmConfigId: config.llm_config_id,
    systemPrompt: config.system_prompt,
    tools: config.tools,
    maxIterations: config.max_iterations,
    memoryEnabled: config.memory_enabled,
    memoryType: config.memory_type,
    memoryWindow: config.memory_window,
    temperature: config.temperature,
    maxTokens: config.max_tokens,
    isDefault: config.is_default,
    metadata: config.metadata,
  }
}

/**
 * Transform local AgentConfig to API format
 */
function transformAgentConfigToApi(config: Omit<AgentConfig, 'id' | 'isDefault'>): Omit<ApiAgentConfig, 'id'> {
  return {
    name: config.name || '',
    agent_type: config.agentType,
    llm_provider: config.llmProvider,
    llm_model: config.llmModel,
    llm_config_id: config.llmConfigId,
    system_prompt: config.systemPrompt,
    tools: config.tools,
    max_iterations: config.maxIterations,
    memory_enabled: config.memoryEnabled,
    memory_type: config.memoryType,
    memory_window: config.memoryWindow,
    temperature: config.temperature,
    max_tokens: config.maxTokens,
    is_default: false,
    metadata: config.metadata,
  }
}

/**
 * Transform API VectorStoreInfo to local store format
 */
function transformVectorStore(store: VectorStoreInfo): VectorStoreState {
  return {
    id: store.id,
    name: store.name,
    provider: store.provider as VectorStoreState['provider'],
    collectionName: store.collection_name,
    documentCount: store.document_count,
    isDefault: false, // Will be set by store
  }
}

// ============================================================================
// Store Implementation
// ============================================================================

export const useConfigStore = create<ConfigState>()(
  persist(
    (set, get) => ({
      // Initial State
      llmConfigs: [],
      agentConfigs: [],
      vectorStores: [],
      defaultLLMConfigId: null,
      defaultAgentConfigId: null,
      defaultVectorStoreId: null,

      isLoading: false,
      isSaving: false,
      error: null,

      // Utility Actions
      clearError: () => set({ error: null }),

      setLoading: (loading) => set({ isLoading: loading }),

      // ========================================================================
      // LLM Config Actions
      // ========================================================================

      fetchLLMConfigs: async () => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.config.listLLMConfigs()
          const configs = response.configs.map(transformLLMConfig)
          const defaultId = response.default

          set({
            llmConfigs: configs,
            defaultLLMConfigId: defaultId,
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch LLM configs',
            isLoading: false,
          })
          throw error
        }
      },

      createLLMConfig: async (config) => {
        set({ isSaving: true, error: null })
        try {
          const apiConfig = transformLLMConfigToApi(config)
          const response = await api.config.createLLMConfig(apiConfig)

          const newConfig: LLMConfig = {
            ...transformLLMConfig({ ...response.config, id: response.id }),
            isDefault: false,
          }

          set((state) => ({
            llmConfigs: [...state.llmConfigs, newConfig],
            isSaving: false,
          }))

          return newConfig
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create LLM config',
            isSaving: false,
          })
          throw error
        }
      },

      updateLLMConfig: async (id, config) => {
        set({ isSaving: true, error: null })
        try {
          await api.config.updateLLMConfig(id, config)

          set((state) => ({
            llmConfigs: state.llmConfigs.map((c) =>
              c.id === id ? { ...c, ...config } : c
            ),
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update LLM config',
            isSaving: false,
          })
          throw error
        }
      },

      deleteLLMConfig: async (id) => {
        set({ isSaving: true, error: null })
        try {
          await api.config.deleteLLMConfig(id)

          set((state) => ({
            llmConfigs: state.llmConfigs.filter((c) => c.id !== id),
            defaultLLMConfigId: state.defaultLLMConfigId === id ? null : state.defaultLLMConfigId,
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete LLM config',
            isSaving: false,
          })
          throw error
        }
      },

      setDefaultLLMConfig: async (id) => {
        set({ isSaving: true, error: null })
        try {
          await api.config.setDefaultLLMConfig(id)

          set((state) => ({
            llmConfigs: state.llmConfigs.map((c) => ({
              ...c,
              isDefault: c.id === id,
            })),
            defaultLLMConfigId: id,
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to set default LLM config',
            isSaving: false,
          })
          throw error
        }
      },

      getLLMConfig: (id) => {
        return get().llmConfigs.find((c) => c.id === id)
      },

      // ========================================================================
      // Agent Config Actions
      // ========================================================================

      fetchAgentConfigs: async () => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.config.listAgentConfigs()
          const configs = response.configs.map(transformAgentConfig)
          const defaultId = response.default

          set({
            agentConfigs: configs,
            defaultAgentConfigId: defaultId,
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch Agent configs',
            isLoading: false,
          })
          throw error
        }
      },

      createAgentConfig: async (config) => {
        set({ isSaving: true, error: null })
        try {
          const apiConfig = transformAgentConfigToApi(config)
          const response = await api.config.createAgentConfig(apiConfig)

          const newConfig: AgentConfig = {
            ...transformAgentConfig({ ...response.config, id: response.id }),
            isDefault: false,
          }

          set((state) => ({
            agentConfigs: [...state.agentConfigs, newConfig],
            isSaving: false,
          }))

          return newConfig
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create Agent config',
            isSaving: false,
          })
          throw error
        }
      },

      updateAgentConfig: async (id, config) => {
        set({ isSaving: true, error: null })
        try {
          await api.config.updateAgentConfig(id, config)

          set((state) => ({
            agentConfigs: state.agentConfigs.map((c) =>
              c.id === id ? { ...c, ...config } : c
            ),
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update Agent config',
            isSaving: false,
          })
          throw error
        }
      },

      deleteAgentConfig: async (id) => {
        set({ isSaving: true, error: null })
        try {
          await api.config.deleteAgentConfig(id)

          set((state) => ({
            agentConfigs: state.agentConfigs.filter((c) => c.id !== id),
            defaultAgentConfigId: state.defaultAgentConfigId === id ? null : state.defaultAgentConfigId,
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete Agent config',
            isSaving: false,
          })
          throw error
        }
      },

      setDefaultAgentConfig: async (id) => {
        set({ isSaving: true, error: null })
        try {
          await api.config.setDefaultAgentConfig(id)

          set((state) => ({
            agentConfigs: state.agentConfigs.map((c) => ({
              ...c,
              isDefault: c.id === id,
            })),
            defaultAgentConfigId: id,
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to set default Agent config',
            isSaving: false,
          })
          throw error
        }
      },

      getAgentConfig: (id) => {
        return get().agentConfigs.find((c) => c.id === id)
      },

      // ========================================================================
      // Vector Store Actions
      // ========================================================================

      fetchVectorStores: async () => {
        set({ isLoading: true, error: null })
        try {
          const stores = await api.vector.listStores()
          const transformedStores = stores.map(transformVectorStore)

          set({
            vectorStores: transformedStores,
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch Vector stores',
            isLoading: false,
          })
          throw error
        }
      },

      createVectorStore: async (config) => {
        set({ isSaving: true, error: null })
        try {
          const apiConfig: VectorStoreConfig = {
            name: config.name,
            provider: config.provider,
            collection_name: config.collectionName,
            connection_string: config.connectionString,
            api_key: config.apiKey,
            embedding_model: config.embeddingModel,
            embedding_provider: config.embeddingProvider,
            dimension: config.dimension,
            is_default: false,
          }

          const response = await api.vector.createStore(apiConfig)
          const newStore = transformVectorStore(response)

          set((state) => ({
            vectorStores: [...state.vectorStores, newStore],
            isSaving: false,
          }))

          return newStore
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create Vector store',
            isSaving: false,
          })
          throw error
        }
      },

      updateVectorStore: async (id, config) => {
        set({ isSaving: true, error: null })
        try {
          await api.vector.updateStore(id, config)

          set((state) => ({
            vectorStores: state.vectorStores.map((s) =>
              s.id === id ? { ...s, ...config } : s
            ),
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update Vector store',
            isSaving: false,
          })
          throw error
        }
      },

      deleteVectorStore: async (id) => {
        set({ isSaving: true, error: null })
        try {
          await api.vector.deleteStore(id)

          set((state) => ({
            vectorStores: state.vectorStores.filter((s) => s.id !== id),
            defaultVectorStoreId: state.defaultVectorStoreId === id ? null : state.defaultVectorStoreId,
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete Vector store',
            isSaving: false,
          })
          throw error
        }
      },

      setDefaultVectorStore: async (id) => {
        set({ isSaving: true, error: null })
        try {
          // Note: This assumes the API supports setting default vector store
          // If not implemented on backend, this will just update local state
          set((state) => ({
            vectorStores: state.vectorStores.map((s) => ({
              ...s,
              isDefault: s.id === id,
            })),
            defaultVectorStoreId: id,
            isSaving: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to set default Vector store',
            isSaving: false,
          })
          throw error
        }
      },

      getVectorStore: (id) => {
        return get().vectorStores.find((s) => s.id === id)
      },
    }),
    {
      name: 'oagent-config-store',
      // Only persist the configs, not loading states
      partialize: (state) => ({
        llmConfigs: state.llmConfigs,
        agentConfigs: state.agentConfigs,
        vectorStores: state.vectorStores,
        defaultLLMConfigId: state.defaultLLMConfigId,
        defaultAgentConfigId: state.defaultAgentConfigId,
        defaultVectorStoreId: state.defaultVectorStoreId,
      }),
    }
  )
)

// ============================================================================
// Convenience Hooks (to be used with React Query)
// ============================================================================

/**
 * Get the default LLM config
 */
export const getDefaultLLMConfig = (): LLMConfig | undefined => {
  const state = useConfigStore.getState()
  return state.llmConfigs.find((c) => c.isDefault) || state.llmConfigs[0]
}

/**
 * Get the default Agent config
 */
export const getDefaultAgentConfig = (): AgentConfig | undefined => {
  const state = useConfigStore.getState()
  return state.agentConfigs.find((c) => c.isDefault) || state.agentConfigs[0]
}

/**
 * Get the default Vector store
 */
export const getDefaultVectorStore = (): VectorStoreState | undefined => {
  const state = useConfigStore.getState()
  return state.vectorStores.find((s) => s.isDefault) || state.vectorStores[0]
}
