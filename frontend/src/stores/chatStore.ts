import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Message, ChatFilters } from '../api/types'

interface ChatState {
  messages: Message[]
  filters: ChatFilters
  isProcessing: boolean

  // Actions
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  setProcessing: (isProcessing: boolean) => void
  setFilters: (filters: Partial<ChatFilters>) => void
  clearFilters: () => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      filters: {},
      isProcessing: false,

      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: crypto.randomUUID(),
              timestamp: new Date(),
            },
          ],
        })),

      setProcessing: (isProcessing) => set({ isProcessing }),

      setFilters: (filters) =>
        set((state) => ({
          filters: { ...state.filters, ...filters },
        })),

      clearFilters: () => set({ filters: {} }),

      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: 'rag-chat-storage',
      partialize: (state) => ({
        messages: state.messages.slice(-50), // Garder les 50 derniers messages
        filters: state.filters,
      }),
    }
  )
)
