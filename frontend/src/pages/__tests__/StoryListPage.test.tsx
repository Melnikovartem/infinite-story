import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import StoryListPage from '../StoryListPage'

// Mock the api module that StoryListPage actually imports
vi.mock('../../services/api', () => ({
  fetchStories: vi.fn(),
}))

import * as api from '../../services/api'

const mockStories = [
  {
    id: 'story_1',
    title: 'Story 1',
    description: 'Test story 1',
    genre: 'Fantasy',
    start_segment_id: 'seg_1',
    created_at: '2024-02-28T09:00:00Z'
  },
  {
    id: 'story_2',
    title: 'Story 2',
    description: 'Test story 2',
    genre: 'Sci-Fi',
    start_segment_id: 'seg_2',
    created_at: '2024-02-28T10:00:00Z'
  }
]

describe('StoryListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays loading state initially', () => {
    vi.mocked(api.fetchStories).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockStories), 100))
    )

    render(
      <BrowserRouter>
        <StoryListPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading stories...')).toBeInTheDocument()
  })

  it('displays stories after loading', async () => {
    vi.mocked(api.fetchStories).mockResolvedValue(mockStories)

    render(
      <BrowserRouter>
        <StoryListPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Story 1')).toBeInTheDocument()
      expect(screen.getByText('Story 2')).toBeInTheDocument()
    })
  })

  it('displays story descriptions', async () => {
    vi.mocked(api.fetchStories).mockResolvedValue(mockStories)

    render(
      <BrowserRouter>
        <StoryListPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Test story 1')).toBeInTheDocument()
      expect(screen.getByText('Test story 2')).toBeInTheDocument()
    })
  })

  it('displays error message on fetch failure', async () => {
    vi.mocked(api.fetchStories).mockRejectedValue(new Error('Network error'))

    render(
      <BrowserRouter>
        <StoryListPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Failed to load stories/)).toBeInTheDocument()
    })
  })
})
