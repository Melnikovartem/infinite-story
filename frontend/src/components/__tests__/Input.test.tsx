import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input, Textarea } from '../Input'

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Username" />)
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
  })

  it('shows required indicator when required', () => {
    render(<Input label="Email" required />)
    expect(screen.getByText('*')).toBeInTheDocument()
  })

  it('displays error message', () => {
    render(
      <Input
        label="Password"
        error="Password is required"
      />
    )
    expect(screen.getByText('Password is required')).toBeInTheDocument()
  })

  it('displays helper text', () => {
    render(
      <Input
        label="Username"
        helperText="Must be 3-20 characters"
      />
    )
    expect(screen.getByText('Must be 3-20 characters')).toBeInTheDocument()
  })

  it('accepts input value', async () => {
    const user = userEvent.setup()
    render(<Input />)
    const input = screen.getByRole('textbox')

    await user.type(input, 'test')
    expect(input).toHaveValue('test')
  })

  it('is disabled when disabled prop is set', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('has aria-invalid when error exists', () => {
    render(<Input error="Invalid input" />)
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
  })
})

describe('Textarea', () => {
  it('renders with label', () => {
    render(<Textarea label="Message" />)
    expect(screen.getByLabelText('Message')).toBeInTheDocument()
  })

  it('displays character count when enabled', () => {
    render(
      <Textarea
        value="hello"
        maxLength={100}
        showCharCount
        onChange={() => {}}
      />
    )
    expect(screen.getByText('5/100')).toBeInTheDocument()
  })

  it('shows error message', () => {
    render(
      <Textarea
        error="Message is too short"
      />
    )
    expect(screen.getByText('Message is too short')).toBeInTheDocument()
  })

  it('renders as textarea element', () => {
    render(<Textarea />)
    const textarea = screen.getByRole('textbox')
    expect(textarea.tagName).toBe('TEXTAREA')
  })
})
