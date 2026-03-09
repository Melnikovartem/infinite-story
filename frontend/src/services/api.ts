/**
 * API Service Wrapper
 * 
 * This module abstracts all API calls, allowing easy swapping between
 * mock and real APIs. Change USE_MOCK to switch implementations.
 */

import * as mockApi from './mockApi'

// Toggle this to switch between mock and real API
const USE_MOCK = false

// Store for real API implementation
const realApi = {
  fetchStories: async () => {
    try {
      const response = await fetch('http://localhost:8000/api/stories')
      const json = await response.json()
      // Extract stories from success response format
      if (json.success && json.data?.stories) {
        return json.data.stories
      }
      throw new Error(json.error || 'Failed to fetch stories')
    } catch (error) {
      console.error('fetchStories error:', error)
      throw error
    }
  },
  fetchStoryDetail: async (storyId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/stories/${storyId}`)
      const json = await response.json()
      if (json.success && json.data) {
        return json.data
      }
      throw new Error(json.error || 'Failed to fetch story detail')
    } catch (error) {
      console.error('fetchStoryDetail error:', error)
      throw error
    }
  },
  fetchSegment: async (storyId: string, segmentId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/segments/${segmentId}?story_id=${storyId}`)
      const json = await response.json()
      if (json.success && json.data) {
        return {
          segment: json.data.segment,
          choices: {
            top_2: json.data.choices?.top || [],
            all: json.data.choices?.all || []
          }
        }
      }
      throw new Error(json.error || 'Failed to fetch segment')
    } catch (error) {
      console.error('fetchSegment error:', error)
      throw error
    }
  },
  generateNextScene: async (storyId: string, segmentId: string, choiceText: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/segments/${segmentId}/next?story_id=${storyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          choice_text: choiceText,
        })
      })
      const json = await response.json()
      if (json.success && json.data) {
        return json.data
      }
      throw new Error(json.error || 'Failed to generate scene')
    } catch (error) {
      console.error('generateNextScene error:', error)
      throw error
    }
  },
  navigateToChoice: async (storyId: string, segmentId: string, choiceId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/segments/${segmentId}/choice/${choiceId}?story_id=${storyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      const json = await response.json()
      if (json.success && json.data) {
        return json.data
      }
      throw new Error(json.error || 'Failed to navigate to choice')
    } catch (error) {
      console.error('navigateToChoice error:', error)
      throw error
    }
  },
  saveSession: async (session: { id: string; story_id: string; user_id: string; current_segment_id: string; visited_segments: string[]; visited_choices: string[] }) => {
    try {
      const response = await fetch('http://localhost:8000/api/sessions/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(session)
      })
      const json = await response.json()
      if (json.success) {
        return { success: true }
      }
      throw new Error(json.error || 'Failed to save session')
    } catch (error) {
      console.error('saveSession error:', error)
      throw error
    }
  },
   loadSession: async (storyId: string, sessionId: string) => {
     try {
       const response = await fetch(`http://localhost:8000/api/sessions/${storyId}/${sessionId}`)
       const json = await response.json()
       // Backend returns {found: boolean, session: SessionData | null}
       if (json.found && json.session) {
         return json.session
       }
       return null
     } catch (error) {
       console.error('loadSession error:', error)
       return null
     }
   },
  deleteSession: async (storyId: string, sessionId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/sessions/${storyId}/${sessionId}`, { method: 'DELETE' })
      const json = await response.json()
      if (json.success) {
        return { success: true }
      }
      throw new Error(json.error || 'Failed to delete session')
    } catch (error) {
      console.error('deleteSession error:', error)
      throw error
    }
  },
  submitReport: async (storyId: string, segmentId: string, reportType: string, description: string, reporterEmail: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_id: storyId,
          segment_id: segmentId,
          report_type: reportType,
          description,
          reporter_email: reporterEmail
        })
      })
      const json = await response.json()
      if (json.success) {
        return { success: true }
      }
      throw new Error(json.error || 'Failed to submit report')
    } catch (error) {
      console.error('submitReport error:', error)
      throw error
    }
  }
}

// Select which API to use
const api = USE_MOCK ? mockApi : realApi

/**
 * Fetch all available stories
 */
export const fetchStories = () => api.fetchStories()

/**
 * Fetch story details including start segment and characters
 */
export const fetchStoryDetail = (storyId: string) => api.fetchStoryDetail(storyId)

/**
 * Fetch a specific story segment with its choices
 */
export const fetchSegment = (storyId: string, segmentId: string) => api.fetchSegment(storyId, segmentId)

/**
 * Generate the next scene from a custom player choice
 */
export const generateNextScene = (storyId: string, segmentId: string, choiceText: string) =>
  api.generateNextScene(storyId, segmentId, choiceText)

/**
 * Navigate to an existing choice's destination segment
 */
export const navigateToChoice = (storyId: string, segmentId: string, choiceId: string) =>
  api.navigateToChoice(storyId, segmentId, choiceId)

/**
 * Save the current session state
 */
export const saveSession = (session: { id: string; story_id: string; user_id: string; current_segment_id: string; visited_segments: string[]; visited_choices: string[] }) =>
  api.saveSession(session)

/**
 * Load a saved session state
 */
export const loadSession = (storyId: string, sessionId: string) => api.loadSession(storyId, sessionId)

/**
 * Delete a saved session
 */
export const deleteSession = (storyId: string, sessionId: string) => api.deleteSession(storyId, sessionId)

/**
 * Submit a content report
 */
export const submitReport = (storyId: string, segmentId: string, reportType: string, description: string, reporterEmail: string) =>
  api.submitReport(storyId, segmentId, reportType, description, reporterEmail)

// ── Story Creation API ──

/**
 * Start creating a new story (async, returns immediately)
 */
export const createStory = async (request: {
  story_id: string;
  title: string;
  description: string;
  genre: string;
  world_input?: string;
  first_scene_input?: string;
}) => {
  const response = await fetch('http://localhost:8000/api/stories/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  const json = await response.json()
  if (json.success && json.data) {
    return json.data
  }
  throw new Error(json.error || 'Failed to start story creation')
}

/**
 * Poll creation status
 */
export const getCreationStatus = async (storyId: string) => {
  const response = await fetch(`http://localhost:8000/api/stories/create/${storyId}/status`)
  const json = await response.json()
  if (json.success && json.data) {
    return json.data
  }
  throw new Error(json.error || 'Failed to get creation status')
}

/**
 * Connect to creation SSE stream for real-time progress
 */
export const streamCreationProgress = (
  storyId: string,
  onStep: (step: { step: number; name: string; status: string; message: string }) => void,
  onDone: (result: any) => void,
  onError: (error: string) => void,
): (() => void) => {
  const eventSource = new EventSource(`http://localhost:8000/api/stories/create/${storyId}/stream`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'step') {
        onStep(data)
      } else if (data.type === 'done') {
        onDone(data.result)
        eventSource.close()
      } else if (data.type === 'error') {
        onError(data.error || data.message || 'Creation failed')
        eventSource.close()
      }
    } catch (e) {
      // ignore parse errors
    }
  }

  eventSource.onerror = () => {
    onError('Connection to creation stream lost')
    eventSource.close()
  }

  // Return cleanup function
  return () => eventSource.close()
}

/**
 * Delete a story
 */
export const deleteStory = async (storyId: string) => {
  const response = await fetch(`http://localhost:8000/api/stories/${storyId}`, {
    method: 'DELETE',
  })
  const json = await response.json()
  if (json.success) {
    return json.data
  }
  throw new Error(json.error || 'Failed to delete story')
}
