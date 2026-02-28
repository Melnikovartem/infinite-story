import React from 'react'

interface AppHeaderProps {
  title?: string
  subtitle?: string
  children?: React.ReactNode
  onTitleClick?: () => void
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  title = 'Infinite Stories',
  subtitle,
  children,
  onTitleClick,
}) => {
  return (
    <header className="bg-primary text-white" role="banner">
      <div className="container py-md">
        <div className="flex items-center justify-between gap-lg">
          <div className="flex-1">
            <button
              onClick={onTitleClick}
              className="text-2xl font-bold hover:opacity-90 transition-opacity focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white rounded-md px-sm py-xs"
              role="banner"
              aria-label={`${title} home`}
            >
              {title}
            </button>
            {subtitle && (
              <p className="text-sm opacity-90 mt-xs">
                {subtitle}
              </p>
            )}
          </div>

          {children && (
            <nav
              className="flex items-center gap-md"
              role="navigation"
              aria-label="Header navigation"
            >
              {children}
            </nav>
          )}
        </div>
      </div>
    </header>
  )
}
