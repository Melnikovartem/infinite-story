import { useState } from 'react'
import './SegmentHistory.css'

interface HistoryEntry {
  segmentId: string
  description: string
  sceneNumber: number
}

interface SegmentHistoryProps {
  entries: HistoryEntry[]
  currentSegmentId: string | null
  onJumpTo?: (segmentId: string) => void
}

export function SegmentHistory({ entries, currentSegmentId, onJumpTo }: SegmentHistoryProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (entries.length === 0) return null

  return (
    <div className={`segment-history ${isOpen ? 'open' : ''}`}>
      <button
        className="history-toggle"
        onClick={() => setIsOpen(!isOpen)}
        title="Story history"
      >
        <span className="history-icon">&#x1D362;</span>
        <span className="history-count">{entries.length}</span>
      </button>

      {isOpen && (
        <div className="history-panel">
          <div className="history-header">
            <h4>Story Path</h4>
            <button className="history-close" onClick={() => setIsOpen(false)}>
              &times;
            </button>
          </div>
          <div className="history-list">
            {entries.map((entry, idx) => (
              <div
                key={entry.segmentId}
                className={`history-entry ${entry.segmentId === currentSegmentId ? 'current' : ''}`}
                onClick={() => onJumpTo?.(entry.segmentId)}
                role={onJumpTo ? 'button' : undefined}
                tabIndex={onJumpTo ? 0 : undefined}
              >
                <span className="entry-number">{entry.sceneNumber}</span>
                <span className="entry-line" />
                <span className="entry-desc">
                  {entry.description || `Scene ${entry.sceneNumber}`}
                </span>
                {idx === entries.length - 1 && entry.segmentId === currentSegmentId && (
                  <span className="entry-current-badge">Now</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
