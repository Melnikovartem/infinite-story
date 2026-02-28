import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SegmentDisplay from '../SegmentDisplay'
import { StorySegment } from '../../types'

describe('SegmentDisplay', () => {
  const mockSegment: StorySegment = {
    id: 'test_segment',
    story_id: 'test_story',
    title: 'Test Scene',
    content: 'This is test content.',
    text_blocks: [
      {
        type: 'NARRATOR_DESCRIBING',
        content: 'A description',
        emotion: null,
        character: null
      }
    ],
    character_states: {
      eira: {
        name: 'Eira',
        emotion: 'concerned',
        status: 'present'
      }
    },
    location_state: {
      name: 'Test Location',
      description: 'A test place',
      atmosphere: 'mysterious'
    },
    is_generated: false,
    created_at: '2024-02-28T10:00:00Z',
    word_count: 100
  }

  it('displays segment title', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('Test Scene')).toBeInTheDocument()
  })

  it('displays segment content', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('This is test content.')).toBeInTheDocument()
  })

  it('displays character states', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('Eira')).toBeInTheDocument()
    expect(screen.getByText(/concerned/)).toBeInTheDocument()
  })

  it('displays location information', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('Test Location')).toBeInTheDocument()
    expect(screen.getByText('A test place')).toBeInTheDocument()
  })

  it('displays word count', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('100 words')).toBeInTheDocument()
  })

  it('displays atmosphere', () => {
    render(<SegmentDisplay segment={mockSegment} />)
    expect(screen.getByText('mysterious')).toBeInTheDocument()
  })
})
