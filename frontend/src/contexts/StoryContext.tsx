import React, { createContext, useState, useCallback, type PropsWithChildren, type ReactNode } from 'react'
import type {
  Story,
  StorySegment,
  ChoicesResponse,
  StoryCharacter,
  StoryLocation,
  EpisodeInfo
} from '../types'
import * as api from '../services/api'

// Simple session state for the frontend
interface FrontendSession {
  id: string
  user_id: string
  story_id: string
  current_segment_id: string
  visited_segments: string[]
  visited_choices: string[]
}

// Generate a simple session ID (story_id + user_id)
function getSessionId(storyId: string, userId: string): string {
  return `session_${storyId}_${userId}`
}

// Default anonymous user
const DEFAULT_USER_ID = 'anonymous'

export interface HistoryEntry {
  segmentId: string
  description: string
  sceneNumber: number
}

export interface StoryContextType {
  // Data
  story: Story | null
  segment: StorySegment | null
  currentChoices: ChoicesResponse | null
  characters: StoryCharacter[]
  locations: StoryLocation[]
  sceneNumber: number
  episodeInfo: EpisodeInfo | null
  showEpisodeTransition: boolean
  history: HistoryEntry[]

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
  dismissEpisodeTransition: () => void
  clearError: () => void
}

export const StoryContext = createContext<StoryContextType | null>(null)

interface StoryProviderProps extends PropsWithChildren {
  children: ReactNode
}

