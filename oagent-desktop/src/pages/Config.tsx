/**
 * Configuration Page for OAgent Desktop
 *
 * Manages LLM Providers, Agent Configurations, and Vector Stores
 * with full CRUD operations, validation, and toast notifications.
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { ToastAction } from '@/components/ui/toast'
import {
  Plus,
  Trash2,
  Edit,
  Check,
  X,
  Loader2,
  Zap,
  Database,
  Cpu,
  Key,
  Link,
  Sliders,
  Settings,
} from 'lucide-react'
import { useConfigStore, LLMConfig, AgentConfig, VectorStoreState } from '@/stores/configStore'

// ============================================================================
// Constants
// ============================================================================

const LLM_PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'ollama', label: 'Ollama' },
  { value: 'dashscope', label: 'DashScope (阿里百炼)' },
  { value: 'azure-openai', label: 'Azure OpenAI' },
] as const

const AGENT_TYPES = [
  { value: 'langchain', label: 'LangChain' },
  { value: 'langgraph', label: 'LangGraph' },
  { value: 'react', label: 'ReAct' },
  { value: 'plan-execute', label: 'Plan & Execute' },
] as const

const VECTOR_STORE_TYPES = [
  { value: 'chroma', label: 'ChromaDB' },
  { value: 'faiss', label: 'FAISS' },
  { value: 'milvus', label: 'Milvus' },
  { value: 'pinecone', label: 'Pinecone' },
] as const

const MEMORY_TYPES = [
  { value: 'buffer', label: 'Buffer' },
  { value: 'window', label: 'Window' },
  { value: 'summary', label: 'Summary' },
] as const

// ============================================================================
// Form Types
// ============================================================================

interface LLMConfigForm extends Omit<LLMConfig, 'id' | 'isDefault'> {
  id?: string
}

interface AgentConfigForm extends Omit<AgentConfig, 'id' | 'isDefault'> {
  id?: string
}

interface VectorStoreForm extends Omit<VectorStoreState, 'id' | 'isDefault' | 'documentCount'> {
  id?: string
}

// ============================================================================
// Main Component
// ============================================================================

export default function Config() {
  const { toast } = useToast()

  // Store state and actions
  const {
    llmConfigs,
    agentConfigs,
    vectorStores,
    defaultLLMConfigId,
    defaultAgentConfigId,
    defaultVectorStoreId,
    isLoading,
    isSaving,
    error,
    fetchLLMConfigs,
    createLLMConfig,
    updateLLMConfig,
    deleteLLMConfig,
    setDefaultLLMConfig,
    fetchAgentConfigs,
    createAgentConfig,
    updateAgentConfig,
    deleteAgentConfig,
    setDefaultAgentConfig,
    fetchVectorStores,
    createVectorStore,
    updateVectorStore,
    deleteVectorStore,
    setDefaultVectorStore,
    clearError,
  } = useConfigStore()

  // UI state
  const [activeTab, setActiveTab] = useState<'llm' | 'agent' | 'vectorstore'>('llm')

  // Dialog states
  const [llmDialogOpen, setLlmDialogOpen] = useState(false)
  const [agentDialogOpen, setAgentDialogOpen] = useState(false)
  const [vectorDialogOpen, setVectorDialogOpen] = useState(false)

  // Edit states
  const [editingLLMConfig, setEditingLLMConfig] = useState<LLMConfigForm | null>(null)
  const [editingAgentConfig, setEditingAgentConfig] = useState<AgentConfigForm | null>(null)
  const [editingVectorStore, setEditingVectorStore] = useState<VectorStoreForm | null>(null)

  // Load configurations on mount
  useEffect(() => {
    loadAllConfigs()
  }, [])

  const loadAllConfigs = async () => {
    try {
      await Promise.all([
        fetchLLMConfigs().catch(() => { /* Silently fail - configs may not exist yet */ }),
        fetchAgentConfigs().catch(() => { /* Silently fail */ }),
        fetchVectorStores().catch(() => { /* Silently fail */ }),
      ])
    } catch (error) {
      // Errors are handled in the store
    }
  }

  // ============================================================================
  // LLM Provider Handlers
  // ============================================================================

  const handleSaveLLMConfig = async (config: LLMConfigForm) => {
    try {
      if (editingLLMConfig?.id) {
        await updateLLMConfig(editingLLMConfig.id, config)
        toast({
          title: 'LLM Provider Updated',
          description: `${config.name} has been updated successfully.`,
        })
      } else {
        await createLLMConfig(config)
        toast({
          title: 'LLM Provider Added',
          description: `${config.name} has been added successfully.`,
        })
      }
      setLlmDialogOpen(false)
      setEditingLLMConfig(null)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Save',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        action: <ToastAction altText="Retry">Retry</ToastAction>,
      })
    }
  }

  const handleDeleteLLMConfig = async (id: string, name: string) => {
    try {
      await deleteLLMConfig(id)
      toast({
        title: 'LLM Provider Deleted',
        description: `${name} has been removed.`,
      })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Delete',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
      })
    }
  }

  const handleSetDefaultLLM = async (id: string) => {
    try {
      await setDefaultLLMConfig(id)
      toast({
        title: 'Default Updated',
        description: 'Default LLM provider has been updated.',
      })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Set Default',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
      })
    }
  }

  const openEditLLMDialog = (config: LLMConfig) => {
    setEditingLLMConfig({
      id: config.id,
      name: config.name,
      provider: config.provider,
      modelName: config.modelName,
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
      temperature: config.temperature,
      maxTokens: config.maxTokens,
    })
    setLlmDialogOpen(true)
  }

  const openAddLLMDialog = () => {
    setEditingLLMConfig(null)
    setLlmDialogOpen(true)
  }

  // ============================================================================
  // Agent Configuration Handlers
  // ============================================================================

  const handleSaveAgentConfig = async (config: AgentConfigForm) => {
    try {
      if (editingAgentConfig?.id) {
        await updateAgentConfig(editingAgentConfig.id, config)
        toast({
          title: 'Agent Updated',
          description: `${config.name} has been updated successfully.`,
        })
      } else {
        await createAgentConfig(config)
        toast({
          title: 'Agent Added',
          description: `${config.name} has been added successfully.`,
        })
      }
      setAgentDialogOpen(false)
      setEditingAgentConfig(null)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Save',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        action: <ToastAction altText="Retry">Retry</ToastAction>,
      })
    }
  }

  const handleDeleteAgentConfig = async (id: string, name: string) => {
    try {
      await deleteAgentConfig(id)
      toast({
        title: 'Agent Deleted',
        description: `${name} has been removed.`,
      })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Delete',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
      })
    }
  }

  const handleSetDefaultAgent = async (id: string) => {
    try {
      await setDefaultAgentConfig(id)
      toast({
        title: 'Default Updated',
        description: 'Default agent configuration has been updated.',
      })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Set Default',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
      })
    }
  }

  const openEditAgentDialog = (config: AgentConfig) => {
    setEditingAgentConfig({
      id: config.id,
      name: config.name,
      agentType: config.agentType,
      llmProvider: config.llmProvider,
      llmModel: config.llmModel,
      llmConfigId: config.llmConfigId,
      systemPrompt: config.systemPrompt,
      tools: config.tools,
      maxIterations: config.maxIterations,
      memoryEnabled: config.memoryEnabled,
      memoryType: config.memoryType,
      memoryWindow: config.memoryWindow,
      temperature: config.temperature,
      maxTokens: config.maxTokens,
    })
    setAgentDialogOpen(true)
  }

  const openAddAgentDialog = () => {
    setEditingAgentConfig(null)
    setAgentDialogOpen(true)
  }

  // ============================================================================
  // Vector Store Handlers
  // ============================================================================

  const handleSaveVectorStore = async (config: VectorStoreForm) => {
    try {
      if (editingVectorStore?.id) {
        await updateVectorStore(editingVectorStore.id, config)
        toast({
          title: 'Vector Store Updated',
          description: `${config.name} has been updated successfully.`,
        })
      } else {
        await createVectorStore(config)
        toast({
          title: 'Vector Store Added',
          description: `${config.name} has been added successfully.`,
        })
      }
      setVectorDialogOpen(false)
      setEditingVectorStore(null)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Save',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        action: <ToastAction altText="Retry">Retry</ToastAction>,
      })
    }
  }

  const handleDeleteVectorStore = async (id: string, name: string) => {
    try {
      await deleteVectorStore(id)
      toast({
        title: 'Vector Store Deleted',
        description: `${name} has been removed.`,
      })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Delete',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
      })
    }
  }

  const handleSetDefaultVectorStore = async (id: string) => {
    try {
      await setDefaultVectorStore(id)
      toast({
        title: 'Default Updated',
        description: 'Default vector store has been updated.',
      })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to Set Default',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
      })
    }
  }

  const openEditVectorDialog = (store: VectorStoreState) => {
    setEditingVectorStore({
      id: store.id,
      name: store.name,
      provider: store.provider,
      collectionName: store.collectionName,
      connectionString: store.connectionString,
      apiKey: store.apiKey,
      embeddingModel: store.embeddingModel,
      embeddingProvider: store.embeddingProvider,
      dimension: store.dimension,
    })
    setVectorDialogOpen(true)
  }

  const openAddVectorDialog = () => {
    setEditingVectorStore(null)
    setVectorDialogOpen(true)
  }

  // ============================================================================
  // Render
  // ============================================================================

  const tabs = [
    { id: 'llm' as const, label: 'LLM Providers', icon: Zap },
    { id: 'agent' as const, label: 'Agents', icon: Cpu },
    { id: 'vectorstore' as const, label: 'Vector Stores', icon: Database },
  ]

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <div className="container mx-auto p-6 space-y-6 max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Configuration</h1>
            <p className="text-muted-foreground mt-1">
              Manage your LLM providers, agents, and vector stores
            </p>
          </div>
          {isSaving && (
            <div className="flex items-center text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-muted/50 p-1 rounded-lg w-fit">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  activeTab === tab.id
                    ? 'bg-background text-primary shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Error Banner */}
        {error && (
          <Card className="border-destructive/50 bg-destructive/10">
            <CardContent className="flex items-center justify-between py-4">
              <div className="flex items-center gap-2 text-destructive">
                <X className="h-4 w-4" />
                <span className="text-sm font-medium">{error}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={clearError}>
                Dismiss
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Content */}
        {activeTab === 'llm' && (
          <LLMProvidersTab
            configs={llmConfigs}
            defaultConfigId={defaultLLMConfigId}
            isLoading={isLoading}
            onAdd={openAddLLMDialog}
            onEdit={openEditLLMDialog}
            onDelete={handleDeleteLLMConfig}
            onSetDefault={handleSetDefaultLLM}
          />
        )}

        {activeTab === 'agent' && (
          <AgentsTab
            configs={agentConfigs}
            defaultConfigId={defaultAgentConfigId}
            isLoading={isLoading}
            onAdd={openAddAgentDialog}
            onEdit={openEditAgentDialog}
            onDelete={handleDeleteAgentConfig}
            onSetDefault={handleSetDefaultAgent}
          />
        )}

        {activeTab === 'vectorstore' && (
          <VectorStoresTab
            stores={vectorStores}
            defaultStoreId={defaultVectorStoreId}
            isLoading={isLoading}
            onAdd={openAddVectorDialog}
            onEdit={openEditVectorDialog}
            onDelete={handleDeleteVectorStore}
            onSetDefault={handleSetDefaultVectorStore}
          />
        )}

        {/* LLM Config Dialog */}
        <LLMConfigDialog
          open={llmDialogOpen}
          onOpenChange={setLlmDialogOpen}
          onSave={handleSaveLLMConfig}
          editingConfig={editingLLMConfig}
          isSaving={isSaving}
        />

        {/* Agent Config Dialog */}
        <AgentConfigDialog
          open={agentDialogOpen}
          onOpenChange={setAgentDialogOpen}
          onSave={handleSaveAgentConfig}
          editingConfig={editingAgentConfig}
          isSaving={isSaving}
        />

        {/* Vector Store Dialog */}
        <VectorStoreDialog
          open={vectorDialogOpen}
          onOpenChange={setVectorDialogOpen}
          onSave={handleSaveVectorStore}
          editingConfig={editingVectorStore}
          isSaving={isSaving}
        />
      </div>
    </div>
  )
}

// ============================================================================
// LLM Providers Tab
// ============================================================================

interface LLMProvidersTabProps {
  configs: LLMConfig[]
  defaultConfigId: string | null
  isLoading: boolean
  onAdd: () => void
  onEdit: (config: LLMConfig) => void
  onDelete: (id: string, name: string) => void
  onSetDefault: (id: string) => void
}

function LLMProvidersTab({
  configs,
  defaultConfigId: _defaultConfigId,
  isLoading,
  onAdd,
  onEdit,
  onDelete,
  onSetDefault,
}: LLMProvidersTabProps) {
  const providerLabels: Record<string, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    ollama: 'Ollama',
    dashscope: 'DashScope',
    'azure-openai': 'Azure OpenAI',
  }

  if (isLoading && configs.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading configurations...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">LLM Providers</h2>
        <Button onClick={onAdd}>
          <Plus className="h-4 w-4 mr-2" />
          Add Provider
        </Button>
      </div>

      {configs.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <Zap className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">No LLM providers configured</h3>
              <p className="text-muted-foreground text-sm mt-1">
                Add an LLM provider to start using OAgent
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {configs.map((config) => (
            <Card key={config.id} className={config.isDefault ? 'border-primary/50' : ''}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center h-10 w-10 rounded-full bg-primary/10">
                    <Zap className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-lg">{config.name}</CardTitle>
                      {config.isDefault && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                          Default
                        </span>
                      )}
                    </div>
                    <CardDescription className="text-sm">
                      {providerLabels[config.provider] || config.provider} &middot; {config.modelName}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex gap-1">
                  {!config.isDefault && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSetDefault(config.id)}
                      title="Set as default"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(config)}
                    title="Edit"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(config.id, config.name)}
                    className="text-destructive hover:text-destructive"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4 text-sm text-muted-foreground">
                  {config.baseUrl && (
                    <div className="flex items-center gap-1">
                      <Link className="h-3 w-3" />
                      <span className="truncate max-w-[200px]">{config.baseUrl}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Sliders className="h-3 w-3" />
                    <span>Temp: {config.temperature}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Key className="h-3 w-3" />
                    <span>{config.apiKey ? 'API key configured' : 'No API key'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Agents Tab
// ============================================================================

interface AgentsTabProps {
  configs: AgentConfig[]
  defaultConfigId: string | null
  isLoading: boolean
  onAdd: () => void
  onEdit: (config: AgentConfig) => void
  onDelete: (id: string, name: string) => void
  onSetDefault: (id: string) => void
}

function AgentsTab({
  configs,
  defaultConfigId: _defaultConfigId,
  isLoading,
  onAdd,
  onEdit,
  onDelete,
  onSetDefault,
}: AgentsTabProps) {
  const agentTypeLabels: Record<string, string> = {
    langchain: 'LangChain',
    langgraph: 'LangGraph',
    react: 'ReAct',
    'plan-execute': 'Plan & Execute',
  }

  if (isLoading && configs.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading configurations...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Agent Configurations</h2>
        <Button onClick={onAdd}>
          <Plus className="h-4 w-4 mr-2" />
          New Agent
        </Button>
      </div>

      {configs.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <Cpu className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">No agents configured</h3>
              <p className="text-muted-foreground text-sm mt-1">
                Create an agent configuration to get started
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {configs.map((config) => (
            <Card key={config.id} className={config.isDefault ? 'border-primary/50' : ''}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center h-10 w-10 rounded-full bg-primary/10">
                    <Cpu className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-lg">{config.name}</CardTitle>
                      {config.isDefault && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                          Default
                        </span>
                      )}
                    </div>
                    <CardDescription className="text-sm">
                      {agentTypeLabels[config.agentType] || config.agentType} &middot; {config.llmModel}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex gap-1">
                  {!config.isDefault && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSetDefault(config.id)}
                      title="Set as default"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(config)}
                    title="Edit"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(config.id, config.name)}
                    className="text-destructive hover:text-destructive"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    <span>Temp: {config.temperature}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Sliders className="h-3 w-3" />
                    <span>Max tokens: {config.maxTokens}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Settings className="h-3 w-3" />
                    <span>Memory: {config.memoryEnabled ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  {config.tools.length > 0 && (
                    <div className="flex items-center gap-1">
                      <Cpu className="h-3 w-3" />
                      <span>{config.tools.length} tools</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Vector Stores Tab
// ============================================================================

interface VectorStoresTabProps {
  stores: VectorStoreState[]
  defaultStoreId: string | null
  isLoading: boolean
  onAdd: () => void
  onEdit: (store: VectorStoreState) => void
  onDelete: (id: string, name: string) => void
  onSetDefault: (id: string) => void
}

function VectorStoresTab({
  stores,
  defaultStoreId: _defaultStoreId,
  isLoading,
  onAdd,
  onEdit,
  onDelete,
  onSetDefault,
}: VectorStoresTabProps) {
  const providerLabels: Record<string, string> = {
    chroma: 'ChromaDB',
    faiss: 'FAISS',
    milvus: 'Milvus',
    pinecone: 'Pinecone',
  }

  if (isLoading && stores.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading configurations...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Vector Stores</h2>
        <Button onClick={onAdd}>
          <Plus className="h-4 w-4 mr-2" />
          Add Vector Store
        </Button>
      </div>

      {stores.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">No vector stores configured</h3>
              <p className="text-muted-foreground text-sm mt-1">
                Add a vector store for RAG capabilities
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {stores.map((store) => (
            <Card key={store.id} className={store.isDefault ? 'border-primary/50' : ''}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center h-10 w-10 rounded-full bg-primary/10">
                    <Database className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-lg">{store.name}</CardTitle>
                      {store.isDefault && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                          Default
                        </span>
                      )}
                    </div>
                    <CardDescription className="text-sm">
                      {providerLabels[store.provider] || store.provider} &middot; {store.collectionName}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex gap-1">
                  {!store.isDefault && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSetDefault(store.id)}
                      title="Set as default"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(store)}
                    title="Edit"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(store.id, store.name)}
                    className="text-destructive hover:text-destructive"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  {store.connectionString && (
                    <div className="flex items-center gap-1">
                      <Link className="h-3 w-3" />
                      <span className="truncate max-w-[200px]">{store.connectionString}</span>
                    </div>
                  )}
                  {store.dimension && (
                    <div className="flex items-center gap-1">
                      <Sliders className="h-3 w-3" />
                      <span>Dimension: {store.dimension}</span>
                    </div>
                  )}
                  {store.documentCount !== undefined && (
                    <div className="flex items-center gap-1">
                      <Database className="h-3 w-3" />
                      <span>{store.documentCount} documents</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// LLM Config Dialog
// ============================================================================

interface LLMConfigDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (config: LLMConfigForm) => void
  editingConfig: LLMConfigForm | null
  isSaving: boolean
}

function LLMConfigDialog({ open, onOpenChange, onSave, editingConfig, isSaving }: LLMConfigDialogProps) {
  const [form, setForm] = useState<LLMConfigForm>({
    name: '',
    provider: 'openai',
    modelName: '',
    apiKey: '',
    baseUrl: '',
    temperature: 0.7,
    maxTokens: 2048,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (editingConfig) {
      setForm(editingConfig)
    } else {
      setForm({
        name: '',
        provider: 'openai',
        modelName: '',
        apiKey: '',
        baseUrl: '',
        temperature: 0.7,
        maxTokens: 2048,
      })
    }
    setErrors({})
  }, [editingConfig, open])

  const validate = () => {
    const newErrors: Record<string, string> = {}

    if (!form.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!form.modelName.trim()) {
      newErrors.modelName = 'Model name is required'
    }

    if (form.provider === 'ollama') {
      if (!form.baseUrl?.trim()) {
        newErrors.baseUrl = 'Base URL is required for Ollama'
      }
    } else if (!form.apiKey?.trim() && form.provider !== 'ollama') {
      newErrors.apiKey = 'API key is required'
    }

    if (form.temperature < 0 || form.temperature > 2) {
      newErrors.temperature = 'Temperature must be between 0 and 2'
    }

    if (form.maxTokens < 1) {
      newErrors.maxTokens = 'Max tokens must be at least 1'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) {
      onSave(form)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {editingConfig ? 'Edit LLM Provider' : 'Add LLM Provider'}
            </DialogTitle>
            <DialogDescription>
              Configure a new language model provider
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="My GPT-4 Config"
                />
                {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="provider">Provider</Label>
                <select
                  id="provider"
                  value={form.provider}
                  onChange={(e) => setForm({ ...form, provider: e.target.value as LLMConfigForm['provider'] })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {LLM_PROVIDERS.map((p) => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
                {errors.provider && <p className="text-xs text-destructive">{errors.provider}</p>}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="modelName">Model Name</Label>
              <Input
                id="modelName"
                value={form.modelName}
                onChange={(e) => setForm({ ...form, modelName: e.target.value })}
                placeholder="gpt-4o"
              />
              {errors.modelName && <p className="text-xs text-destructive">{errors.modelName}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                value={form.apiKey || ''}
                onChange={(e) => setForm({ ...form, apiKey: e.target.value })}
                placeholder="sk-..."
                disabled={form.provider === 'ollama'}
              />
              {errors.apiKey && <p className="text-xs text-destructive">{errors.apiKey}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="baseUrl">Base URL (optional)</Label>
              <Input
                id="baseUrl"
                value={form.baseUrl || ''}
                onChange={(e) => setForm({ ...form, baseUrl: e.target.value })}
                placeholder="https://api.example.com/v1"
              />
              {errors.baseUrl && <p className="text-xs text-destructive">{errors.baseUrl}</p>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={form.temperature}
                  onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) || 0 })}
                />
                {errors.temperature && <p className="text-xs text-destructive">{errors.temperature}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxTokens">Max Tokens</Label>
                <Input
                  id="maxTokens"
                  type="number"
                  min="1"
                  value={form.maxTokens}
                  onChange={(e) => setForm({ ...form, maxTokens: parseInt(e.target.value) || 1 })}
                />
                {errors.maxTokens && <p className="text-xs text-destructive">{errors.maxTokens}</p>}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingConfig ? 'Save Changes' : 'Add Provider'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Agent Config Dialog
// ============================================================================

interface AgentConfigDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (config: AgentConfigForm) => void
  editingConfig: AgentConfigForm | null
  isSaving: boolean
}

function AgentConfigDialog({ open, onOpenChange, onSave, editingConfig, isSaving }: AgentConfigDialogProps) {
  const { llmConfigs } = useConfigStore()

  const [form, setForm] = useState<AgentConfigForm>({
    name: '',
    agentType: 'langchain',
    llmProvider: 'openai',
    llmModel: 'gpt-4o-mini',
    llmConfigId: '',
    systemPrompt: '',
    tools: [],
    maxIterations: 10,
    memoryEnabled: true,
    memoryType: 'buffer',
    memoryWindow: 10,
    temperature: 0.7,
    maxTokens: 2048,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (editingConfig) {
      setForm(editingConfig)
    } else {
      setForm({
        name: '',
        agentType: 'langchain',
        llmProvider: 'openai',
        llmModel: 'gpt-4o-mini',
        llmConfigId: llmConfigs.find((c) => c.isDefault)?.id || '',
        systemPrompt: '',
        tools: [],
        maxIterations: 10,
        memoryEnabled: true,
        memoryType: 'buffer',
        memoryWindow: 10,
        temperature: 0.7,
        maxTokens: 2048,
      })
    }
    setErrors({})
  }, [editingConfig, open, llmConfigs])

  const validate = () => {
    const newErrors: Record<string, string> = {}

    if (!form.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!form.llmModel.trim()) {
      newErrors.llmModel = 'LLM model is required'
    }

    if (form.maxIterations < 1) {
      newErrors.maxIterations = 'Max iterations must be at least 1'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) {
      onSave(form)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {editingConfig ? 'Edit Agent' : 'Create New Agent'}
            </DialogTitle>
            <DialogDescription>
              Configure a new agent with LLM and tools
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="agentName">Name</Label>
                <Input
                  id="agentName"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="My Assistant"
                />
                {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="agentType">Agent Type</Label>
                <select
                  id="agentType"
                  value={form.agentType}
                  onChange={(e) => setForm({ ...form, agentType: e.target.value as AgentConfigForm['agentType'] })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {AGENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="llmConfig">LLM Configuration</Label>
              <select
                id="llmConfig"
                value={form.llmConfigId || ''}
                onChange={(e) => {
                  const config = llmConfigs.find((c) => c.id === e.target.value)
                  setForm({
                    ...form,
                    llmConfigId: e.target.value,
                    llmProvider: config?.provider || form.llmProvider,
                    llmModel: config?.modelName || form.llmModel,
                  })
                }}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Select LLM config...</option>
                {llmConfigs.map((config) => (
                  <option key={config.id} value={config.id}>
                    {config.name} ({config.modelName})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="llmProvider">LLM Provider</Label>
                <Input
                  id="llmProvider"
                  value={form.llmProvider}
                  onChange={(e) => setForm({ ...form, llmProvider: e.target.value })}
                  placeholder="openai"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="llmModel">LLM Model</Label>
                <Input
                  id="llmModel"
                  value={form.llmModel}
                  onChange={(e) => setForm({ ...form, llmModel: e.target.value })}
                  placeholder="gpt-4o"
                />
                {errors.llmModel && <p className="text-xs text-destructive">{errors.llmModel}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="systemPrompt">System Prompt (optional)</Label>
              <textarea
                id="systemPrompt"
                value={form.systemPrompt || ''}
                onChange={(e) => setForm({ ...form, systemPrompt: e.target.value })}
                placeholder="You are a helpful assistant..."
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>

            <div className="space-y-2">
              <Label>Memory Settings</Label>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.memoryEnabled}
                    onChange={(e) => setForm({ ...form, memoryEnabled: e.target.checked })}
                    className="h-4 w-4"
                  />
                  Enable Memory
                </label>
                {form.memoryEnabled && (
                  <>
                    <select
                      value={form.memoryType}
                      onChange={(e) => setForm({ ...form, memoryType: e.target.value })}
                      className="flex h-8 rounded-md border border-input bg-background px-2 py-1 text-sm"
                    >
                      {MEMORY_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                    <Input
                      type="number"
                      min="1"
                      value={form.memoryWindow}
                      onChange={(e) => setForm({ ...form, memoryWindow: parseInt(e.target.value) || 1 })}
                      className="w-20"
                      placeholder="Window"
                      title="Memory window size"
                    />
                  </>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="agentTemperature">Temperature</Label>
                <Input
                  id="agentTemperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={form.temperature}
                  onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="agentMaxTokens">Max Tokens</Label>
                <Input
                  id="agentMaxTokens"
                  type="number"
                  min="1"
                  value={form.maxTokens}
                  onChange={(e) => setForm({ ...form, maxTokens: parseInt(e.target.value) || 1 })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxIterations">Max Iterations</Label>
              <Input
                id="maxIterations"
                type="number"
                min="1"
                value={form.maxIterations}
                onChange={(e) => setForm({ ...form, maxIterations: parseInt(e.target.value) || 1 })}
              />
              {errors.maxIterations && <p className="text-xs text-destructive">{errors.maxIterations}</p>}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingConfig ? 'Save Changes' : 'Create Agent'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Vector Store Dialog
// ============================================================================

interface VectorStoreDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (config: VectorStoreForm) => void
  editingConfig: VectorStoreForm | null
  isSaving: boolean
}

function VectorStoreDialog({ open, onOpenChange, onSave, editingConfig, isSaving }: VectorStoreDialogProps) {
  const [form, setForm] = useState<VectorStoreForm>({
    name: '',
    provider: 'chroma',
    collectionName: '',
    connectionString: '',
    apiKey: '',
    embeddingModel: '',
    embeddingProvider: '',
    dimension: 1536,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (editingConfig) {
      setForm(editingConfig)
    } else {
      setForm({
        name: '',
        provider: 'chroma',
        collectionName: '',
        connectionString: '',
        apiKey: '',
        embeddingModel: '',
        embeddingProvider: '',
        dimension: 1536,
      })
    }
    setErrors({})
  }, [editingConfig, open])

  const validate = () => {
    const newErrors: Record<string, string> = {}

    if (!form.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!form.collectionName.trim()) {
      newErrors.collectionName = 'Collection name is required'
    }

    if (form.provider === 'milvus' && !form.connectionString?.trim()) {
      newErrors.connectionString = 'Connection string is required for Milvus'
    }

    if (form.provider === 'pinecone' && !form.apiKey?.trim()) {
      newErrors.apiKey = 'API key is required for Pinecone'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) {
      onSave(form)
    }
  }

  const renderProviderSpecificFields = () => {
    switch (form.provider) {
      case 'milvus':
        return (
          <div className="space-y-2">
            <Label htmlFor="connectionString">Connection String</Label>
            <Input
              id="connectionString"
              value={form.connectionString || ''}
              onChange={(e) => setForm({ ...form, connectionString: e.target.value })}
              placeholder="http://localhost:19530"
            />
            {errors.connectionString && <p className="text-xs text-destructive">{errors.connectionString}</p>}
          </div>
        )
      case 'pinecone':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                value={form.apiKey || ''}
                onChange={(e) => setForm({ ...form, apiKey: e.target.value })}
                placeholder="pc-..."
              />
              {errors.apiKey && <p className="text-xs text-destructive">{errors.apiKey}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="connectionString">Environment</Label>
              <Input
                id="connectionString"
                value={form.connectionString || ''}
                onChange={(e) => setForm({ ...form, connectionString: e.target.value })}
                placeholder="gcp-starter"
              />
            </div>
          </>
        )
      case 'chroma':
        return (
          <div className="space-y-2">
            <Label htmlFor="connectionString">Path (optional)</Label>
            <Input
              id="connectionString"
              value={form.connectionString || ''}
              onChange={(e) => setForm({ ...form, connectionString: e.target.value })}
              placeholder="./chroma_db"
            />
          </div>
        )
      case 'faiss':
        return (
          <div className="space-y-2">
            <Label htmlFor="connectionString">Index Path (optional)</Label>
            <Input
              id="connectionString"
              value={form.connectionString || ''}
              onChange={(e) => setForm({ ...form, connectionString: e.target.value })}
              placeholder="./faiss_index"
            />
          </div>
        )
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {editingConfig ? 'Edit Vector Store' : 'Add Vector Store'}
            </DialogTitle>
            <DialogDescription>
              Configure a new vector store for RAG capabilities
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="vsName">Name</Label>
                <Input
                  id="vsName"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="My Vector Store"
                />
                {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="vsProvider">Provider</Label>
                <select
                  id="vsProvider"
                  value={form.provider}
                  onChange={(e) => setForm({ ...form, provider: e.target.value as VectorStoreForm['provider'] })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {VECTOR_STORE_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="collectionName">Collection Name</Label>
              <Input
                id="collectionName"
                value={form.collectionName}
                onChange={(e) => setForm({ ...form, collectionName: e.target.value })}
                placeholder="my_collection"
              />
              {errors.collectionName && <p className="text-xs text-destructive">{errors.collectionName}</p>}
            </div>
            {renderProviderSpecificFields()}
            <div className="space-y-2">
              <Label htmlFor="dimension">Embedding Dimension</Label>
              <Input
                id="dimension"
                type="number"
                min="1"
                value={form.dimension}
                onChange={(e) => setForm({ ...form, dimension: parseInt(e.target.value) || 1 })}
                placeholder="1536"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="embeddingProvider">Embedding Provider (optional)</Label>
                <Input
                  id="embeddingProvider"
                  value={form.embeddingProvider || ''}
                  onChange={(e) => setForm({ ...form, embeddingProvider: e.target.value })}
                  placeholder="openai"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="embeddingModel">Embedding Model (optional)</Label>
                <Input
                  id="embeddingModel"
                  value={form.embeddingModel || ''}
                  onChange={(e) => setForm({ ...form, embeddingModel: e.target.value })}
                  placeholder="text-embedding-3-small"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingConfig ? 'Save Changes' : 'Add Vector Store'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
