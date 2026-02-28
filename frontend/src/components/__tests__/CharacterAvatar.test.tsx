import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CharacterAvatar } from '../CharacterAvatar'

describe('CharacterAvatar', () => {
  it('renders with shape and color', () => {
    render(
      <CharacterAvatar
        shape="circle"
        color="#FF6B6B"
        name="Eira"
      />
    )
    const avatar = screen.getByRole('img', { name: 'Eira avatar - circle' })
    expect(avatar).toBeInTheDocument()
  })

  it('displays label when showLabel is true', () => {
    render(
      <CharacterAvatar
        shape="square"
        color="#4ECDC4"
        name="Brother Cellen"
        showLabel
      />
    )
    expect(screen.getByText('Brother Cellen')).toBeInTheDocument()
  })

  it('hides label when showLabel is false', () => {
    render(
      <CharacterAvatar
        shape="triangle"
        color="#45B7D1"
        name="Hidden"
        showLabel={false}
      />
    )
    expect(screen.queryByText('Hidden')).not.toBeInTheDocument()
  })

  it('renders all avatar shapes', () => {
    const shapes = ['square', 'circle', 'triangle', 'diamond', 'star', 'pentagon'] as const
    
    shapes.forEach(shape => {
      render(
        <CharacterAvatar
          shape={shape}
          color="#FF6B6B"
          name={shape}
        />
      )
      expect(screen.getByRole('img', { name: new RegExp(shape) })).toBeInTheDocument()
    })
  })

  it('renders different sizes', () => {
    const { rerender } = render(
      <CharacterAvatar
        shape="circle"
        color="#FF6B6B"
        name="Avatar"
        size="sm"
      />
    )
    let avatar = screen.getByRole('img')
    expect(avatar).toBeInTheDocument()

    rerender(
      <CharacterAvatar
        shape="circle"
        color="#FF6B6B"
        name="Avatar"
        size="lg"
      />
    )
    avatar = screen.getByRole('img')
    expect(avatar).toBeInTheDocument()
  })
})
