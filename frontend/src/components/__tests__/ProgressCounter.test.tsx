import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProgressCounter from '../ProgressCounter'
import { SceneCounter } from '../../types'

describe('ProgressCounter', () => {
  it('displays scene number', () => {
    const counter: SceneCounter = {
      scene_number: 5,
      start_time: '2024-02-28T14:00:00Z',
      elapsed_seconds: 0
    }
    render(<ProgressCounter sceneCounter={counter} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('formats elapsed time in minutes', () => {
    const counter: SceneCounter = {
      scene_number: 1,
      start_time: '2024-02-28T14:00:00Z',
      elapsed_seconds: 600 // 10 minutes
    }
    render(<ProgressCounter sceneCounter={counter} />)
    expect(screen.getByText('10m')).toBeInTheDocument()
  })

  it('formats elapsed time in hours and minutes', () => {
    const counter: SceneCounter = {
      scene_number: 1,
      start_time: '2024-02-28T14:00:00Z',
      elapsed_seconds: 7320 // 2h 2m
    }
    render(<ProgressCounter sceneCounter={counter} />)
    expect(screen.getByText('2h 2m')).toBeInTheDocument()
  })

  it('formats start date correctly', () => {
    const counter: SceneCounter = {
      scene_number: 1,
      start_time: '2024-02-28T14:00:00Z',
      elapsed_seconds: 0
    }
    render(<ProgressCounter sceneCounter={counter} />)
    // Feb 28 format
    expect(screen.getByText('Feb 28')).toBeInTheDocument()
  })
})
