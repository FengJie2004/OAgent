import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Settings, Plus, Trash2, Edit } from 'lucide-react'

interface LLMConfig {
  id: string
  name: string
  provider: string
  model: string
  isDefault: boolean
}

export default function Config() {
  const [configs, setConfigs] = useState<LLMConfig[]>([
    { id: '1', name: 'GPT-4', provider: 'OpenAI', model: 'gpt-4o', isDefault: true },
    { id: '2', name: 'Local Llama', provider: 'Ollama', model: 'llama3.2', isDefault: false },
  ])

  const [activeTab, setActiveTab] = useState<'llm' | 'agent' | 'vectorstore'>('llm')

  const tabs = [
    { id: 'llm', label: 'LLM Providers' },
    { id: 'agent', label: 'Agents' },
    { id: 'vectorstore', label: 'Vector Stores' },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Configuration</h1>
          <p className="text-muted-foreground mt-2">
            Manage your LLM providers, agents, and vector stores
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === 'llm' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">LLM Providers</h2>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Provider
              </Button>
            </div>

            <div className="grid gap-4">
              {configs.map((config) => (
                <Card key={config.id}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-lg">{config.name}</CardTitle>
                      {config.isDefault && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                          Default
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="icon">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-4 text-sm text-muted-foreground">
                      <span>Provider: {config.provider}</span>
                      <span>Model: {config.model}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Add New Config Form */}
            <Card>
              <CardHeader>
                <CardTitle>Add New LLM Provider</CardTitle>
                <CardDescription>
                  Configure a new language model provider
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Name</label>
                    <Input placeholder="My GPT-4 Config" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Provider</label>
                    <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                      <option>OpenAI</option>
                      <option>Anthropic</option>
                      <option>Ollama</option>
                      <option>Zhipu</option>
                      <option>DeepSeek</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Model</label>
                    <Input placeholder="gpt-4o" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">API Key</label>
                    <Input type="password" placeholder="sk-..." />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline">Cancel</Button>
                  <Button>Save</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'agent' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Agent Configurations</h2>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Agent
              </Button>
            </div>

            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Settings className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium">No agents configured</h3>
                  <p className="text-muted-foreground text-sm mt-1">
                    Create an agent configuration to get started
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'vectorstore' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Vector Stores</h2>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Vector Store
              </Button>
            </div>

            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Settings className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium">No vector stores configured</h3>
                  <p className="text-muted-foreground text-sm mt-1">
                    Add a vector store for RAG capabilities
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}