import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CustomChoiceInput } from '../CustomChoiceInput'

describe('CustomChoiceInput', () => {
  it('renders textarea and submit button', () => {
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    expect(screen.getByPlaceholderText(/Describe what you do or say/)).toBeInTheDocument()
    expect(screen.getByText('Submit Custom Choice')).toBeInTheDocument()
  })

  it('disables submit button when text is too short', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Describe what you do or say/)
    const button = screen.getByText('Submit Custom Choice')

    expect(button).toBeDisabled()

    await user.type(textarea, 'short')
    expect(button).toBeDisabled()
  })

  it('enables submit button when text meets minimum length', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Describe what you do or say/)
    const button = screen.getByText('Submit Custom Choice')

    await user.type(textarea, 'This is a long enough text to submit')
    expect(button).not.toBeDisabled()
  })

  it('calls onSubmit with trimmed text', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Describe what you do or say/)
    const button = screen.getByText('Submit Custom Choice')

    await user.type(textarea, '  Test choice text  ')
    await user.click(button)

    expect(onSubmit).toHaveBeenCalledWith('Test choice text')
  })

  it('disables input when loading', () => {
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={true} />
    )

    const textarea = screen.getByPlaceholderText(/Describe what you do or say/)
    const button = screen.getByText('Generating...')

    expect(textarea).toBeDisabled()
    expect(button).toBeDisabled()
  })

  it('limits character input to 200 characters', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Describe what you do or say/)
    const longText = 'a'.repeat(250)

    await user.type(textarea, longText)

    expect(textarea).toHaveValue('a'.repeat(200))
  })

  it('displays character count', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Describe what you do or say/)
    await user.type(textarea, 'test')

    expect(screen.getByText('4/200')).toBeInTheDocument()
  })
})
