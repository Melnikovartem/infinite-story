import React, { useState } from 'react'
import { Button } from './Button'

export interface Choice {
  id: string
  text: string
  popularity_score?: number
  is_custom?: boolean
}

interface ChoiceDisplayProps {
  topChoices: Choice[]
  allChoices: Choice[]
  onChoiceSelect: (choiceId: string) => void
  loading?: boolean
}

export const ChoiceDisplay: React.FC<ChoiceDisplayProps> = ({
  topChoices,
  allChoices,
  onChoiceSelect,
  loading = false,
}) => {
  const [showAll, setShowAll] = useState(false)

  const choicesToShow = showAll ? allChoices : topChoices

  return (
    <div className="space-y-lg" role="region" aria-label="Story choices">
      <h3 className="text-lg font-semibold text-neutral-900">
        What do you do?
      </h3>

      {/* Top Choices */}
      <div className="space-y-md" role="group" aria-label="Available choices">
        {choicesToShow.map((choice, index) => (
          <Button
            key={choice.id}
            onClick={() => onChoiceSelect(choice.id)}
            disabled={loading}
            isLoading={loading}
            className="w-full text-left h-auto py-md px-lg break-words whitespace-normal"
            variant={choice.is_custom ? 'secondary' : 'primary'}
            aria-label={`Choice ${index + 1}: ${choice.text}${choice.popularity_score ? ` (${choice.popularity_score} stars)` : ''}`}
          >
            <div className="flex justify-between items-start gap-md">
              <span className="flex-1">{choice.text}</span>
              {choice.popularity_score && (
                <span className="text-xs opacity-75 flex-shrink-0" aria-hidden="false">
                  ⭐ {choice.popularity_score}
                </span>
              )}
            </div>
          </Button>
        ))}
      </div>

      {/* Toggle Show All */}
      {allChoices.length > topChoices.length && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="text-primary hover:text-primary/80 text-sm font-medium transition-colors"
          aria-expanded={showAll}
          aria-controls="all-choices"
        >
          {showAll ? '← Show top choices' : `View all choices (${allChoices.length} total) →`}
        </button>
      )}
    </div>
  )
}
