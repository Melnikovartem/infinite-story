import { useState } from 'react'
import { useStory } from '../contexts/StoryContext'
import './ChoiceDisplay.css'

interface ChoiceDisplayProps {
  onSelect: (choiceId: string) => void
  loading?: boolean
}

export default function ChoiceDisplay({ onSelect, loading }: ChoiceDisplayProps) {
  const { currentChoices } = useStory()
  const [showAll, setShowAll] = useState(false)

  if (!currentChoices) {
    return <div className="choices-placeholder">Loading choices...</div>
  }

  const { top_2, all } = currentChoices

  return (
    <div className="choice-display">
      <div className="top-choices">
        {top_2.map(choice => (
          <button
            key={choice.id}
            className="choice-button primary"
            onClick={() => onSelect(choice.id)}
            disabled={loading}
          >
            <span className="choice-text">{choice.choice_text}</span>
            {choice.popularity_score > 0 && (
              <span className="choice-popularity">
                {choice.popularity_score}% popular
              </span>
            )}
          </button>
        ))}
      </div>

      {all.length > top_2.length && (
        <div className="all-choices-section">
          {!showAll && (
            <button
              className="expand-button"
              onClick={() => setShowAll(true)}
            >
              View All {all.length} Choices
            </button>
          )}

          {showAll && (
            <div className="all-choices">
              {all.map(choice => (
                <button
                  key={choice.id}
                  className="choice-button"
                  onClick={() => onSelect(choice.id)}
                  disabled={loading}
                >
                  <span className="choice-text">{choice.choice_text}</span>
                  {choice.popularity_score > 0 && (
                    <span className="choice-popularity">
                      {choice.popularity_score}% popular
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
