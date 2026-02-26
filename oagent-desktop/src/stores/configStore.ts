import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LLMConfig {
  id: string
  name: string
  provider: string
  modelName: string
  apiKey?: string
  baseUrl?: string
  temperature: number
  maxTokens: number
  isDefault: boolean
}

interface AgentConfig {
  id: string
  name: string
  agentType: string
  llmConfigId: string
  systemPrompt?: string
  tools: string[]
  memoryEnabled: boolean
  isDefault: boolean
}

interface ConfigState {
  llmConfigs: LLMConfig[]
  agentConfigs: AgentConfig[]
  defaultLLMConfigId: string | null
  defaultAgentConfigId: string | null

  addLLMConfig: (config: Omit<LLMConfig, 'id'>) => void
  updateLLMConfig: (id: string, config: Partial<LLMConfig>) => void
  deleteLLMConfig: (id: string) => void
  setDefaultLLMConfig: (id: string) => void

  addAgentConfig: (config: Omit<AgentConfig, 'id'>) => void
  updateAgentConfig: (id: string, config: Partial<AgentConfig>) => void
  deleteAgentConfig: (id: string) => void
  setDefaultAgentConfig: (id: string) => void
}

export const useConfigStore = create<ConfigState>()(
  persist(
    (set) => ({
      llmConfigs: [],
      agentConfigs: [],
      defaultLLMConfigId: null,
      defaultAgentConfigId: null,

      addLLMConfig: (config) =>
        set((state) => ({
          llmConfigs: [
            ...state.llmConfigs,
            { ...config, id: Date.now().toString() },
          ],
        })),

      updateLLMConfig: (id, config) =>
        set((state) => ({
          llmConfigs: state.llmConfigs.map((c) =>
            c.id === id ? { ...c, ...config } : c
          ),
        })),

      deleteLLMConfig: (id) =>
        set((state) => ({
          llmConfigs: state.llmConfigs.filter((c) => c.id !== id),
          defaultLLMConfigId:
            state.defaultLLMConfigId === id ? null : state.defaultLLMConfigId,
        })),

      setDefaultLLMConfig: (id) =>
        set((state) => ({
          llmConfigs: state.llmConfigs.map((c) => ({
            ...c,
            isDefault: c.id === id,
          })),
          defaultLLMConfigId: id,
        })),

      addAgentConfig: (config) =>
        set((state) => ({
          agentConfigs: [
            ...state.agentConfigs,
            { ...config, id: Date.now().toString() },
          ],
        })),

      updateAgentConfig: (id, config) =>
        set((state) => ({
          agentConfigs: state.agentConfigs.map((c) =>
            c.id === id ? { ...c, ...config } : c
          ),
        })),

      deleteAgentConfig: (id) =>
        set((state) => ({
          agentConfigs: state.agentConfigs.filter((c) => c.id !== id),
          defaultAgentConfigId:
            state.defaultAgentConfigId === id
              ? null
              : state.defaultAgentConfigId,
        })),

      setDefaultAgentConfig: (id) =>
        set((state) => ({
          agentConfigs: state.agentConfigs.map((c) => ({
            ...c,
            isDefault: c.id === id,
          })),
          defaultAgentConfigId: id,
        })),
    }),
    {
      name: 'oagent-config',
    }
  )
)