import Sidebar from './Sidebar'
import Header from './Header'

interface MainLayoutProps {
  children: React.ReactNode
  darkMode: boolean
  toggleDarkMode: () => void
}

export default function MainLayout({ children, darkMode, toggleDarkMode }: MainLayoutProps) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
