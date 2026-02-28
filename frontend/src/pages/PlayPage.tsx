import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useStory } from '../contexts/StoryContext'
import SegmentDisplay from '../components/SegmentDisplay'
import ChoiceDisplay from '../components/ChoiceDisplay'
import CustomChoiceInput from '../components/CustomChoiceInput'
import ProgressCounter from '../components/ProgressCounter'
import ReportModal from '../components/ReportModal'
import * as api from '../services/api'
import './PlayPage.css'

export default function PlayPage() {
  const { storyId } = useParams<{ storyId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const mode = searchParams.get('mode') || 'new'
  const [showReportModal, setShowReportModal] = useState(false)

  const {
    story,
    segment,
    loading,
    generating,
    error,
    sceneCounter,
    startNewGame,
    resumeGame,
    selectChoice,
    submitCustomChoice,
    clearError
  } = useStory()

  const handleReportSubmit = async (email: string, description: string) => {
    if (!story || !segment) return
    await api.submitReport(story.id, segment.id, 'inappropriate_content', description, email)
  }

  useEffect(() => {
    if (!storyId) {
      navigate('/')
      return
    }

    if (mode === 'resume') {
      resumeGame(storyId)
    } else {
      startNewGame(storyId)
    }
  }, [storyId, mode, startNewGame, resumeGame, navigate])

  if (loading) {
    return (
      <div className="page play-page">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading story...</p>
        </div>
      </div>
    )
  }

  if (!story || !segment) {
    return (
      <div className="page play-page">
        <div className="error">
          <p>Failed to load story</p>
          <button onClick={() => navigate('/')}>Back to Stories</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page play-page">
      <div className="play-container">
        <div className="play-header">
          <button className="back-button" onClick={() => navigate('/')}>
            ← Back
          </button>
          <h2>{story.title}</h2>
          {sceneCounter && (
            <ProgressCounter sceneCounter={sceneCounter} />
          )}
          <button 
            className="report-button"
            onClick={() => setShowReportModal(true)}
            title="Report inappropriate content"
          >
            ⚠
          </button>
        </div>

        {error && (
          <div className="error">
            <p>{error}</p>
            <button onClick={clearError}>Dismiss</button>
          </div>
        )}

        <div className="segment-container">
          <SegmentDisplay segment={segment} />
        </div>

        <div className="choices-container">
          <h3>What do you do?</h3>
          <ChoiceDisplay
            onSelect={selectChoice}
            loading={loading}
          />
          <div className="custom-choice-section">
            <h4>Or write your own choice:</h4>
            <CustomChoiceInput
              onSubmit={submitCustomChoice}
              loading={generating}
            />
          </div>
        </div>

        <ReportModal
          isOpen={showReportModal}
          onClose={() => setShowReportModal(false)}
          _storyId={story.id}
          _segmentId={segment.id}
          onSubmit={handleReportSubmit}
        />
      </div>
    </div>
  )
}
