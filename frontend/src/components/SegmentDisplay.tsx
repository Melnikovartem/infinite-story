import React from 'react'
import type { StorySegment } from '../types'
import './SegmentDisplay.css'

interface SegmentDisplayProps {
  segment: StorySegment
}

/**
 * Map text block types to CSS class names for styling.
 */
function blockTypeClass(type: string): string {
  const lower = type.toLowerCase()
  if (lower.includes('speech')) return 'block-speech'
  if (lower.includes('thought')) return 'block-thought'
  if (lower.includes('narrator')) return 'block-narrator'
  if (lower.includes('scene_title')) return 'block-title'
  if (lower.includes('location')) return 'block-location'
  if (lower.includes('sfx')) return 'block-sfx'
  if (lower.includes('visual')) return 'block-visual'
  if (lower.includes('flashback')) return 'block-flashback'
  if (lower.includes('dream')) return 'block-dream'
  if (lower.includes('poem') || lower.includes('song')) return 'block-poem'
  if (lower.includes('letter') || lower.includes('note')) return 'block-letter'
  if (lower.includes('system')) return 'block-system'
  return 'block-narrator'
}

export const SegmentDisplay: React.FC<SegmentDisplayProps> = ({ segment }) => {
  return (
    <div className="segment-display">
      {segment.short_description && (
        <h3 className="segment-description">{segment.short_description}</h3>
      )}

      {segment.atmosphere && (
        <p className="segment-atmosphere"><em>{segment.atmosphere}</em></p>
      )}

      <div className="segment-content">
        {segment.text_blocks.map((block, index) => (
          <div key={index} className={`text-block ${blockTypeClass(block.type)}`}>
            {block.character && (
              <span className="block-character">{block.character}</span>
            )}
            <p className="block-content">{block.content}</p>
            {block.emotion && (
              <span className="block-emotion">{block.emotion}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
