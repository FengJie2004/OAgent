import { ReactNode } from 'react'
import { Sidebar } from './Sidebar'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar className="w-64" />
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  )
}