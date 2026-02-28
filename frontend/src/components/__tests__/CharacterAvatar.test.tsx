import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import CharacterAvatar from '../CharacterAvatar'

describe('CharacterAvatar', () => {
  it('renders with circle shape', () => {
    const { container } = render(
      <CharacterAvatar
        shape="circle"
        color="#FF6B6B"
        size="medium"
      />
    )
    const shape = container.querySelector('.circle')
    expect(shape).toBeInTheDocument()
    expect(shape).toHaveStyle({ backgroundColor: '#FF6B6B' })
  })

  it('renders with square shape', () => {
    const { container } = render(
      <CharacterAvatar
        shape="square"
        color="#4ECDC4"
        size="small"
      />
    )
    const shape = container.querySelector('.square')
    expect(shape).toBeInTheDocument()
  })

  it('renders with different sizes', () => {
    const { container, rerender } = render(
      <CharacterAvatar shape="circle" color="#000" size="small" />
    )
    expect(container.querySelector('.small')).toBeInTheDocument()

    rerender(
      <CharacterAvatar shape="circle" color="#000" size="medium" />
    )
    expect(container.querySelector('.medium')).toBeInTheDocument()

    rerender(
      <CharacterAvatar shape="circle" color="#000" size="large" />
    )
    expect(container.querySelector('.large')).toBeInTheDocument()
  })

  it('applies color to triangle shape', () => {
    const { container } = render(
      <CharacterAvatar
        shape="triangle"
        color="#FFA500"
        size="medium"
      />
    )
    const shape = container.querySelector('.triangle')
    expect(shape).toBeInTheDocument()
  })
})
