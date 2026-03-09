import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import CreateStoryPage from '../CreateStoryPage'

// Mock the api module
vi.mock('../../services/api', () => ({
  createStory: vi.fn(),
  streamCreationProgress: vi.fn(),
}))

import * as api from '../../services/api'

describe('CreateStoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the form initially', () => {
    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Create New Story')).toBeInTheDocument()
    expect(screen.getByLabelText('Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
    expect(screen.getByLabelText('Genre')).toBeInTheDocument()
    expect(screen.getByText('Create Story')).toBeInTheDocument()
  })

  it('disables submit when title is empty', () => {
    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    const submitBtn = screen.getByText('Create Story')
    expect(submitBtn).toBeDisabled()
  })

  it('disables submit when description is empty', () => {
    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'My Story' },
    })

    const submitBtn = screen.getByText('Create Story')
    expect(submitBtn).toBeDisabled()
  })

  it('enables submit when title and description are filled', () => {
    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'My Story' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'A great adventure' },
    })

    const submitBtn = screen.getByText('Create Story')
    expect(submitBtn).not.toBeDisabled()
  })

  it('calls createStory on submit', async () => {
    vi.mocked(api.createStory).mockResolvedValue({
      story_id: 'my_story',
      status: 'running',
    })
    vi.mocked(api.streamCreationProgress).mockReturnValue(() => {})

    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'My Story' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'A great adventure' },
    })
    fireEvent.click(screen.getByText('Create Story'))

    await waitFor(() => {
      expect(api.createStory).toHaveBeenCalledWith({
        story_id: 'my_story',
        title: 'My Story',
        description: 'A great adventure',
        genre: 'Fantasy',
        world_input: '',
        first_scene_input: '',
      })
    })
  })

  it('shows progress view after submission', async () => {
    vi.mocked(api.createStory).mockResolvedValue({
      story_id: 'my_story',
      status: 'running',
    })
    vi.mocked(api.streamCreationProgress).mockReturnValue(() => {})

    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'My Story' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'A great adventure' },
    })
    fireEvent.click(screen.getByText('Create Story'))

    await waitFor(() => {
      expect(screen.getByText('Creating your world...')).toBeInTheDocument()
    })
  })

  it('shows error on API failure', async () => {
    vi.mocked(api.createStory).mockRejectedValue(new Error('API down'))

    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'My Story' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'A great adventure' },
    })
    fireEvent.click(screen.getByText('Create Story'))

    await waitFor(() => {
      expect(screen.getByText('Creation Failed')).toBeInTheDocument()
      expect(screen.getByText('API down')).toBeInTheDocument()
    })
  })

  it('has a back button that exists', () => {
    render(
      <BrowserRouter>
        <CreateStoryPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Back')).toBeInTheDocument()
  })
})
