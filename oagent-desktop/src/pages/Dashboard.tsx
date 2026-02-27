import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MessageSquare, Settings, Database, Zap, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const stats = [
    { label: 'Total Chats', value: '0', icon: MessageSquare },
    { label: 'Knowledge Bases', value: '0', icon: Database },
    { label: 'Agents Configured', value: '0', icon: Settings },
    { label: 'LLM Providers', value: '2', icon: Zap },
  ]

  const quickActions = [
    {
      title: 'Start a Chat',
      description: 'Begin a new conversation with your AI agent',
      icon: MessageSquare,
      link: '/chat',
      color: 'bg-blue-500',
    },
    {
      title: 'Configure LLM',
      description: 'Set up your language model providers',
      icon: Settings,
      link: '/config',
      color: 'bg-green-500',
    },
    {
      title: 'Add Knowledge',
      description: 'Upload documents to your knowledge base',
      icon: Database,
      link: '/knowledge',
      color: 'bg-purple-500',
    },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="container mx-auto p-6 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Welcome to OAgent</h1>
          <p className="text-muted-foreground mt-2">
            Your pluggable universal AI agent framework
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardContent className="flex items-center p-6">
                <div className="p-2 rounded-lg bg-primary/10 mr-4">
                  <stat.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {quickActions.map((action) => (
              <Link key={action.title} to={action.link}>
                <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                  <CardHeader>
                    <div className={`p-2 rounded-lg ${action.color} w-fit mb-2`}>
                      <action.icon className="h-5 w-5 text-white" />
                    </div>
                    <CardTitle className="text-lg flex items-center justify-between">
                      {action.title}
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{action.description}</CardDescription>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        {/* Getting Started */}
        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
            <CardDescription>
              Follow these steps to set up your AI agent
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h3 className="font-medium">Configure your LLM Provider</h3>
                <p className="text-sm text-muted-foreground">
                  Add your OpenAI, Anthropic, or local Ollama API keys in the Config section
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h3 className="font-medium">Set up your Agent</h3>
                <p className="text-sm text-muted-foreground">
                  Choose your agent type, configure tools and memory settings
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h3 className="font-medium">Start chatting!</h3>
                <p className="text-sm text-muted-foreground">
                  Begin a conversation with your configured AI agent
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}