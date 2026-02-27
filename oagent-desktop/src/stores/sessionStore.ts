/**
 * Session Store for OAgent Desktop
 *
 * Manages chat sessions with backend API integration.
 * This store is deprecated in favor of the enhanced chatStore.ts
 * but kept for backward compatibility.
 *
 * @deprecated Use useChatStore from './chatStore' instead
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../lib/api'
import type { ChatSession } from '../lib/types'

/**
 * Extended session with local UI state
 */
export interface Session extends Omit<ChatSession, 'messages'> {
  messageCount?: number
}

/**
 * Session store state
 */
interface SessionStoreState {
  // State
  sessions: Session[]
  activeSessionId: string | null
  isLoading: boolean
  error: string | null

  // CRUD Operations
  fetchSessions: () => Promise<void>
  createSession: (title?: string, agentConfigId?: string) => Promise<Session>
  updateSession: (id: string, data: Partial<Session>) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  setActiveSession: (id: string | null) => void

  // Selectors
  getSession: (id: string) => Session | undefined
  getActiveSession: () => Session | undefined

  // Utility
  clearError: () => void
}

/**
 * Transform API ChatSession to local Session format
 */
function transformSession(apiSession: ChatSession): Session {
  return {
    id: apiSession.id,
    title: apiSession.title || '',
    agent_config_id: apiSession.agent_config_id,
    created_at: apiSession.created_at,
    updated_at: apiSession.updated_at,
    messageCount: apiSession.messages?.length || 0,
  }
}

/**
 * Session store
 */
export const useSessionStore = create<SessionStoreState>()(
  persist(
    (set, get) => ({
      // Initial state
      sessions: [],
      activeSessionId: null,
      isLoading: false,
      error: null,

      // Fetch all sessions from backend
      fetchSessions: async () => {
        set({ isLoading: true, error: null })
        try {
          const sessions = await api.chat.listSessions()
          const transformedSessions = sessions.map(transformSession)

          set({
            sessions: transformedSessions,
            isLoading: false,
          })
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to fetch sessions',
          })
          throw error
        }
      },

      // Create new session
      createSession: async (title?: string, agentConfigId?: string) => {
        set({ isLoading: true, error: null })
        try {
          const newSession = await api.chat.createSession({
            title: title || 'New Chat',
            agent_config_id: agentConfigId,
          })

          const transformedSession = transformSession(newSession)

          set((state) => ({
            sessions: [...state.sessions, transformedSession],
            activeSessionId: transformedSession.id,
            isLoading: false,
          }))

          return transformedSession
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to create session',
          })
          throw error
        }
      },

      // Update session
      updateSession: async (id: string, data: Partial<Session>) => {
        try {
          // Note: Backend API may not support session updates yet
          // This is a local update only
          set((state) => ({
            sessions: state.sessions.map((s) =>
              s.id === id
                ? { ...s, ...data, updated_at: new Date().toISOString() }
                : s
            ),
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update session',
          })
          throw error
        }
      },

      // Delete session
      deleteSession: async (id: string) => {
        set({ isLoading: true, error: null })
        try {
          await api.chat.deleteSession(id)

          set((state) => {
            const newSessions = state.sessions.filter((s) => s.id !== id)
            const newActiveSessionId =
              state.activeSessionId === id
                ? newSessions.length > 0
                  ? newSessions[0].id
                  : null
                : state.activeSessionId

            return {
              sessions: newSessions,
              activeSessionId: newActiveSessionId,
              isLoading: false,
            }
          })
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to delete session',
          })
          throw error
        }
      },

      // Set active session
      setActiveSession: (id: string | null) => {
        set({ activeSessionId: id })
      },

      // Get session by ID
      getSession: (id: string) => {
        return get().sessions.find((s) => s.id === id)
      },

      // Get active session
      getActiveSession: () => {
        const { sessions, activeSessionId } = get()
        return sessions.find((s) => s.id === activeSessionId)
      },

      // Clear error
      clearError: () => {
        set({ error: null })
      },
    }),
    {
      name: 'oagent-sessions',
      // Persist sessions and active session ID
      partialize: (state) => ({
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
      }),
    }
  )
)

/**
 * Get active session helper
 */
export const getActiveSession = (): Session | undefined => {
  return useSessionStore.getState().getActiveSession()
}

/**
 * Get session by ID helper
 */
export const getSessionById = (id: string): Session | undefined => {
  return useSessionStore.getState().getSession(id)
}
