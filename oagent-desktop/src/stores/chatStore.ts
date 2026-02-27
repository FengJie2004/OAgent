/**
 * Chat Store for OAgent Desktop
 *
 * Manages chat sessions, messages, and streaming state.
 * Uses Zustand for state management with persistence.
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { ChatSession as ApiChatSession, ChatMessage as ApiChatMessage } from '@/lib/types'

/**
 * Chat message with full backend compatibility
 * Extends API type with local UI state
 */
export interface ChatMessage extends ApiChatMessage {
  // Local UI state
  isStreaming?: boolean
  isError?: boolean
}

/**
 * Chat session
 * Extends API type with local UI state
 */
export interface ChatSession extends Omit<ApiChatSession, 'title'> {
  title: string | null
}

/**
 * Tool call information for UI display
 */
export interface ToolCallInfo {
  tool_name: string
  tool_args: Record<string, unknown>
  tool_result?: string
  status: 'pending' | 'running' | 'completed' | 'error'
}

/**
 * Streaming state
 */
export interface StreamingState {
  isActive: boolean
  sessionId: string | null
  messageId: string | null
  toolCalls: ToolCallInfo[]
  accumulatedContent: string
}

/**
 * Chat store state
 */
interface ChatStoreState {
  // Sessions
  sessions: ChatSession[]
  currentSessionId: string | null
  isLoadingSessions: boolean

  // Messages
  messages: ChatMessage[]

  // Streaming
  streamingState: StreamingState
  isStreaming: boolean

  // UI State
  sidebarOpen: boolean
  error: string | null

  // Session CRUD
  loadSessions: () => Promise<void>
  createSession: (title?: string, agentConfigId?: string) => Promise<ChatSession>
  deleteSession: (sessionId: string) => Promise<void>
  switchSession: (sessionId: string) => Promise<void>

  // Messages
  addMessage: (message: Omit<ChatMessage, 'id' | 'created_at'>) => void
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  clearMessages: () => void

  // Streaming
  startStreaming: (sessionId: string, messageId: string) => void
  stopStreaming: () => void
  updateStreamingContent: (content: string) => void
  addToolCall: (toolCall: ToolCallInfo) => void
  updateToolCall: (toolName: string, updates: Partial<ToolCallInfo>) => void

