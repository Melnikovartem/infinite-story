import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReportModal } from '../ReportModal'

describe('ReportModal', () => {
  it('does not render when closed', () => {
    const onSubmit = vi.fn()
    const { container } =     render(
      <ReportModal
        isOpen={false}
        onClose={vi.fn()}
        _storyId="test"
        _segmentId="seg_1"
        onSubmit={onSubmit}
      />
    )
    expect(container.querySelector('.modal-overlay')).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        _storyId="test"
        _segmentId="seg_1"
        onSubmit={onSubmit}
      />
    )
    expect(screen.getByText('Report Inappropriate Content')).toBeInTheDocument()
  })

  it('has email and description fields', () => {
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        _storyId="test"
        _segmentId="seg_1"
        onSubmit={onSubmit}
      />
    )
    expect(screen.getByPlaceholderText(/your@email.com/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/describe what you found/)).toBeInTheDocument()
  })

  it('disables submit button until form is filled', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        _storyId="test"
        _segmentId="seg_1"
        onSubmit={onSubmit}
      />
    )

    const submitButton = screen.getByText('Submit Report')
    expect(submitButton).toBeDisabled()

    const emailInput = screen.getByPlaceholderText(/your@email.com/)
    await user.type(emailInput, 'test@example.com')
    expect(submitButton).toBeDisabled()

    const descriptionInput = screen.getByPlaceholderText(/describe what you found/)
    await user.type(descriptionInput, 'This content is inappropriate')
    expect(submitButton).not.toBeDisabled()
  })

  it('calls onSubmit with form data', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        _storyId="test"
        _segmentId="seg_1"
        onSubmit={onSubmit}
      />
    )

    await user.type(screen.getByPlaceholderText(/your@email.com/), 'test@example.com')
    await user.type(screen.getByPlaceholderText(/describe what you found/), 'Bad content')
    await user.click(screen.getByText('Submit Report'))

    expect(onSubmit).toHaveBeenCalledWith('test@example.com', 'Bad content')
  })

  it('closes modal on cancel button', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    const onSubmit = vi.fn()
    render(
      <ReportModal
        isOpen={true}
        onClose={onClose}
        _storyId="test"
        _segmentId="seg_1"
        onSubmit={onSubmit}
      />
    )

    await user.click(screen.getByText('Cancel'))
    expect(onClose).toHaveBeenCalled()
  })

  it('closes modal on X button', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    const onSubmit = vi.fn()
    const { container } = render(
      <ReportModal
        isOpen={true}
        onClose={onClose}
        _storyId="test"
        _segmentId="seg_1"
        onSubmit={onSubmit}
      />
    )

    const closeButton = container.querySelector('.modal-close')
    if (closeButton) {
      await user.click(closeButton)
    }
    expect(onClose).toHaveBeenCalled()
  })
})
