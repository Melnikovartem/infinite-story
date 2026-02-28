import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChoiceDisplay from '../ChoiceDisplay'

// Mock the useStory hook
vi.mock('../../contexts/StoryContext', async () => {
  const actual = await vi.importActual('../../contexts/StoryContext')
  return {
    ...actual,
    useStory: () => ({
      currentChoices: {
        top_2: [
          {
            id: 'choice_1',
            choice_text: 'Choice 1',
            popularity_score: 85,
            is_custom: false
          },
          {
            id: 'choice_2',
            choice_text: 'Choice 2',
            popularity_score: 78,
            is_custom: false
          }
        ],
        all: [
          {
            id: 'choice_1',
            choice_text: 'Choice 1',
            popularity_score: 85,
            is_custom: false
          },
          {
            id: 'choice_2',
            choice_text: 'Choice 2',
            popularity_score: 78,
            is_custom: false
          },
          {
            id: 'choice_3',
            choice_text: 'Choice 3',
            popularity_score: 62,
            is_custom: false
          }
        ]
      }
    })
  }
})

describe('ChoiceDisplay', () => {
  it('displays top 2 choices by default', async () => {
    const onSelect = vi.fn()
    render(
      <ChoiceDisplay onSelect={onSelect} loading={false} />
    )
    
    expect(screen.getByText('Choice 1')).toBeInTheDocument()
    expect(screen.getByText('Choice 2')).toBeInTheDocument()
  })

  it('shows expand button when more choices available', () => {
    const onSelect = vi.fn()
    render(
      <ChoiceDisplay onSelect={onSelect} loading={false} />
    )
    
    expect(screen.getByText(/View All 3 Choices/)).toBeInTheDocument()
  })

  it('expands to show all choices when button clicked', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    render(
      <ChoiceDisplay onSelect={onSelect} loading={false} />
    )

    const expandButton = screen.getByText(/View All 3 Choices/)
    await user.click(expandButton)

    expect(screen.getByText('Choice 3')).toBeInTheDocument()
  })

  it('calls onSelect when choice clicked', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    render(
      <ChoiceDisplay onSelect={onSelect} loading={false} />
    )

    const choice1 = screen.getByText('Choice 1')
    await user.click(choice1)

    expect(onSelect).toHaveBeenCalledWith('choice_1')
  })

  it('disables choices when loading', () => {
    const onSelect = vi.fn()
    const { container } = render(
      <ChoiceDisplay onSelect={onSelect} loading={true} />
    )

    const buttons = container.querySelectorAll('.choice-button')
    buttons.forEach(button => {
      expect(button).toBeDisabled()
    })
  })
})
