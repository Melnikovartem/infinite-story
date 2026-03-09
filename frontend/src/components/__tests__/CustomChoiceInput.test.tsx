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

    expect(screen.getByPlaceholderText(/Write your own choice/)).toBeInTheDocument()
    expect(screen.getByText('Submit Choice')).toBeInTheDocument()
  })

  it('disables submit button when text is empty', () => {
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const button = screen.getByText('Submit Choice')
    expect(button).toBeDisabled()
  })

  it('enables submit button when text is entered', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Write your own choice/)
    const button = screen.getByText('Submit Choice')

    await user.type(textarea, 'This is a long enough text to submit')
    expect(button).not.toBeDisabled()
  })

  it('calls onSubmit with text', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Write your own choice/)
    const button = screen.getByText('Submit Choice')

    await user.type(textarea, 'Test choice text')
    await user.click(button)

    expect(onSubmit).toHaveBeenCalled()
  })

  it('disables input when loading', () => {
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={true} />
    )

    const textarea = screen.getByPlaceholderText(/Write your own choice/)
    expect(textarea).toBeDisabled()
  })

  it('displays character count', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <CustomChoiceInput onSubmit={onSubmit} loading={false} />
    )

    const textarea = screen.getByPlaceholderText(/Write your own choice/)
    await user.type(textarea, 'test')

    expect(screen.getByText(/4/)).toBeInTheDocument()
  })
})
