import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReportModal } from '../ReportModal'

// Polyfill HTMLDialogElement methods for jsdom
beforeAll(() => {
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
    this.setAttribute('open', '')
  })
  HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) {
    this.removeAttribute('open')
  })
})

describe('ReportModal', () => {
  it('does not render content when closed', () => {
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={false}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />
    )
    expect(screen.queryByText('Report Inappropriate Content')).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />
    )
    expect(screen.getByText('Report Inappropriate Content')).toBeInTheDocument()
  })

  it('has reason options and description field', () => {
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />
    )
    expect(screen.getByText('Offensive Content')).toBeInTheDocument()
    expect(screen.getByText('Inappropriate Content')).toBeInTheDocument()
    expect(screen.getByText('Story Error')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/provide more information/i)).toBeInTheDocument()
  })

  it('disables submit button until form is filled', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />
    )

    const submitButton = screen.getByText('Submit Report')
    expect(submitButton).toBeDisabled()

    // Select a reason
    await user.click(screen.getByText('Offensive Content'))
    expect(submitButton).toBeDisabled()

    // Fill description
    const descriptionInput = screen.getByPlaceholderText(/provide more information/i)
    await user.type(descriptionInput, 'This content is inappropriate')
    expect(submitButton).not.toBeDisabled()
  })

  it('calls onSubmit with reason and description', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />
    )

    await user.click(screen.getByText('Offensive Content'))
    const descriptionInput = screen.getByPlaceholderText(/provide more information/i)
    await user.type(descriptionInput, 'Bad content')
    await user.click(screen.getByText('Submit Report'))

    expect(onSubmit).toHaveBeenCalledWith('offensive', 'Bad content')
  })

  it('closes modal on cancel button', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={onClose}
        onSubmit={onSubmit}
      />
    )

    await user.click(screen.getByText('Cancel'))
    expect(onClose).toHaveBeenCalled()
  })
})
