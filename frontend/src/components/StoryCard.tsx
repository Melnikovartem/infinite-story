import React from 'react'
import { Card } from './Card'

interface StoryCardProps {
  id: string
  title: string
  description: string
  characterCount: number
  onClick?: (id: string) => void
  imageUrl?: string
}

export const StoryCard: React.FC<StoryCardProps> = ({
  id,
  title,
  description,
  characterCount,
  onClick,
  imageUrl,
}) => {
  return (
    <Card
      interactive={!!onClick}
      onClick={() => onClick?.(id)}
      className="overflow-hidden"
      role="article"
    >
      {/* Image Placeholder */}
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={title}
          className="w-full h-48 object-cover"
        />
      ) : (
        <div className="w-full h-48 bg-gradient-to-br from-primary/10 to-secondary/10 flex items-center justify-center">
          <span className="text-4xl">📖</span>
        </div>
      )}

      {/* Content */}
      <div className="p-lg space-y-md">
        <h3 className="text-xl font-bold text-neutral-900 line-clamp-2">
          {title}
        </h3>

        <p className="text-neutral-600 line-clamp-3">
          {description}
        </p>

        {/* Meta Info */}
        <div className="flex items-center gap-md pt-md border-t border-neutral-200 text-sm text-neutral-600">
          <span className="flex items-center gap-xs">
            <span>👥</span>
            {characterCount} character{characterCount !== 1 ? 's' : ''}
          </span>
        </div>

        {/* CTA */}
        {onClick && (
          <div className="pt-md">
            <button className="w-full btn btn-primary text-center">
              Play Story →
            </button>
          </div>
        )}
      </div>
    </Card>
  )
}
