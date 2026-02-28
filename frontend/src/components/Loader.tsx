import React from 'react'

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'spinner' | 'dots' | 'bar'
  label?: string
  fullscreen?: boolean
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
}

export const Loader: React.FC<LoaderProps> = ({
  size = 'md',
  variant = 'spinner',
  label = 'Loading...',
  fullscreen = false,
}) => {
  const content = (
    <div className="flex flex-col items-center gap-md">
      {variant === 'spinner' && (
        <div
          className={`
            ${sizeClasses[size]}
            border-4
            border-primary/20
            border-t-primary
            rounded-full
            animate-spin
          `.trim()}
          role="status"
          aria-label={label}
        />
      )}

      {variant === 'dots' && (
        <div className="flex gap-sm" role="status" aria-label={label}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={`
                ${sizeClasses[size]}
                bg-primary
                rounded-full
                animate-pulse
              `.trim()}
              style={{
                animationDelay: `${i * 0.15}s`,
              }}
            />
          ))}
        </div>
      )}

      {variant === 'bar' && (
        <div
          className={`
            w-full
            h-1
            bg-primary/10
            rounded-full
            overflow-hidden
          `.trim()}
          role="status"
          aria-label={label}
        >
          <div
            className="h-full bg-primary animate-shimmer"
            style={{
              backgroundSize: '200% 100%',
            }}
          />
        </div>
      )}

      {label && <span className="text-sm text-neutral-600">{label}</span>}
    </div>
  )

  if (fullscreen) {
    return (
      <div className="fixed inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-lg shadow-lg">
          {content}
        </div>
      </div>
    )
  }

  return content
}
