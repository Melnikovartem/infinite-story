import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <Link to="/" className="logo">
            <h1>Infinite Story</h1>
          </Link>
          <nav className="nav">
            <Link to="/">Stories</Link>
          </nav>
        </div>
      </header>
      <main className="main">
        {children}
      </main>
      <footer className="footer">
        <p>&copy; 2024 Infinite Story Engine. All rights reserved.</p>
      </footer>
    </div>
  )
}
