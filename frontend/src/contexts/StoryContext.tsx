import React, { createContext, useState, useCallback, type PropsWithChildren, type ReactNode } from 'react'
import type {
  Story,
  StorySegment,
  SessionState,
  SceneCounter,
  ChoicesResponse,
  StoryCharacter,
  StoryLocation
} from '../types'
import * as api from '../services/api'

export interface StoryContextType {
  // Data
  story: Story | null
  segment: StorySegment | null
  sessionState: SessionState | null
  currentChoices: ChoicesResponse | null
  characters: StoryCharacter[]
  locations: StoryLocation[]
  sceneCounter: SceneCounter | null

  // UI States
  loading: boolean
  generating: boolean
  error: string | null

  // Actions
  loadStory: (storyId: string) => Promise<void>
  startNewGame: (storyId: string) => Promise<void>
  resumeGame: (storyId: string) => Promise<void>
  goToSegment: (segmentId: string) => Promise<void>
  selectChoice: (choiceId: string) => Promise<void>
  submitCustomChoice: (choiceText: string) => Promise<void>
  clearError: () => void
}

export const StoryContext = createContext<StoryContextType | null>(null)

interface StoryProviderProps extends PropsWithChildren {
  children: ReactNode
}

export function StoryProvider({ children }: StoryProviderProps) {
  const [story, setStory] = useState<Story | null>(null)
  const [segment, setSegment] = useState<StorySegment | null>(null)
  const [sessionState, setSessionState] = useState<SessionState | null>(null)
  const [currentChoices, setCurrentChoices] = useState<ChoicesResponse | null>(null)
  const [characters, setCharacters] = useState<StoryCharacter[]>([])
  const [locations, setLocations] = useState<StoryLocation[]>([])
  const [sceneCounter, setSceneCounter] = useState<SceneCounter | null>(null)

  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const loadStory = useCallback(async (storyId: string) => {
    setLoading(true)
    setError(null)
    try {
      const storyDetail = await api.fetchStoryDetail(storyId)
      setStory(storyDetail)
      setCharacters(storyDetail.characters)
      setLocations(storyDetail.locations)
      setSegment(storyDetail.start_segment)

      const segmentResponse = await api.fetchSegment(storyId, storyDetail.start_segment.id)
      setCurrentChoices(segmentResponse.choices)
      setSceneCounter(segmentResponse.scene_counter)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load story'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  const startNewGame = useCallback(async (storyId: string) => {
    await loadStory(storyId)
    // Delete any existing session
    await api.deleteSession(storyId)
  }, [loadStory])

  const resumeGame = useCallback(async (storyId: string) => {
    setLoading(true)
    setError(null)
    try {
      const session = await api.loadSession(storyId)
      if (!session) {
        await startNewGame(storyId)
        return
      }

      const storyDetail = await api.fetchStoryDetail(storyId)
      setStory(storyDetail)
      setCharacters(storyDetail.characters)
      setLocations(storyDetail.locations)
      setSessionState(session)

      const segmentResponse = await api.fetchSegment(storyId, session.current_segment_id)
      setSegment(segmentResponse.segment)
      setCurrentChoices(segmentResponse.choices)
      setSceneCounter(segmentResponse.scene_counter)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to resume game'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [startNewGame])

  const goToSegment = useCallback(async (segmentId: string) => {
    if (!story) return

    setLoading(true)
    setError(null)
    try {
      const segmentResponse = await api.fetchSegment(story.id, segmentId)
      setSegment(segmentResponse.segment)
      setCurrentChoices(segmentResponse.choices)
      setSceneCounter(segmentResponse.scene_counter)

      // Update session
      const newVisitedSegments = [...(sessionState?.visited_segments || []), segmentId]
      const newSceneCounter = (sessionState?.scene_counter || 0) + 1
      const startTime = sessionState?.start_time || new Date().toISOString()
      
      const updatedSession: SessionState = {
        story_id: story.id,
        current_segment_id: segmentId,
        visited_segments: newVisitedSegments,
        scene_counter: newSceneCounter,
        start_time: startTime,
        last_updated: new Date().toISOString()
      }
      setSessionState(updatedSession)
      await api.saveSession({
        story_id: story.id,
        current_segment_id: segmentId,
        visited_segments: newVisitedSegments,
        scene_counter: newSceneCounter,
        start_time: startTime
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load segment'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [story, sessionState])

  const selectChoice = useCallback(async (choiceId: string) => {
    if (!story || !segment) return

    setLoading(true)
    setError(null)
    try {
      const segmentResponse = await api.navigateToChoice(story.id, segment.id, choiceId)
      await goToSegment(segmentResponse.segment.id)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to select choice'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [story, segment, goToSegment])

  const submitCustomChoice = useCallback(async (choiceText: string) => {
    if (!story || !segment) return

    setGenerating(true)
    setError(null)
    try {
      const response = await api.generateNextScene(story.id, segment.id, choiceText)
      await goToSegment(response.new_segment.id)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate scene'
      setError(message)
    } finally {
      setGenerating(false)
    }
  }, [story, segment, goToSegment])

  const value: StoryContextType = {
    story,
    segment,
    sessionState,
    currentChoices,
    characters,
    locations,
    sceneCounter,
    loading,
    generating,
    error,
    loadStory,
    startNewGame,
    resumeGame,
    goToSegment,
    selectChoice,
    submitCustomChoice,
    clearError
  }

  return (
    <StoryContext.Provider value={value}>
      {children}
    </StoryContext.Provider>
  )
}

export function useStory(): StoryContextType {
  const context = React.useContext(StoryContext)
  if (!context) {
    throw new Error('useStory must be used within StoryProvider')
  }
  return context
}
