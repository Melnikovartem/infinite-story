import React from 'react'
import type { AvatarShape } from '../types'

interface CharacterAvatarProps {
  shape: AvatarShape
  color: string
  name: string
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

const shapeComponents: Record<AvatarShape, (color: string) => React.ReactElement> = {
  square: (color) => (
    <rect x="25%" y="25%" width="50%" height="50%" fill={color} rx="4" />
  ),
  circle: (color) => (
    <circle cx="50%" cy="50%" r="35%" fill={color} />
  ),
  triangle: (color) => (
    <polygon points="50,15 85,70 15,70" fill={color} />
  ),
  diamond: (color) => (
    <polygon points="50,10 90,50 50,90 10,50" fill={color} />
  ),
  star: (color) => (
    <polygon
      points="50,15 61,39 87,39 71,55 80,79 50,63 20,79 29,55 13,39 39,39"
      fill={color}
    />
  ),
  pentagon: (color) => (
    <polygon
      points="50,15 92,35 73,80 27,80 8,35"
      fill={color}
    />
  ),
}

const sizeClasses = {
  sm: 'w-8 h-8',
  md: 'w-16 h-16',
  lg: 'w-24 h-24',
}

export const CharacterAvatar: React.FC<CharacterAvatarProps> = ({
  shape,
  color,
  name,
  size = 'md',
  showLabel = false,
  className = '',
}) => {
  const sizeClass = sizeClasses[size]
  
  return (
    <div className={`flex flex-col items-center gap-sm ${className}`.trim()}>
      <div
        className={`
          ${sizeClass}
          bg-neutral-100
          rounded-lg
          border-2
          border-neutral-300
          flex
          items-center
          justify-center
          shadow-md
          hover:shadow-lg
          transition-shadow
        `.trim()}
        role="img"
        aria-label={`${name} avatar - ${shape}`}
      >
        <svg
          viewBox="0 0 100 100"
          className="w-full h-full"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect x="0" y="0" width="100" height="100" fill="transparent" />
          {shapeComponents[shape](color)}
        </svg>
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-neutral-700 text-center max-w-16 truncate">
          {name}
        </span>
      )}
    </div>
  )
}
