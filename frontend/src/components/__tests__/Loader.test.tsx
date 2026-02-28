import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Loader } from '../Loader'

describe('Loader', () => {
  it('renders spinner variant by default', () => {
    render(<Loader />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders with label', () => {
    render(<Loader label="Loading..." />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders dots variant', () => {
    render(<Loader variant="dots" />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders bar variant', () => {
    render(<Loader variant="bar" />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('supports different sizes', () => {
    const { rerender } = render(<Loader size="sm" />)
    let loader = screen.getByRole('status')
    expect(loader).toBeInTheDocument()

    rerender(<Loader size="lg" />)
    loader = screen.getByRole('status')
    expect(loader).toBeInTheDocument()
  })

  it('renders fullscreen version', () => {
    render(<Loader fullscreen label="Loading..." />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
})
