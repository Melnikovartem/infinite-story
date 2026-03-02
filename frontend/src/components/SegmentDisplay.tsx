import React from 'react'
import type { StorySegment } from '../types'
import './SegmentDisplay.css'

interface SegmentDisplayProps {
  segment: StorySegment
}

export const SegmentDisplay: React.FC<SegmentDisplayProps> = ({ segment }) => {
  return (
    <div className="segment-display">
      <h2 className="segment-title">{segment.title}</h2>

      <div className="segment-content">
        <p>{segment.content}</p>
      </div>

      {Object.keys(segment.character_states).length > 0 && (
        <div className="characters-present">
          <h4>Present Characters</h4>
          <div className="characters-list">
            {Object.entries(segment.character_states).map(([charId, state]) => (
              <div key={charId} className="character-state">
                <p className="char-name">{state.name}</p>
                {state.emotion && (
                  <p className="char-emotion">Feeling: {state.emotion}</p>
                )}
                <p className="char-status">
                  Status: <span className={`status-${state.status}`}>{state.status}</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {segment.location_state && (
        <div className="location-info">
          <h4>Location</h4>
          <div className="location-details">
            <p className="location-name">{segment.location_state.name}</p>
            <p className="location-desc">{segment.location_state.description}</p>
            {segment.location_state.atmosphere && (
              <p className="location-atmosphere">
                Atmosphere: <em>{segment.location_state.atmosphere}</em>
              </p>
            )}
          </div>
        </div>
      )}

      <div className="word-count">
        {segment.word_count} words
      </div>
    </div>
  )
}
