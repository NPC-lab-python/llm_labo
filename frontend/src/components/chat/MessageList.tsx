import { useEffect, useRef } from 'react'
import { MessageSquare } from 'lucide-react'
import type { Message } from '../../api/types'
import MessageBubble from './MessageBubble'
import Spinner from '../ui/Spinner'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll vers le bas
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
        <MessageSquare className="h-16 w-16 mb-4 opacity-50" />
        <h2 className="text-xl font-medium mb-2">Posez votre question</h2>
        <p className="text-sm text-center max-w-md">
          Je peux rechercher dans vos articles de recherche et vous fournir des réponses
          sourcées.
        </p>
        <div className="mt-6 space-y-2 text-sm">
          <p className="text-gray-500 dark:text-gray-400">Exemples de questions :</p>
          <ul className="list-disc list-inside text-gray-400 dark:text-gray-500 space-y-1">
            <li>Quelles sont les méthodes de deep learning pour la NLP ?</li>
            <li>Comment fonctionne l'attention dans les transformers ?</li>
            <li>Quels sont les avantages du RAG par rapport au fine-tuning ?</li>
          </ul>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isLoading && (
        <div className="flex gap-3">
          <div className="shrink-0 w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
            <Spinner size="sm" />
          </div>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-bl-md px-4 py-3">
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <span>Recherche en cours</span>
              <span className="animate-pulse">...</span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
