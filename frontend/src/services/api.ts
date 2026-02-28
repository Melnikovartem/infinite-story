/**
 * API Service Wrapper
 * 
 * This module abstracts all API calls, allowing easy swapping between
 * mock and real APIs. Change USE_MOCK to switch implementations.
 */

import * as mockApi from './mockApi'

// Toggle this to switch between mock and real API
const USE_MOCK = true

// Store for real API implementation (to be added later)
const realApi = {
  fetchStories: async () => {
    const response = await fetch('http://localhost:8000/api/stories')
    return response.json()
  },
  fetchStoryDetail: async (storyId: string) => {
    const response = await fetch(`http://localhost:8000/api/stories/${storyId}`)
    return response.json()
  },
  fetchSegment: async (storyId: string, segmentId: string) => {
    const response = await fetch(`http://localhost:8000/api/segments/${segmentId}?story_id=${storyId}`)
    return response.json()
  },
  generateNextScene: async (storyId: string, segmentId: string, choiceText: string) => {
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
    return response.json()
  },
  navigateToChoice: async (storyId: string, segmentId: string, choiceId: string) => {
    const response = await fetch(`http://localhost:8000/api/segments/${segmentId}/choice/${choiceId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ story_id: storyId })
    })
    return response.json()
  },
  saveSession: async (session: { story_id: string; current_segment_id: string; visited_segments: string[]; scene_counter: number; start_time: string; last_updated?: string }) => {
    const response = await fetch('http://localhost:8000/api/sessions/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(session)
    })
    return response.json()
  },
  loadSession: async (storyId: string) => {
    const response = await fetch(`http://localhost:8000/api/sessions/${storyId}`)
    return response.json()
  },
  deleteSession: async (storyId: string) => {
    const response = await fetch(`http://localhost:8000/api/sessions/${storyId}`, { method: 'DELETE' })
    return response.json()
  },
  submitReport: async (storyId: string, segmentId: string, reportType: string, description: string, reporterEmail: string) => {
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
    return response.json()
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
