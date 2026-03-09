import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { StoryDetail } from '../types'
import * as api from '../services/api'
import { CharacterAvatar } from '../components/CharacterAvatar'
import './StoryDetailPage.css'

export default function StoryDetailPage() {
  const { storyId } = useParams<{ storyId: string }>()
  const navigate = useNavigate()
  const [story, setStory] = useState<StoryDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasSession, setHasSession] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const loadStory = async () => {
      if (!storyId) return

      try {
        setLoading(true)
        const storyDetail = await api.fetchStoryDetail(storyId)
        setStory(storyDetail)

        // Check for existing session
        const sessionId = `session_${storyId}_anonymous`
        const session = await api.loadSession(storyId, sessionId)
        setHasSession(!!session)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load story')
      } finally {
        setLoading(false)
      }
    }

    loadStory()
  }, [storyId])

  const handleStartNew = () => {
    if (storyId) {
      navigate(`/play/${storyId}?mode=new`)
    }
  }

  const handleResume = () => {
    if (storyId) {
      navigate(`/play/${storyId}?mode=resume`)
    }
  }

  const handleDelete = async () => {
    if (!storyId) return
    const confirmed = window.confirm(
      `Are you sure you want to delete "${story?.title || storyId}"? This cannot be undone.`
    )
    if (!confirmed) return

    setDeleting(true)
    try {
      await api.deleteStory(storyId)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete story')
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading story...</p>
        </div>
      </div>
    )
  }

  if (error || !story) {
    return (
      <div className="page">
        <div className="error">
          <p>Failed to load story: {error}</p>
          <button onClick={() => navigate('/')}>Back to Stories</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page story-detail-page">
      <div className="container">
        <div className="top-actions">
          <button className="back-button" onClick={() => navigate('/')}>
            ← Back
          </button>
          <div className="story-actions">
            <button className="action-button primary" onClick={handleStartNew}>
              Start New Game
            </button>
            {hasSession && (
              <button className="action-button" onClick={handleResume}>
                Resume Game
              </button>
            )}
            <button
              className="action-button danger"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Story'}
            </button>
          </div>
        </div>

        <div className="story-header">
          <h2>{story.title}</h2>
          <p className="author">By {story.author}</p>
          <p className="description">{story.description}</p>
        </div>

        <div className="story-info">
          <div className="info-section">
            <h3>Characters</h3>
            <div className="characters-list">
              {story.characters.map(character => (
                <div key={character.id} className="character-item">
                  <CharacterAvatar
                    shape={character.avatar_shape}
                    color={character.avatar_color}
                    name={character.name}
                    size="md"
                  />
                  <div className="character-info">
                    <p className="character-name">{character.name}</p>
                    <p className="character-desc">{character.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="info-section">
            <h3>Story Setting</h3>
            {story.locations.map(location => (
              <div key={location.id} className="location-item">
                <h4>{location.name}</h4>
                <p>{location.description}</p>
              </div>
            ))}
          </div>
         </div>
      </div>
    </div>
  )
}
