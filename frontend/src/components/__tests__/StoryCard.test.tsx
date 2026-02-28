import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StoryCard } from '../StoryCard'

describe('StoryCard', () => {
  const mockProps = {
    id: 'test-story',
    title: 'Test Story',
    description: 'A test story description',
    characterCount: 3,
  }

  it('renders story information', () => {
    render(<StoryCard {...mockProps} />)
    expect(screen.getByText('Test Story')).toBeInTheDocument()
    expect(screen.getByText('A test story description')).toBeInTheDocument()
    expect(screen.getByText(/3 characters/)).toBeInTheDocument()
  })

  it('displays character count', () => {
    render(<StoryCard {...mockProps} />)
    expect(screen.getByText(/3 characters/)).toBeInTheDocument()
  })

  it('handles click event', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    
    render(
      <StoryCard
        {...mockProps}
        onClick={onClick}
      />
    )

    const button = screen.getByRole('button', { name: /Play Story/ })
    await user.click(button)

    expect(onClick).toHaveBeenCalledWith('test-story')
  })

  it('displays placeholder when no image', () => {
    render(<StoryCard {...mockProps} />)
    expect(screen.getByText('📖')).toBeInTheDocument()
  })

  it('displays image when provided', () => {
    render(
      <StoryCard
        {...mockProps}
        imageUrl="https://example.com/image.jpg"
      />
    )
    const img = screen.getByAltText('Test Story') as HTMLImageElement
    expect(img.src).toBe('https://example.com/image.jpg')
  })
})
