/**
 * ToolIndicator Component
 *
 * Displays tool usage information during agent execution.
 * Shows tool calls, arguments, and results in an expandable format.
 */

import { useState } from 'react'
import { ChevronDown, ChevronRight, Wrench, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ToolCallInfo } from '@/stores/chatStore'

interface ToolIndicatorProps {
  toolCalls: ToolCallInfo[]
  isLoading?: boolean
}

/**
 * Format tool arguments for display
 */
function formatArgs(args: Record<string, unknown>): string {
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
}

/**
 * Single tool call display
 */
function ToolCallItem({ toolCall }: { toolCall: ToolCallInfo }) {
  const [isExpanded, setIsExpanded] = useState(true)

  const statusIcons = {
    pending: <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />,
    running: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
    completed: <CheckCircle2 className="h-4 w-4 text-green-500" />,
    error: <XCircle className="h-4 w-4 text-red-500" />,
  }

  const statusColors = {
    pending: 'text-yellow-500',
    running: 'text-blue-500',
    completed: 'text-green-500',
    error: 'text-red-500',
  }

  return (
    <div className="border border-border rounded-lg overflow-hidden my-2">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-muted/50 hover:bg-muted transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
        <Wrench className="h-4 w-4 text-muted-foreground" />
        <span className="font-mono text-sm font-medium">{toolCall.tool_name}</span>
        <div className="ml-auto">{statusIcons[toolCall.status]}</div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-3 py-2 border-t border-border">
          {/* Arguments */}
          {toolCall.tool_args && Object.keys(toolCall.tool_args).length > 0 && (
            <div className="mb-2">
              <p className="text-xs text-muted-foreground mb-1">Arguments:</p>
              <pre className="bg-muted p-2 rounded text-xs font-mono overflow-x-auto">
                {formatArgs(toolCall.tool_args)}
              </pre>
            </div>
          )}

          {/* Result */}
          {toolCall.tool_result && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Result:</p>
              <pre
                className={cn(
                  'p-2 rounded text-xs font-mono overflow-x-auto whitespace-pre-wrap',
                  toolCall.status === 'error'
                    ? 'bg-red-500/10 text-red-500'
                    : 'bg-muted'
                )}
              >
                {toolCall.tool_result}
              </pre>
            </div>
          )}

          {/* Status message for pending/running */}
          {(toolCall.status === 'pending' || toolCall.status === 'running') && (
            <p className={cn('text-xs', statusColors[toolCall.status])}>
              {toolCall.status === 'pending' && 'Waiting to execute...'}
              {toolCall.status === 'running' && 'Executing...'}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Main ToolIndicator component
 */
export function ToolIndicator({ toolCalls, isLoading }: ToolIndicatorProps) {
  if (toolCalls.length === 0 && !isLoading) {
    return null
  }

  return (
    <div className="max-w-[80%] mx-auto my-2">
      <div className="bg-muted/30 border border-border rounded-lg p-3">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <Wrench className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Tool Usage</span>
          {isLoading && (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground ml-auto" />
          )}
        </div>

        {/* Tool calls */}
        <div className="space-y-2">
          {toolCalls.map((toolCall, index) => (
            <ToolCallItem key={index} toolCall={toolCall} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default ToolIndicator
