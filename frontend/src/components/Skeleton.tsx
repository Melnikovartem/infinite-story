import React from 'react'

interface SkeletonProps {
  count?: number
  height?: string | number
  width?: string | number
  className?: string
  circle?: boolean
  circle_radius?: string
}

export const Skeleton: React.FC<SkeletonProps> = ({
  count = 1,
  height = '1rem',
  width = '100%',
  className = '',
  circle = false,
  circle_radius = '50%',
}) => {
  const heightStyle = typeof height === 'number' ? `${height}px` : height
  const widthStyle = typeof width === 'number' ? `${width}px` : width

  const style: React.CSSProperties = {
    height: heightStyle,
    width: widthStyle,
  }

  const baseClass = `
    bg-neutral-200
    animate-pulse
    rounded-md
    ${className}
  `.trim()

  const circleClass = circle ? `rounded-full` : ''

  const skeleton = (
    <div
      style={style}
      className={`${baseClass} ${circleClass}`.trim()}
      aria-busy="true"
      aria-label="Loading"
    />
  )

  if (count === 1) {
    return skeleton
  }

  return (
    <div className="space-y-md">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={style}
          className={`${baseClass} ${circleClass}`.trim()}
          aria-busy="true"
          aria-label={`Loading item ${i + 1}`}
        />
      ))}
    </div>
  )
}

interface CardSkeletonProps {
  lines?: number
  showAvatar?: boolean
  className?: string
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({
  lines = 3,
  showAvatar = true,
  className = '',
}) => {
  return (
    <div className={`card ${className}`.trim()}>
      <div className="flex gap-md mb-lg">
        {showAvatar && (
          <Skeleton
            width={64}
            height={64}
            circle
            className="flex-shrink-0"
          />
        )}
        <div className="flex-1 space-y-md">
          <Skeleton height={24} width="80%" />
          <Skeleton height={16} width="60%" />
        </div>
      </div>
      <Skeleton count={lines} height={16} width="100%" />
    </div>
  )
}

interface SegmentSkeletonProps {
  showTitle?: boolean
  className?: string
}

export const SegmentSkeleton: React.FC<SegmentSkeletonProps> = ({
  showTitle = true,
  className = '',
}) => {
  return (
    <div className={`space-y-lg ${className}`.trim()}>
      {showTitle && (
        <div className="space-y-md">
          <Skeleton height={32} width="60%" />
          <Skeleton height={16} width="80%" />
        </div>
      )}
      <div className="space-y-md">
        <Skeleton count={4} height={16} width="100%" />
      </div>
      <div className="space-y-md">
        <Skeleton height={20} width="40%" />
        <Skeleton count={2} height={16} width="100%" />
      </div>
    </div>
  )
}
