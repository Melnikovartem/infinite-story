import React from 'react'

interface EpisodeTransitionProps {
  fromEpisode: number
  toEpisode: number
  onContinue: () => void
  className?: string
}

/**
 * Full-screen interstitial shown when an episode transition occurs.
 */
export const EpisodeTransition: React.FC<EpisodeTransitionProps> = ({
  fromEpisode,
  toEpisode,
  onContinue,
  className = '',
}) => {
  return (
    <div
      className={`
        fixed inset-0 z-50 bg-black/80
        flex items-center justify-center
        ${className}
      `.trim()}
      role="dialog"
      aria-modal="true"
      aria-label="Episode transition"
    >
      <div className="text-center max-w-md px-lg">
        <p className="text-neutral-400 text-sm uppercase tracking-wider mb-md">
          End of Episode {fromEpisode}
        </p>
        <h2 className="text-3xl font-bold text-white mb-lg">
          Episode {toEpisode}
        </h2>
        <p className="text-neutral-300 mb-xl">
          The story continues...
        </p>
        <button
          onClick={onContinue}
          className="bg-primary text-white px-xl py-md rounded-lg font-medium hover:bg-primary/90 transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  )
}
