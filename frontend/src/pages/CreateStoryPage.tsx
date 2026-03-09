import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../services/api'
import type { CreationStepUpdate, CreationSummary } from '../types'
import './CreateStoryPage.css'

const GENRES = [
  'Fantasy',
  'Sci-Fi',
  'Mystery',
  'Horror',
  'Adventure',
  'Romance',
  'Thriller',
  'Historical',
  'Post-Apocalyptic',
  'Steampunk',
  'Cyberpunk',
  'Urban Fantasy',
]

const STEP_NAMES: Record<number, string> = {
  0: 'Story Planner',
  1: 'World Generator',
  2: 'Faction Generator',
  3: 'Magic System',
  4: 'Location Generator',
  5: 'Arc Generator',
  6: 'Character Generator',
  7: 'Protagonist Selector',
  8: 'Opening Scene',
  9: 'Choice Generator',
}

type Phase = 'form' | 'generating' | 'done' | 'error'

export default function CreateStoryPage() {
  const navigate = useNavigate()

  // Form state
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [genre, setGenre] = useState('Fantasy')
  const [worldInput, setWorldInput] = useState('')
  const [sceneInput, setSceneInput] = useState('')

  // Generation state
  const [phase, setPhase] = useState<Phase>('form')
  const [steps, setSteps] = useState<CreationStepUpdate[]>([])
  const [result, setResult] = useState<CreationSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [storyId, setStoryId] = useState<string | null>(null)

  const slugify = (text: string) =>
    text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'untitled'

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !description.trim()) return

    const id = slugify(title)
    setStoryId(id)
    setPhase('generating')
    setSteps([])
    setError(null)
    setResult(null)

    try {
      await api.createStory({
        story_id: id,
        title: title.trim(),
        description: description.trim(),
        genre,
        world_input: worldInput.trim(),
        first_scene_input: sceneInput.trim(),
      })

      // Connect to SSE stream for progress
      api.streamCreationProgress(
        id,
        (step) => {
          setSteps(prev => {
            // Update existing step or add new one
            const existing = prev.findIndex(
              s => s.step === step.step && s.name === step.name
            )
            if (existing >= 0) {
              const updated = [...prev]
              updated[existing] = step
              return updated
            }
            return [...prev, step]
          })
        },
        (res) => {
          setResult(res)
          setPhase('done')
        },
        (err) => {
          setError(err)
          setPhase('error')
        },
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start creation')
      setPhase('error')
    }
  }, [title, description, genre, worldInput, sceneInput])

  const handleRetry = () => {
    setPhase('form')
    setSteps([])
    setError(null)
    setResult(null)
  }

  const completedCount = steps.filter(s => s.status === 'completed').length
  const failedCount = steps.filter(s => s.status === 'failed').length
  const progressPct = Math.round((completedCount / 10) * 100)

  return (
    <div className="page create-story-page">
      <h2>Create New Story</h2>
      <p className="subtitle">AI will generate a complete world, characters, factions, and opening scene</p>

      {phase === 'form' && (
        <form className="create-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="create-title">Title</label>
            <input
              id="create-title"
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="The Last Frontier"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="create-description">Description</label>
            <textarea
              id="create-description"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="A journey through forgotten lands where ancient powers awaken..."
              required
            />
            <span className="hint">Describe the premise, themes, and mood of your story</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="create-genre">Genre</label>
              <select id="create-genre" value={genre} onChange={e => setGenre(e.target.value)}>
                {GENRES.map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="create-world">World Vision (optional)</label>
            <textarea
              id="create-world"
              value={worldInput}
              onChange={e => setWorldInput(e.target.value)}
              placeholder="A crumbling empire where magic is dying, three rival factions compete..."
            />
            <span className="hint">Guide the AI's world-building, or leave empty for full AI creativity</span>
          </div>

          <div className="form-group">
            <label htmlFor="create-scene">Opening Scene Direction (optional)</label>
            <textarea
              id="create-scene"
              value={sceneInput}
              onChange={e => setSceneInput(e.target.value)}
              placeholder="Start in a busy marketplace as rumors of war spread..."
            />
            <span className="hint">Tell the AI how the story should begin, or leave empty</span>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-create" disabled={!title.trim() || !description.trim()}>
              Create Story
            </button>
            <button type="button" className="btn-back" onClick={() => navigate('/')}>
              Back
            </button>
          </div>
        </form>
      )}

      {phase === 'generating' && (
        <div className="creation-progress">
          <div className="progress-header">
            <h3>Creating your world...</h3>
            <span>{completedCount}/10 steps</span>
          </div>

          <div className="progress-bar-container">
            <div
              className={`progress-bar-fill ${failedCount > 0 ? 'failed' : ''}`}
              style={{ width: `${progressPct}%` }}
            />
          </div>

          <div className="step-list">
            {Array.from({ length: 10 }, (_, i) => {
              const step = steps.find(s => s.step === i && s.status !== 'pending')
              const latestForStep = steps
                .filter(s => s.step === i)
                .pop()

              const status = latestForStep?.status || 'pending'
              const message = latestForStep?.message || ''

              let icon = '\u25CB' // circle
              let iconClass = ''
              if (status === 'running') { icon = '\u25D4'; iconClass = 'spinning' }
              else if (status === 'completed') { icon = '\u2713' }
              else if (status === 'failed') { icon = '\u2717' }

              return (
                <div key={i} className={`step-item ${status}`}>
                  <span className={`step-icon ${iconClass}`}>{icon}</span>
                  <span className="step-name">{STEP_NAMES[i] || `Step ${i}`}</span>
                  <span className="step-message">{message}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {phase === 'done' && result && (
        <div className="creation-complete">
          <h3>Story Created!</h3>
          <p>Your world is ready to explore.</p>

          <div className="creation-summary">
            <div className="summary-item">
              <div className="count">{result.summary.factions}</div>
              <div className="label">Factions</div>
            </div>
            <div className="summary-item">
              <div className="count">{result.summary.locations}</div>
              <div className="label">Locations</div>
            </div>
            <div className="summary-item">
              <div className="count">{result.summary.characters}</div>
              <div className="label">Characters</div>
            </div>
            <div className="summary-item">
              <div className="count">{result.summary.arcs}</div>
              <div className="label">Story Arcs</div>
            </div>
            <div className="summary-item">
              <div className="count">{result.summary.choices}</div>
              <div className="label">Choices</div>
            </div>
            <div className="summary-item">
              <div className="count">{result.summary.has_magic_system ? 'Yes' : 'No'}</div>
              <div className="label">Magic System</div>
            </div>
          </div>

          <button className="btn-play" onClick={() => navigate(`/story/${storyId}`)}>
            Play Story
          </button>
        </div>
      )}

      {phase === 'error' && (
        <div className="creation-error">
          <h3>Creation Failed</h3>
          <p>{error}</p>
          <button className="btn-retry" onClick={handleRetry}>
            Try Again
          </button>
        </div>
      )}
    </div>
  )
}
