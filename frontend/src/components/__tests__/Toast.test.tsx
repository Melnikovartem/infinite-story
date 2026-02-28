import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Toast, useToast } from '../Toast'

describe('Toast', () => {
  it('renders with message', () => {
    render(
      <Toast
        id="test"
        message="Test message"
        onClose={() => {}}
      />
    )
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('displays different types', () => {
    const types = ['success', 'error', 'warning', 'info'] as const

    types.forEach(type => {
      const { unmount } = render(
        <Toast
          id={type}
          message={`${type} message`}
          type={type}
          onClose={() => {}}
        />
      )
      expect(screen.getByText(`${type} message`)).toBeInTheDocument()
      unmount()
    })
  })

  it('closes when close button is clicked', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()

    render(
      <Toast
        id="test"
        message="Test message"
        onClose={onClose}
        duration={0}
      />
    )

    const closeButton = screen.getByLabelText('Close notification')
    await user.click(closeButton)

    expect(onClose).toHaveBeenCalledWith('test')
  })

  it('auto-closes after duration', async () => {
    const onClose = vi.fn()

    render(
      <Toast
        id="test"
        message="Test message"
        onClose={onClose}
        duration={100}
      />
    )

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledWith('test')
    }, { timeout: 500 })
  })

  it('renders action button when provided', async () => {
    const action = vi.fn()
    const user = userEvent.setup()

    render(
      <Toast
        id="test"
        message="Test message"
        onClose={() => {}}
        duration={0}
        action={{ label: 'Undo', onClick: action }}
      />
    )

    await user.click(screen.getByText('Undo'))
    expect(action).toHaveBeenCalled()
  })

  it('has proper accessibility attributes', () => {
    render(
      <Toast
        id="test"
        message="Test message"
        onClose={() => {}}
        duration={0}
      />
    )

    const toast = screen.getByRole('status')
    expect(toast).toHaveAttribute('aria-live', 'polite')
    expect(toast).toHaveAttribute('aria-atomic', 'true')
  })
})

describe('ToastContainer', () => {
  it('renders multiple toasts', () => {
    const toasts = [
      { id: '1', message: 'Toast 1', type: 'success' as const, onClose: () => {} },
      { id: '2', message: 'Toast 2', type: 'error' as const, onClose: () => {} },
    ]

    const { container } = render(
      <>
        {toasts.map(toast => (
          <Toast key={toast.id} {...toast} duration={0} />
        ))}
      </>
    )

    expect(screen.getByText('Toast 1')).toBeInTheDocument()
    expect(screen.getByText('Toast 2')).toBeInTheDocument()
  })
})