export function StoryProvider({ children }: StoryProviderProps) {
  const [story, setStory] = useState<Story | null>(null)
  const [segment, setSegment] = useState<StorySegment | null>(null)
  const [currentChoices, setCurrentChoices] = useState<ChoicesResponse | null>(null)
  const [characters, setCharacters] = useState<StoryCharacter[]>([])
  const [locations, setLocations] = useState<StoryLocation[]>([])
  const [sceneNumber, setSceneNumber] = useState(1)
  const [episodeInfo, setEpisodeInfo] = useState<EpisodeInfo | null>(null)
  const [showEpisodeTransition, setShowEpisodeTransition] = useState(false)
  const [previousEpisodeNumber, setPreviousEpisodeNumber] = useState(0)
  const [session, setSession] = useState<FrontendSession | null>(null)

  const [history, setHistory] = useState<HistoryEntry[]>([])

  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const dismissEpisodeTransition = useCallback(() => {
    setShowEpisodeTransition(false)
  }, [])

  /**
   * Update episode info from an API response and detect episode transitions.
   */
  const updateEpisodeInfo = useCallback((responseData: Record<string, unknown>) => {
    const ep = responseData.episode as EpisodeInfo | undefined
    if (ep) {
      setEpisodeInfo(ep)
      // Detect episode transition: new episode number > previous
      if (ep.triggers_transition && previousEpisodeNumber > 0 && ep.number > previousEpisodeNumber) {
        setShowEpisodeTransition(true)
      }
      setPreviousEpisodeNumber(ep.number)
    }
  }, [previousEpisodeNumber])

  const saveCurrentSession = useCallback(async (
    storyId: string,
    segmentId: string,
    visitedSegments: string[],
    visitedChoices: string[]
  ) => {
    const sessionId = getSessionId(storyId, DEFAULT_USER_ID)
    const sessionData: FrontendSession = {
      id: sessionId,
      user_id: DEFAULT_USER_ID,
      story_id: storyId,
      current_segment_id: segmentId,
      visited_segments: visitedSegments,
      visited_choices: visitedChoices,
    }
    setSession(sessionData)
    try {
      await api.saveSession(sessionData)
    } catch (err) {
      console.error('Failed to save session:', err)
    }
  }, [])

  const loadStory = useCallback(async (storyId: string) => {
    setLoading(true)
    setError(null)
    try {
      // Load story details
      const storyDetail = await api.fetchStoryDetail(storyId)
      setStory(storyDetail)
      setCharacters(storyDetail.characters || [])
      setLocations(storyDetail.locations || [])

      // Load the start segment
      if (!storyDetail.start_segment_id) {
        throw new Error('Story has no starting segment')
      }

      const segmentResponse = await api.fetchSegment(storyId, storyDetail.start_segment_id)
      setSegment(segmentResponse.segment)
      setCurrentChoices(segmentResponse.choices)
      setSceneNumber(1)
      setHistory([{
        segmentId: segmentResponse.segment.id,
        description: segmentResponse.segment.short_description || 'The beginning',
        sceneNumber: 1,
      }])
      // Extract episode info if present
      if ((segmentResponse as Record<string, unknown>).episode) {
        updateEpisodeInfo(segmentResponse as Record<string, unknown>)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load story'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [updateEpisodeInfo])

  const startNewGame = useCallback(async (storyId: string) => {
    // Delete any existing session
    const sessionId = getSessionId(storyId, DEFAULT_USER_ID)
    try {
      await api.deleteSession(storyId, sessionId)
    } catch {
      // Session may not exist, that's fine
    }
    setHistory([])
    await loadStory(storyId)
  }, [loadStory])

  const resumeGame = useCallback(async (storyId: string) => {
    setLoading(true)
    setError(null)
    try {
      const sessionId = getSessionId(storyId, DEFAULT_USER_ID)
      const savedSession = await api.loadSession(storyId, sessionId)
      
      if (!savedSession) {
        // No saved session, start fresh
        setLoading(false)
        await startNewGame(storyId)
        return
      }

      // Load story details
      const storyDetail = await api.fetchStoryDetail(storyId)
      setStory(storyDetail)
      setCharacters(storyDetail.characters || [])
      setLocations(storyDetail.locations || [])
      
      // Restore session
      setSession({
        id: savedSession.id || sessionId,
        user_id: savedSession.user_id || DEFAULT_USER_ID,
        story_id: storyId,
        current_segment_id: savedSession.current_segment_id,
        visited_segments: savedSession.visited_segments || [],
        visited_choices: savedSession.visited_choices || [],
      })

      // Load the current segment
      const segmentResponse = await api.fetchSegment(storyId, savedSession.current_segment_id)
      setSegment(segmentResponse.segment)
      setCurrentChoices(segmentResponse.choices)
      setSceneNumber((savedSession.visited_segments || []).length + 1)
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

      // Update session
      const newVisitedSegments = [...(session?.visited_segments || []), segmentId]
      const newSceneNumber = newVisitedSegments.length + 1
      setSceneNumber(newSceneNumber)

      await saveCurrentSession(
        story.id,
        segmentId,
        newVisitedSegments,
        session?.visited_choices || []
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load segment'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [story, session, saveCurrentSession])

  const selectChoice = useCallback(async (choiceId: string) => {
    if (!story || !segment) return

    setLoading(true)
    setError(null)
    try {
      // Call navigate-to-choice endpoint (handles both existing and AI generation)
      const response = await api.navigateToChoice(story.id, segment.id, choiceId)
      
      // Update with the returned segment and choices
      setSegment(response.segment)
      setCurrentChoices(response.choices)
      updateEpisodeInfo(response)

      // Update session
      const newVisitedSegments = [...(session?.visited_segments || []), response.segment.id]
      const newVisitedChoices = [...(session?.visited_choices || []), choiceId]
      const newSceneNumber = newVisitedSegments.length + 1
      setSceneNumber(newSceneNumber)

      // Push to history
      setHistory(prev => [...prev, {
        segmentId: response.segment.id,
        description: response.segment.short_description || `Scene ${newSceneNumber}`,
        sceneNumber: newSceneNumber,
      }])

      await saveCurrentSession(
        story.id,
        response.segment.id,
        newVisitedSegments,
        newVisitedChoices
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to select choice'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [story, segment, session, saveCurrentSession])

  const submitCustomChoice = useCallback(async (choiceText: string) => {
    if (!story || !segment) return

    setGenerating(true)
    setError(null)
    try {
      // Call generate endpoint with custom text
      const response = await api.generateNextScene(story.id, segment.id, choiceText)
      
      // Update with the returned segment and choices
      setSegment(response.segment)
      setCurrentChoices(response.choices)
      updateEpisodeInfo(response)

      // Update session
      const newVisitedSegments = [...(session?.visited_segments || []), response.segment.id]
      const newSceneNumber = newVisitedSegments.length + 1
      setSceneNumber(newSceneNumber)

      // Push to history
      setHistory(prev => [...prev, {
        segmentId: response.segment.id,
        description: response.segment.short_description || `Scene ${newSceneNumber}`,
        sceneNumber: newSceneNumber,
      }])

      await saveCurrentSession(
        story.id,
        response.segment.id,
        newVisitedSegments,
        session?.visited_choices || []
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate scene'
      setError(message)
    } finally {
      setGenerating(false)
    }
  }, [story, segment, session, saveCurrentSession])

  const value: StoryContextType = {
    story,
    segment,
    currentChoices,
    characters,
    locations,
    sceneNumber,
    episodeInfo,
    showEpisodeTransition,
    history,
    loading,
    generating,
    error,
    loadStory,
    startNewGame,
    resumeGame,
    goToSegment,
    selectChoice,
    submitCustomChoice,
    dismissEpisodeTransition,
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
