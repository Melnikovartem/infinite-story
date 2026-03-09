import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressCounter } from '../ProgressCounter'

describe('ProgressCounter', () => {
  it('displays scene number', () => {
    render(<ProgressCounter sceneNumber={5} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('formats elapsed time in minutes', () => {
    render(<ProgressCounter sceneNumber={1} elapsedTime={600} />)
    expect(screen.getByText('10m')).toBeInTheDocument()
  })

  it('formats elapsed time in hours and minutes', () => {
    render(<ProgressCounter sceneNumber={1} elapsedTime={7320} />)
    expect(screen.getByText('2h 2m')).toBeInTheDocument()
  })

  it('formats start date correctly', () => {
    render(<ProgressCounter sceneNumber={1} startDate="2024-02-28T14:00:00Z" />)
    // Date format depends on locale, just check it renders
    expect(screen.getByText(/Feb/)).toBeInTheDocument()
  })
})
