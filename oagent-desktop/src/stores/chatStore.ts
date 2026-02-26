import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

interface ChatState {
  messages: Message[]
  currentSessionId: string | null
  isStreaming: boolean

  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  updateMessage: (id: string, content: string) => void
  setStreaming: (streaming: boolean) => void
  clearMessages: () => void
  setCurrentSession: (sessionId: string | null) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      currentSessionId: null,
      isStreaming: false,

      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: Date.now().toString(),
              timestamp: Date.now(),
            },
          ],
        })),

      updateMessage: (id, content) =>
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id ? { ...m, content } : m
          ),
        })),

      setStreaming: (streaming) => set({ isStreaming: streaming }),

      clearMessages: () => set({ messages: [] }),

      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
    }),
    {
      name: 'oagent-chat',
    }
  )
)