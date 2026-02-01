import { Trash2 } from 'lucide-react'
import { useChatStore } from '../stores/chatStore'
import { useRagQuery } from '../hooks/useQuery'
import { ChatInput, MessageList, FilterPanel } from '../components/chat'
import Button from '../components/ui/Button'

export default function ChatPage() {
  const { messages, filters, addMessage, clearMessages } = useChatStore()
  const ragQuery = useRagQuery()

  const handleSubmit = async (question: string) => {
    // Ajouter le message utilisateur
    addMessage({
      role: 'user',
      content: question,
    })

    try {
      const response = await ragQuery.mutateAsync({
        question,
        top_k: 5,
        year_min: filters.yearMin,
        year_max: filters.yearMax,
        authors: filters.authors,
      })

      // Ajouter la réponse de l'assistant
      addMessage({
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        processingTime: response.processing_time_ms,
      })
    } catch (error) {
      addMessage({
        role: 'assistant',
        content:
          "Désolé, une erreur s'est produite lors du traitement de votre question. Veuillez réessayer.",
      })
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header avec filtres */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between px-4 py-2">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Chat RAG
          </h1>
          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearMessages}
              leftIcon={<Trash2 className="h-4 w-4" />}
            >
              Effacer
            </Button>
          )}
        </div>
        <FilterPanel />
      </div>

      {/* Messages */}
      <MessageList messages={messages} isLoading={ragQuery.isPending} />

      {/* Input */}
      <div className="bg-white dark:bg-gray-800">
        <ChatInput
          onSubmit={handleSubmit}
          isLoading={ragQuery.isPending}
        />
      </div>
    </div>
  )
}
