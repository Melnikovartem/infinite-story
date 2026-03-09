import React from 'react'
import type { EpisodeInfo } from '../types'

interface EpisodeHeaderProps {
  episode: EpisodeInfo
  className?: string
}

/**
 * Displays current episode/arc info in a compact header bar.
 */
export const EpisodeHeader: React.FC<EpisodeHeaderProps> = ({
  episode,
  className = '',
}) => {
  if (!episode.arc_id) return null

  return (
    <div
      className={`
        bg-neutral-50 border border-neutral-200 rounded-md px-md py-sm
        flex items-center gap-md text-sm text-neutral-600
        ${className}
      `.trim()}
      role="status"
      aria-label="Episode info"
    >
      <span className="font-medium text-neutral-800">
        Episode {episode.number}
      </span>
      <span className="text-neutral-300">|</span>
      <span>
        Scene {episode.segment_in_episode}
      </span>
      {episode.tone && (
        <>
          <span className="text-neutral-300">|</span>
          <span className="italic">{episode.tone}</span>
        </>
      )}
      {episode.arc_title && (
        <>
          <span className="text-neutral-300">|</span>
          <span className="text-primary font-medium">{episode.arc_title}</span>
        </>
      )}
    </div>
  )
}
