import { User, Bot, Clock } from 'lucide-react'
import type { Message } from '../../api/types'
import { SourceList } from './SourceCard'
import clsx from 'clsx'

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={clsx('flex gap-3', isUser ? 'flex-row-reverse' : '')}>
      {/* Avatar */}
      <div
        className={clsx(
          'shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser
            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Contenu */}
      <div className={clsx('flex-1 max-w-[85%]', isUser ? 'text-right' : '')}>
        <div
          className={clsx(
            'inline-block px-4 py-3 rounded-2xl text-sm',
            isUser
              ? 'bg-primary-600 text-white rounded-br-md'
              : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-md'
          )}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>

        {/* Sources (uniquement pour l'assistant) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceList sources={message.sources} />
        )}

        {/* Métadonnées */}
        <div
          className={clsx(
            'flex items-center gap-2 mt-1 text-xs text-gray-400',
            isUser ? 'justify-end' : ''
          )}
        >
          {message.processingTime && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {(message.processingTime / 1000).toFixed(1)}s
            </span>
          )}
          <span>
            {new Date(message.timestamp).toLocaleTimeString('fr-FR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
      </div>
    </div>
  )
}
