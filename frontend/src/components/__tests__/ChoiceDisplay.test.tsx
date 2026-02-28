import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChoiceDisplay } from '../ChoiceDisplay'

describe('ChoiceDisplay', () => {
  const mockChoices = [
    { id: 'choice-1', text: 'First choice', popularity_score: 85 },
    { id: 'choice-2', text: 'Second choice', popularity_score: 72 },
    { id: 'choice-3', text: 'Third choice' },
  ]

  it('renders top choices', () => {
    render(
      <ChoiceDisplay
        topChoices={mockChoices.slice(0, 2)}
        allChoices={mockChoices}
        onChoiceSelect={() => {}}
      />
    )
    expect(screen.getByText('First choice')).toBeInTheDocument()
    expect(screen.getByText('Second choice')).toBeInTheDocument()
  })

  it('hides extra choices by default', () => {
    render(
      <ChoiceDisplay
        topChoices={mockChoices.slice(0, 2)}
        allChoices={mockChoices}
        onChoiceSelect={() => {}}
      />
    )
    expect(screen.queryByText('Third choice')).not.toBeInTheDocument()
  })

  it('shows all choices when toggled', async () => {
    const user = userEvent.setup()
    render(
      <ChoiceDisplay
        topChoices={mockChoices.slice(0, 2)}
        allChoices={mockChoices}
        onChoiceSelect={() => {}}
      />
    )

    const toggleButton = screen.getByText('View all choices →')
    await user.click(toggleButton)

    expect(screen.getByText('Third choice')).toBeInTheDocument()
  })

  it('calls onChoiceSelect when choice is clicked', async () => {
    const onChoiceSelect = vi.fn()
    const user = userEvent.setup()

    render(
      <ChoiceDisplay
        topChoices={mockChoices.slice(0, 1)}
        allChoices={mockChoices}
        onChoiceSelect={onChoiceSelect}
      />
    )

    await user.click(screen.getByRole('button', { name: /First choice/ }))
    expect(onChoiceSelect).toHaveBeenCalledWith('choice-1')
  })

  it('shows loading state', () => {
    render(
      <ChoiceDisplay
        topChoices={mockChoices.slice(0, 1)}
        allChoices={mockChoices}
        onChoiceSelect={() => {}}
        loading
      />
    )

    expect(screen.getByRole('button', { name: /First choice/ })).toBeDisabled()
  })
})
