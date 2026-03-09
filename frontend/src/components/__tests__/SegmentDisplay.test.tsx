import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SegmentDisplay } from '../SegmentDisplay'
import type { StorySegment } from '../../types'

describe('SegmentDisplay', () => {
  const mockSegment: StorySegment = {
    id: 'test_segment',
    story_id: 'test_story',
    short_description: 'The beginning of a journey',
    atmosphere: 'mysterious',
    text_blocks: [
      {
        type: 'NARRATOR_DESCRIBING',
        content: 'A description of the scene.',
        emotion: null,
        character: null
      },
      {
        type: 'CHARACTER_SPEECH',
        content: 'Hello, traveler.',
        emotion: 'friendly',
        character: 'Eira'
      }
    ],
  }

  it('displays segment description', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('The beginning of a journey')).toBeInTheDocument()
  })

  it('displays text block content', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('A description of the scene.')).toBeInTheDocument()
  })

  it('displays character speech', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('Hello, traveler.')).toBeInTheDocument()
    expect(screen.getByText('Eira')).toBeInTheDocument()
  })

  it('displays atmosphere', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('mysterious')).toBeInTheDocument()
  })
})
