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
      const response = await fetch(`http://localhost:8000/api/segments/${segmentId}/next`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_id: storyId,
          choice_text: choiceText,
          context: {
            previous_segments_count: 5,
            include_character_details: true,
            include_location_details: true,
            include_worldbuilding: true
          }
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
      const response = await fetch(`http://localhost:8000/api/segments/${segmentId}/choice/${choiceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ story_id: storyId })
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
  saveSession: async (session: { story_id: string; current_segment_id: string; visited_segments: string[]; scene_counter: number; start_time: string }) => {
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
   loadSession: async (storyId: string) => {
     try {
       const response = await fetch(`http://localhost:8000/api/sessions/${storyId}`)
       const json = await response.json()
       // Backend returns {found: boolean, session: SessionData | null}
       if (json.found && json.session) {
         return json.session
       }
       return { found: false }
     } catch (error) {
       console.error('loadSession error:', error)
       return { found: false }
     }
   },
  deleteSession: async (storyId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/sessions/${storyId}`, { method: 'DELETE' })
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
export const saveSession = (session: { story_id: string; current_segment_id: string; visited_segments: string[]; scene_counter: number; start_time: string }) =>
  api.saveSession(session)

/**
 * Load a saved session state
 */
export const loadSession = (storyId: string) => api.loadSession(storyId)

/**
 * Delete a saved session
 */
export const deleteSession = (storyId: string) => api.deleteSession(storyId)

/**
 * Submit a content report
 */
export const submitReport = (storyId: string, segmentId: string, reportType: string, description: string, reporterEmail: string) =>
  api.submitReport(storyId, segmentId, reportType, description, reporterEmail)
