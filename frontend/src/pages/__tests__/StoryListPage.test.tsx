import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import StoryListPage from '../StoryListPage'
import * as api from '../../services/mockApi'

vi.mock('../../services/mockApi')

const mockStories = [
  {
    id: 'story_1',
    title: 'Story 1',
    description: 'Test story 1',
    author: 'Author 1',
    start_segment_id: 'seg_1',
    created_at: '2024-02-28T09:00:00Z'
  },
  {
    id: 'story_2',
    title: 'Story 2',
    description: 'Test story 2',
    author: 'Author 2',
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
      () => new Promise(resolve => setTimeout(() => resolve({ stories: mockStories }), 100))
    )

    render(
      <BrowserRouter>
        <StoryListPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading stories...')).toBeInTheDocument()
  })

  it('displays stories after loading', async () => {
    vi.mocked(api.fetchStories).mockResolvedValue({ stories: mockStories })

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
    vi.mocked(api.fetchStories).mockResolvedValue({ stories: mockStories })

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
