import React from 'react'

export type AlertVariant = 'success' | 'error' | 'warning' | 'info'

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant
  title?: string
  children: React.ReactNode
  onClose?: () => void
  dismissible?: boolean
}

const variantStyles = {
  success: {
    container: 'bg-green-50 border border-green-200 text-green-800',
    icon: '✓',
    color: 'text-green-600',
  },
  error: {
    container: 'bg-red-50 border border-red-200 text-red-800',
    icon: '✕',
    color: 'text-red-600',
  },
  warning: {
    container: 'bg-yellow-50 border border-yellow-200 text-yellow-800',
    icon: '⚠',
    color: 'text-yellow-600',
  },
  info: {
    container: 'bg-blue-50 border border-blue-200 text-blue-800',
    icon: 'ℹ',
    color: 'text-blue-600',
  },
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({
    variant = 'info',
    title,
    children,
    onClose,
    dismissible = false,
    className = '',
    role = 'alert',
    ...props
  }, ref) => {
    const style = variantStyles[variant]

    return (
      <div
        ref={ref}
        role={role}
        className={`
          ${style.container}
          rounded-lg
          p-md
          flex
          gap-md
          items-start
          animate-slide-in-down
          ${className}
        `.trim()}
        {...props}
      >
        <span
          className={`${style.color} text-lg font-bold flex-shrink-0 mt-xs`}
          aria-hidden="true"
        >
          {style.icon}
        </span>

        <div className="flex-1">
          {title && (
            <h3 className="font-semibold mb-sm">
              {title}
            </h3>
          )}
          <div className="text-sm">
            {children}
          </div>
        </div>

        {dismissible && onClose && (
          <button
            onClick={onClose}
            className={`
              flex-shrink-0
              ${style.color}
              hover:opacity-70
              focus-visible:outline-2
              focus-visible:outline-offset-2
              focus-visible:outline-primary
              rounded-md
              p-xs
            `.trim()}
            aria-label="Close alert"
          >
            ✕
          </button>
        )}
      </div>
    )
  }
)

Alert.displayName = 'Alert'
