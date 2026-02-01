import { NavLink } from 'react-router-dom'
import { MessageSquare, FileText, BarChart3, BookOpen } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: MessageSquare, label: 'Chat' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/dashboard', icon: BarChart3, label: 'Dashboard' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-gray-200 dark:border-gray-700">
        <BookOpen className="h-8 w-8 text-primary-600" />
        <div>
          <h1 className="font-bold text-gray-900 dark:text-gray-100">RAG</h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">Recherche Académique</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700/50'
              )
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-400 dark:text-gray-500 text-center">
          Claude + Voyage AI + ChromaDB
        </p>
      </div>
    </aside>
  )
}
