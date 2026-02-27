/**
 * Chat Page
 *
 * Main chat interface with:
 * - Real backend API connection
 * - Streaming responses
 * - Tool usage indicators
 * - Conversation history
 * - Multiple session support
 * - Markdown rendering with syntax highlighting
 */

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, Loader2, Trash2, RefreshCw, Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { MarkdownMessage } from '@/components/chat/MarkdownMessage'
import { ToolIndicator } from '@/components/chat/ToolIndicator'
import { SessionSidebar } from '@/components/chat/SessionSidebar'
import { useChatStore, ChatMessage } from '@/stores/chatStore'
import { api, ApiClientError } from '@/lib/api'
import type { StreamEvent } from '@/lib/types'

/**
 * Generate unique ID
 */
const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

export default function Chat() {
  const {
    // Sessions
    sessions,
    currentSessionId,
    isLoadingSessions,
    loadSessions,
    createSession,
    deleteSession,
    switchSession,

    // Messages
    messages,
    addMessage,
    updateMessage,
    clearMessages,

    // Streaming
    streamingState,
    isStreaming,
    startStreaming,
    stopStreaming,
    updateStreamingContent,
    addToolCall,

    // UI
    sidebarOpen,
    setSidebarOpen,
    error,
    setError,
    clearError,
  } = useChatStore()

  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, streamingState.accumulatedContent])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K to focus input
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }

      // Ctrl/Cmd + N for new chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault()
        handleNewChat()
      }

      // Escape to blur input
      if (e.key === 'Escape') {
        inputRef.current?.blur()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  /**
   * Handle sending a message
   */
  const handleSend = useCallback(async () => {
    const messageText = input.trim()
    if (!messageText || isSending || isStreaming) return

    // Ensure we have a session
    let sessionId = currentSessionId

    if (!sessionId) {
      try {
        const newSession = await createSession('New Chat')
        sessionId = newSession.id
      } catch (error) {
        console.error('Failed to create session:', error)
        setError('Failed to create session')
        return
      }
    }

    // Create user message
    const userMessage: Omit<ChatMessage, 'id' | 'created_at'> = {
      session_id: sessionId,
      role: 'user',
      content: messageText,
    }

    addMessage(userMessage)
    setInput('')
    setIsSending(true)
    clearError()

    // Create placeholder for assistant response
    const assistantMessageId = generateId()
    startStreaming(sessionId, assistantMessageId)

    try {
      // Send message to backend with streaming
      const stream = api.agent.runStream({
        input: messageText,
        thread_id: sessionId,
        stream: true,
      }, {
        onToken: (token) => {
          updateStreamingContent(token)
        },
        onToolCall: (toolCall) => {
          addToolCall({
            tool_name: toolCall.function.name,
            tool_args: JSON.parse(toolCall.function.arguments),
            status: 'running',
          })
        },
      })

      // Process stream
      for await (const event of stream) {
        const streamEvent = event as StreamEvent

        switch (streamEvent.type) {
          case 'token':
            updateStreamingContent(streamEvent.data as string)
            break

          case 'tool_call':
            // Tool call already handled via onToolCall callback
            break

          case 'thought':
            // Could show thinking process if desired
            break

          case 'error':
            throw new Error(streamEvent.data as string)

          case 'done':
            break
        }
      }

      // Mark message as complete
      updateMessage(assistantMessageId, { isStreaming: false })
      stopStreaming()

      // Update session title if this is the first message
      const sessionMessages = messages.filter(m => m.session_id === sessionId)
      if (sessionMessages.length === 1) {
        // Could update session title with first message preview
        // TODO: Implement when backend supports title updates
      }

    } catch (error) {
      console.error('Streaming error:', error)
      updateMessage(assistantMessageId, {
        isError: true,
        isStreaming: false,
      })
      stopStreaming()

      if (error instanceof ApiClientError) {
        setError(error.message)
      } else {
        setError(error instanceof Error ? error.message : 'Failed to send message')
      }
    } finally {
      setIsSending(false)
    }
  }, [
    input,
    isSending,
    isStreaming,
    currentSessionId,
    createSession,
    addMessage,
    updateMessage,
    startStreaming,
    updateStreamingContent,
    addToolCall,
    stopStreaming,
    messages,
    setError,
    clearError,
  ])

  /**
   * Handle new chat
   */
  const handleNewChat = useCallback(async () => {
    try {
      await createSession('New Chat')
      clearMessages()
      stopStreaming()
      setInput('')
      inputRef.current?.focus()
    } catch (error) {
      console.error('Failed to create new chat:', error)
      setError('Failed to create new chat')
    }
  }, [createSession, clearMessages, stopStreaming, setError])

  /**
   * Handle clear conversation
   */
  const handleClearConversation = useCallback(() => {
    if (currentSessionId) {
      clearMessages()
      stopStreaming()
    }
  }, [currentSessionId, clearMessages, stopStreaming])

  /**
   * Handle retry last message
   */
  const handleRetry = useCallback(() => {
    // Find last user message and resend
    const lastUserMessageIndex = messages.map(m => m.role).lastIndexOf('user')
    if (lastUserMessageIndex >= 0) {
      const lastUserMessage = messages[lastUserMessageIndex]
      setInput(lastUserMessage.content)
      // TODO: Implement proper retry functionality with backend
    }
  }, [messages])

  /**
   * Handle Enter key press
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  /**
   * Get the last user message for retry
   */
  const canRetry = messages.filter(m => m.role === 'user').length > 0 && !isStreaming

  return (
    <div className="flex h-full">
      {/* Session Sidebar - Desktop */}
      <div
        className={cn(
          'hidden lg:block transition-all duration-300',
          sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'
        )}
      >
        <SessionSidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          isLoading={isLoadingSessions}
          onSelectSession={async (sessionId) => {
            await switchSession(sessionId)
          }}
          onCreateSession={async (title) => {
            await createSession(title)
            clearMessages()
          }}
          onDeleteSession={deleteSession}
        />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed left-0 top-0 bottom-0 w-72 max-w-[80vw]">
            <SessionSidebar
              sessions={sessions}
              currentSessionId={currentSessionId}
              isLoading={isLoadingSessions}
              onSelectSession={async (sessionId) => {
                await switchSession(sessionId)
                setSidebarOpen(false)
              }}
              onCreateSession={async (title) => {
                await createSession(title)
                clearMessages()
                setSidebarOpen(false)
              }}
              onDeleteSession={deleteSession}
              onClose={() => setSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="border-b p-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden"
              >
                <Menu className="h-5 w-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="hidden lg:flex"
              >
                {sidebarOpen ? (
                  <PanelLeftClose className="h-5 w-5" />
                ) : (
                  <PanelLeftOpen className="h-5 w-5" />
                )}
              </Button>
              <div>
                <h1 className="text-xl font-semibold">Chat</h1>
                <p className="text-sm text-muted-foreground">
                  {currentSessionId
                    ? 'Active conversation'
                    : 'Start a new conversation'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Retry button */}
              {canRetry && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRetry}
                  title="Retry last message"
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              )}

              {/* Clear button */}
              {messages.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearConversation}
                  title="Clear conversation"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="border-b bg-destructive/10 px-4 py-2">
            <div className="flex items-center justify-between">
              <p className="text-sm text-destructive">{error}</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearError}
                className="h-6"
              >
                Dismiss
              </Button>
            </div>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1" ref={scrollRef}>
          <div className="p-4">
            {messages.length === 0 && !isLoadingSessions ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
                <div className="w-16 h-16 rounded-2xl bg-primary flex items-center justify-center mb-4">
                  <Bot className="h-8 w-8 text-primary-foreground" />
                </div>
                <h2 className="text-xl font-semibold mb-2">
                  Start a conversation
                </h2>
                <p className="text-muted-foreground max-w-md mb-4">
                  Send a message to begin chatting with your AI agent.
                  Make sure you have configured an LLM provider in the Config section.
                </p>
                <div className="flex gap-2 text-sm text-muted-foreground">
                  <kbd className="px-2 py-1 bg-muted rounded text-xs">Ctrl+K</kbd>
                  <span>to focus input</span>
                </div>
              </div>
            ) : isLoadingSessions && messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-4 max-w-3xl mx-auto">
                {messages.map((message) => (
                  <MarkdownMessage
                    key={message.id}
                    message={message}
                  />
                ))}

                {/* Tool usage indicator during streaming */}
                {isStreaming && streamingState.toolCalls.length > 0 && (
                  <ToolIndicator
                    toolCalls={streamingState.toolCalls}
                    isLoading={isStreaming}
                  />
                )}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-4 bg-background">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex gap-2">
              <textarea
                ref={inputRef}
                placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isSending || isStreaming}
                className={cn(
                  'flex-1 min-h-[56px] max-h-[200px] py-3 px-4 rounded-lg',
                  'border border-input bg-background',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                  'resize-none disabled:opacity-50'
                )}
                rows={1}
                style={{
                  height: 'auto',
                  minHeight: '56px',
                  maxHeight: '200px',
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`
                }}
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isSending || isStreaming}
                size="icon"
                className="h-[56px] w-[56px] flex-shrink-0"
              >
                {isSending || isStreaming ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2 text-center">
              AI-generated content may be inaccurate. Please verify important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
