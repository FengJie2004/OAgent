import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Session {
  id: string
  title: string
  agentConfigId?: string
  createdAt: number
  updatedAt: number
}

interface SessionState {
  sessions: Session[]
  activeSessionId: string | null

  addSession: (session: Omit<Session, 'id' | 'createdAt' | 'updatedAt'>) => string
  updateSession: (id: string, data: Partial<Session>) => void
  deleteSession: (id: string) => void
  setActiveSession: (id: string | null) => void
  getSession: (id: string) => Session | undefined
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,

      addSession: (session) => {
        const id = Date.now().toString()
        set((state) => ({
          sessions: [
            ...state.sessions,
            {
              ...session,
              id,
              createdAt: Date.now(),
              updatedAt: Date.now(),
            },
          ],
        }))
        return id
      },

      updateSession: (id, data) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, ...data, updatedAt: Date.now() } : s
          ),
        })),

      deleteSession: (id) =>
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== id),
          activeSessionId:
            state.activeSessionId === id ? null : state.activeSessionId,
        })),

      setActiveSession: (id) => set({ activeSessionId: id }),

      getSession: (id) => get().sessions.find((s) => s.id === id),
    }),
    {
      name: 'oagent-sessions',
    }
  )
)