import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Story } from '../types'
import * as api from '../services/api'
import './StoryListPage.css'

export default function StoryListPage() {
  const [stories, setStories] = useState<Story[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const loadStories = async () => {
      try {
        setLoading(true)
        const response = await api.fetchStories()
        // Handle both array format and object format
        const storiesList = Array.isArray(response) ? response : (response.stories || [])
        setStories(storiesList)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stories')
      } finally {
        setLoading(false)
      }
    }

    loadStories()
  }, [])

  if (loading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading stories...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="error">
          <p>Failed to load stories: {error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page story-list-page">
      <div className="container">
        <h2>Available Stories</h2>
        <div className="stories-grid">
          {stories.map(story => (
            <div key={story.id} className="story-card">
              <h3>{story.title}</h3>
              {story.genre && <p className="genre">{story.genre}</p>}
              <p className="description">{story.description}</p>
              <button
                className="play-button"
                onClick={() => navigate(`/story/${story.id}`)}
              >
                View Story
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
