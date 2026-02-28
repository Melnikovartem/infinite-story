import React from 'react'

interface LayoutProps {
  children: React.ReactNode
  header?: React.ReactNode
  sidebar?: React.ReactNode
  footer?: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  header,
  sidebar,
  footer,
}) => {
  return (
    <div className="flex flex-col h-screen bg-neutral-50">
      {/* Header */}
      {header && (
        <header className="bg-white border-b border-neutral-200 shadow-sm sticky top-0 z-40">
          <div className="container py-md">
            {header}
          </div>
        </header>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        {sidebar && (
          <aside className="w-64 bg-white border-r border-neutral-200 overflow-y-auto">
            {sidebar}
          </aside>
        )}

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="container py-lg">
            {children}
          </div>
        </main>
      </div>

      {/* Footer */}
      {footer && (
        <footer className="bg-white border-t border-neutral-200 py-md">
          <div className="container text-center text-sm text-neutral-600">
            {footer}
          </div>
        </footer>
      )}
    </div>
  )
}

interface PageProps {
  title?: string
  description?: string
  children: React.ReactNode
  actions?: React.ReactNode
}

export const Page: React.FC<PageProps> = ({
  title,
  description,
  children,
  actions,
}) => {
  return (
    <div className="space-y-lg">
      {(title || description || actions) && (
        <div className="flex justify-between items-start gap-lg">
          <div>
            {title && (
              <h1 className="text-4xl font-bold text-neutral-900 mb-md">
                {title}
              </h1>
            )}
            {description && (
              <p className="text-lg text-neutral-600">
                {description}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex gap-md">
              {actions}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  )
}

interface PageSectionProps {
  title?: string
  children: React.ReactNode
}

export const PageSection: React.FC<PageSectionProps> = ({
  title,
  children,
}) => {
  return (
    <section className="space-y-md">
      {title && (
        <h2 className="text-2xl font-bold text-neutral-900">
          {title}
        </h2>
      )}
      {children}
    </section>
  )
}
