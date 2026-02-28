import React, { useEffect, useState } from 'react'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastProps {
  id: string
  message: string
  type?: ToastType
  duration?: number
  onClose?: (id: string) => void
  action?: {
    label: string
    onClick: () => void
  }
}

const typeStyles = {
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

export const Toast: React.FC<ToastProps> = ({
  id,
  message,
  type = 'info',
  duration = 4000,
  onClose,
  action,
}) => {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    if (duration <= 0) return

    const timer = setTimeout(() => {
      setIsVisible(false)
      onClose?.(id)
    }, duration)

    return () => clearTimeout(timer)
  }, [duration, id, onClose])

  if (!isVisible) return null

  const style = typeStyles[type]

  return (
    <div
      className={`
        ${style.container}
        rounded-lg
        p-md
        shadow-lg
        flex
        items-center
        justify-between
        gap-md
        animate-slide-in-up
        min-w-80
      `.trim()}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex items-center gap-md">
        <span
          className={`${style.color} text-lg flex-shrink-0`}
          aria-hidden="true"
        >
          {style.icon}
        </span>
        <p className="text-sm">{message}</p>
      </div>

      <div className="flex items-center gap-sm flex-shrink-0">
        {action && (
          <button
            onClick={action.onClick}
            className={`
              ${style.color}
              hover:opacity-70
              font-medium
              text-sm
              focus-visible:outline-2
              focus-visible:outline-offset-2
              focus-visible:outline-current
              rounded-md
              px-sm
              py-xs
              transition-opacity
            `.trim()}
          >
            {action.label}
          </button>
        )}

        <button
          onClick={() => {
            setIsVisible(false)
            onClose?.(id)
          }}
          className={`
            ${style.color}
            hover:opacity-70
            focus-visible:outline-2
            focus-visible:outline-offset-2
            focus-visible:outline-current
            rounded-md
            p-xs
            transition-opacity
          `.trim()}
          aria-label="Close notification"
        >
          ✕
        </button>
      </div>
    </div>
  )
}

interface ToastContainerProps {
  toasts: ToastProps[]
  onClose: (id: string) => void
}

export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onClose,
}) => {
  return (
    <div
      className="fixed bottom-lg right-lg space-y-md z-50 pointer-events-none"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
      aria-atomic="false"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast
            {...toast}
            onClose={onClose}
          />
        </div>
      ))}
    </div>
  )
}

/**
 * Hook for managing toasts
 */
export const useToast = () => {
  const [toasts, setToasts] = useState<ToastProps[]>([])

  const add = (
    message: string,
    options?: Partial<Omit<ToastProps, 'id' | 'message'>>
  ) => {
    const id = Math.random().toString(36).substr(2, 9)
    const toast: ToastProps = {
      id,
      message,
      type: 'info',
      duration: 4000,
      ...options,
    }
    setToasts((prev) => [...prev, toast])
    return id
  }

  const remove = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const success = (message: string, options?: Partial<Omit<ToastProps, 'id' | 'message' | 'type'>>) => {
    return add(message, { type: 'success', ...options })
  }

  const error = (message: string, options?: Partial<Omit<ToastProps, 'id' | 'message' | 'type'>>) => {
    return add(message, { type: 'error', ...options })
  }

  const warning = (message: string, options?: Partial<Omit<ToastProps, 'id' | 'message' | 'type'>>) => {
    return add(message, { type: 'warning', ...options })
  }

  const info = (message: string, options?: Partial<Omit<ToastProps, 'id' | 'message' | 'type'>>) => {
    return add(message, { type: 'info', ...options })
  }

  return { toasts, add, remove, success, error, warning, info }
}
