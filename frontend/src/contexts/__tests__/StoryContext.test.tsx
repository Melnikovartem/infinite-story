import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { StoryProvider, useStory } from '../StoryContext'


describe('StoryContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('provides initial state', () => {
    const { result } = renderHook(() => useStory(), {
      wrapper: StoryProvider
    })

    expect(result.current.story).toBeNull()
    expect(result.current.segment).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('throws error when used outside provider', () => {
    expect(() => {
      renderHook(() => useStory())
    }).toThrow('useStory must be used within StoryProvider')
  })

  it('calls clearError to reset error state', () => {
    const { result } = renderHook(() => useStory(), {
      wrapper: StoryProvider
    })

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBeNull()
  })
})
