import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import Button from '../ui/Button'

interface ChatInputProps {
  onSubmit: (question: string) => void
  isLoading: boolean
  disabled?: boolean
}

export default function ChatInput({ onSubmit, isLoading, disabled }: ChatInputProps) {
  const [question, setQuestion] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize du textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [question])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (question.trim() && !isLoading && !disabled) {
      onSubmit(question.trim())
      setQuestion('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 dark:border-gray-700 p-4">
      <div className="flex gap-3 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Posez votre question sur les articles de recherche..."
            className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-white text-gray-900 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
            rows={1}
            disabled={disabled || isLoading}
          />
        </div>
        <Button
          type="submit"
          disabled={!question.trim() || disabled}
          isLoading={isLoading}
          className="h-12 w-12 shrink-0"
          aria-label="Envoyer"
        >
          {!isLoading && <Send className="h-5 w-5" />}
        </Button>
      </div>
      <p className="text-xs text-gray-400 mt-2 text-center">
        Appuyez sur Entrer pour envoyer, Shift+Entrer pour un saut de ligne
      </p>
    </form>
  )
}
