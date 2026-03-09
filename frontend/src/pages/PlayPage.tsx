import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useStory } from '../contexts/StoryContext'
import { SegmentDisplay } from '../components/SegmentDisplay'
import { ChoiceDisplay } from '../components/ChoiceDisplay'
import { CustomChoiceInput } from '../components/CustomChoiceInput'
import { EpisodeHeader } from '../components/EpisodeHeader'
import { EpisodeTransition } from '../components/EpisodeTransition'
import { SegmentHistory } from '../components/SegmentHistory'
import { ReportModal } from '../components/ReportModal'
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
    sceneNumber,
    currentChoices,
    episodeInfo,
    showEpisodeTransition,
    history,
    startNewGame,
    resumeGame,
    selectChoice,
    submitCustomChoice,
    dismissEpisodeTransition,
    goToSegment,
    clearError
  } = useStory()

  const handleReportSubmit = async (reason: string, description: string) => {
    if (!story || !segment) return
    await api.submitReport(story.id, segment.id, reason, description, '')
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

  if (loading && !segment) {
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

  // Map choices from API format to ChoiceDisplay format
  const topChoices = (currentChoices?.top_2 || []).map(c => ({
    id: c.id,
    text: c.choice_text,
    popularity_score: c.popularity_score,
    is_custom: c.is_custom,
  }))
  
  const allChoices = (currentChoices?.all || []).map(c => ({
    id: c.id,
    text: c.choice_text,
    popularity_score: c.popularity_score,
    is_custom: c.is_custom,
  }))

  return (
    <div className="page play-page">
      {showEpisodeTransition && episodeInfo && (
        <EpisodeTransition
          fromEpisode={episodeInfo.number - 1}
          toEpisode={episodeInfo.number}
          onContinue={dismissEpisodeTransition}
        />
      )}
      <div className="play-container">
        <div className="play-header">
          <button className="back-button" onClick={() => navigate('/')}>
            &larr; Back
          </button>
          <h2>{story.title}</h2>
          <span className="scene-number">Scene {sceneNumber}</span>
          <button 
            className="report-button"
            onClick={() => setShowReportModal(true)}
            title="Report inappropriate content"
          >
            !
          </button>
        </div>

        {episodeInfo && (
          <EpisodeHeader episode={episodeInfo} />
        )}

        {error && (
          <div className="error">
            <p>{error}</p>
            <button onClick={clearError}>Dismiss</button>
          </div>
        )}

        {generating && (
          <div className="generating-overlay">
            <div className="generating-content">
              <div className="generating-quill" />
              <p className="generating-text">The story unfolds...</p>
              <p className="generating-subtext">AI is crafting your next scene</p>
            </div>
          </div>
        )}

        <SegmentHistory
          entries={history}
          currentSegmentId={segment.id}
          onJumpTo={goToSegment}
        />

        <div className="segment-container">
          <SegmentDisplay segment={segment} />
        </div>

        <div className="choices-container">
          <ChoiceDisplay
            topChoices={topChoices}
            allChoices={allChoices}
            onChoiceSelect={selectChoice}
            loading={loading || generating}
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
          onSubmit={handleReportSubmit}
        />
      </div>
    </div>
  )
}
