import { SceneCounter } from '../types'
import './ProgressCounter.css'

interface ProgressCounterProps {
  sceneCounter: SceneCounter
}

export default function ProgressCounter({ sceneCounter }: ProgressCounterProps) {
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return 'Unknown'
    }
  }

  const elapsedTime = formatTime(sceneCounter.elapsed_seconds)
  const startDate = formatDate(sceneCounter.start_time)

  return (
    <div className="progress-counter">
      <div className="counter-item">
        <span className="label">Scene</span>
        <span className="value">{sceneCounter.scene_number}</span>
      </div>
      <span className="separator">•</span>
      <div className="counter-item">
        <span className="label">Elapsed</span>
        <span className="value">{elapsedTime}</span>
      </div>
      <span className="separator">•</span>
      <div className="counter-item">
        <span className="label">Started</span>
        <span className="value">{startDate}</span>
      </div>
    </div>
  )
}
