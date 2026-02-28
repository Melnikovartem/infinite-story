import React from 'react'

interface ProgressCounterProps {
  sceneNumber: number
  elapsedTime?: number
  startDate?: string
  className?: string
}

const formatTime = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  })
}

export const ProgressCounter: React.FC<ProgressCounterProps> = ({
  sceneNumber,
  elapsedTime,
  startDate,
  className = '',
}) => {
  return (
    <div
      className={`
        bg-white
        border
        border-neutral-300
        rounded-lg
        px-lg
        py-md
        shadow-md
        ${className}
      `.trim()}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-lg flex-wrap">
        <div className="flex flex-col">
          <span className="text-sm font-medium text-neutral-600">Scene</span>
          <span className="text-2xl font-bold text-primary">
            {sceneNumber}
          </span>
        </div>

        {elapsedTime !== undefined && (
          <>
            <div className="w-px h-8 bg-neutral-300"></div>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-neutral-600">Elapsed</span>
              <span className="text-lg font-semibold text-neutral-800">
                {formatTime(elapsedTime)}
              </span>
            </div>
          </>
        )}

        {startDate && (
          <>
            <div className="w-px h-8 bg-neutral-300"></div>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-neutral-600">Started</span>
              <span className="text-sm text-neutral-600">
                {formatDate(startDate)}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