  // UI
  setSidebarOpen: (open: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

/**
 * Generate unique ID
 */
const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Format date to ISO string
 */
const toIsoString = (date: Date = new Date()): string => {
  return date.toISOString()
}

/**
 * Transform API ChatSession to local store format
 */
function transformSession(apiSession: ApiChatSession): ChatSession {
  return {
    ...apiSession,
    title: apiSession.title ?? null,
  }
}

/**
 * Transform API ChatMessage to local store format
 */
function transformMessage(apiMessage: ApiChatMessage): ChatMessage {
  return {
    ...apiMessage,
    tool_name: apiMessage.tool_name ?? undefined,
    tool_args: apiMessage.tool_args ?? undefined,
    tool_result: apiMessage.tool_result ?? undefined,
  }
}

/**
 * Chat store
 */
export const useChatStore = create<ChatStoreState>()(
  persist(
    (set, get) => ({
      // Initial state
      sessions: [],
      currentSessionId: null,
      isLoadingSessions: false,
      messages: [],
      streamingState: {
        isActive: false,
        sessionId: null,
        messageId: null,
        toolCalls: [],
        accumulatedContent: '',
      },
      isStreaming: false,
      sidebarOpen: true,
      error: null,

      // Load all sessions from backend
      loadSessions: async () => {
        set({ isLoadingSessions: true })
        try {
          const { api } = await import('@/lib/api')
          const sessions = await api.chat.listSessions()
          set({ sessions: sessions.map(transformSession), isLoadingSessions: false })

          // Load messages for current session if exists
          const { currentSessionId } = get()
          if (currentSessionId) {
            const session = sessions.find(s => s.id === currentSessionId)
            if (session) {
              set({ messages: (session.messages || []).map(transformMessage) })
            }
          }
        } catch (error) {
          console.error('Failed to load sessions:', error)
          set({
            isLoadingSessions: false,
            error: error instanceof Error ? error.message : 'Failed to load sessions'
          })
        }
      },

      // Create new session
      createSession: async (title?: string, agentConfigId?: string) => {
        try {
          const { api } = await import('@/lib/api')
          const newSession = await api.chat.createSession({
            title: title || 'New Chat',
            agent_config_id: agentConfigId,
          })

          const transformedSession = transformSession(newSession)

          set((state) => ({
            sessions: [...state.sessions, transformedSession],
            currentSessionId: transformedSession.id,
            messages: [],
          }))

          return transformedSession
        } catch (error) {
          console.error('Failed to create session:', error)
          set({
            error: error instanceof Error ? error.message : 'Failed to create session'
          })
          throw error
        }
      },

      // Delete session
      deleteSession: async (sessionId: string) => {
        try {
          const { api } = await import('@/lib/api')
          await api.chat.deleteSession(sessionId)

          set((state) => {
            const newSessions = state.sessions.filter(s => s.id !== sessionId)
            const newCurrentSessionId = state.currentSessionId === sessionId
              ? (newSessions[0]?.id || null)
              : state.currentSessionId

            return {
              sessions: newSessions,
              currentSessionId: newCurrentSessionId,
              messages: newCurrentSessionId === sessionId ? [] : state.messages,
            }
          })
        } catch (error) {
          console.error('Failed to delete session:', error)
          set({
            error: error instanceof Error ? error.message : 'Failed to delete session'
          })
          throw error
        }
      },

      // Switch to a different session
      switchSession: async (sessionId: string) => {
        set({ currentSessionId: sessionId })

        try {
          const { api } = await import('@/lib/api')
          const session = await api.chat.getSession(sessionId)
          set({ messages: (session.messages || []).map(transformMessage) })
        } catch (error) {
          console.error('Failed to load session messages:', error)
          set({ messages: [] })
        }
      },

      // Add a new message
      addMessage: (message) => {
        const newMessage: ChatMessage = {
          ...message,
          id: generateId(),
          created_at: toIsoString(),
        }

        set((state) => ({
          messages: [...state.messages, newMessage],
        }))
      },

      // Update an existing message
      updateMessage: (id, updates) => {
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id ? { ...m, ...updates } : m
          ),
        }))
      },

      // Clear all messages
      clearMessages: () => {
        set({ messages: [] })
      },

      // Start streaming
      startStreaming: (sessionId, messageId) => {
        set({
          isStreaming: true,
          streamingState: {
            isActive: true,
            sessionId,
            messageId,
            toolCalls: [],
            accumulatedContent: '',
          },
        })
      },

      // Stop streaming
      stopStreaming: () => {
        set({
          isStreaming: false,
          streamingState: {
            isActive: false,
            sessionId: null,
            messageId: null,
            toolCalls: [],
            accumulatedContent: '',
          },
        })
      },

      // Update streaming content
      updateStreamingContent: (content: string) => {
        set((state) => {
          const { messageId } = state.streamingState

          if (messageId) {
            const existingMessage = state.messages.find(m => m.id === messageId)

            if (existingMessage) {
              // Update existing message
              return {
                streamingState: {
                  ...state.streamingState,
                  accumulatedContent: state.streamingState.accumulatedContent + content,
                },
                messages: state.messages.map(m =>
                  m.id === messageId
                    ? {
                        ...m,
                        content: m.content + content,
                        isStreaming: true,
                      }
                    : m
                ),
              }
            } else {
              // Create new streaming message
              const newMessage: ChatMessage = {
                id: messageId,
                session_id: state.streamingState.sessionId || '',
                role: 'assistant',
                content,
                created_at: toIsoString(),
                isStreaming: true,
              }

              return {
                streamingState: {
                  ...state.streamingState,
                  accumulatedContent: content,
                },
                messages: [...state.messages, newMessage],
              }
            }
          }

          return state
        })
      },

      // Add tool call
      addToolCall: (toolCall) => {
        set((state) => ({
          streamingState: {
            ...state.streamingState,
            toolCalls: [...state.streamingState.toolCalls, toolCall],
          },
        }))
      },

      // Update tool call
      updateToolCall: (toolName, updates) => {
        set((state) => ({
          streamingState: {
            ...state.streamingState,
            toolCalls: state.streamingState.toolCalls.map(tc =>
              tc.tool_name === toolName ? { ...tc, ...updates } : tc
            ),
          },
        }))
      },

      // Set sidebar open state
      setSidebarOpen: (open) => {
        set({ sidebarOpen: open })
      },

      // Set error
      setError: (error) => {
        set({ error })
      },

      // Clear error
      clearError: () => {
        set({ error: null })
      },
    }),
    {
      name: 'oagent-chat-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
        messages: state.messages,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
)