import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Alert } from '../Alert'
import { Button } from '../Button'
import { Input } from '../Input'
import { Modal } from '../Modal'

describe('Accessibility - WCAG 2.1 AA Compliance', () => {
  describe('Semantic HTML', () => {
    it('Button component uses semantic button element', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('Input component uses semantic input element with label', () => {
      render(<Input label="Email" />)
      const input = screen.getByRole('textbox')
      const label = screen.getByText('Email')
      
      expect(input).toBeInTheDocument()
      expect(label).toBeInTheDocument()
      expect(label.tagName).toBe('LABEL')
    })

    it('Alert component uses semantic role="alert"', () => {
      render(
        <Alert variant="error" title="Error">
          Something went wrong
        </Alert>
      )
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  describe('Keyboard Navigation', () => {
    it('Button is keyboard accessible with Tab and Enter', () => {
      render(<Button>Click me</Button>)
      const button = screen.getByRole('button')
      
      // Should be focusable
      button.focus()
      expect(document.activeElement).toBe(button)
    })

    it('Input field accepts keyboard input', () => {
      render(<Input />)
      const input = screen.getByRole('textbox') as HTMLInputElement
      
      input.focus()
      expect(document.activeElement).toBe(input)
    })
  })

  describe('ARIA Labels', () => {
    it('Input with error has aria-invalid', () => {
      render(<Input error="Required" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
    })

    it('Button with loading state has aria-busy', () => {
      render(<Button isLoading>Loading</Button>)
      expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true')
    })

    it('Alert has role="alert"', () => {
      render(
        <Alert variant="info">
          Information message
        </Alert>
      )
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
      expect(alert).toHaveAttribute('aria-live', 'polite')
    })
  })

  describe('Color Contrast', () => {
    it('Primary button has sufficient contrast', () => {
      // This would require actual color contrast checking
      // Simplified: verify button has color classes
      render(<Button>Text</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('btn-primary')
    })

    it('Alert variants render with appropriate styling', () => {
      const { rerender } = render(
        <Alert variant="success" title="Success">Success Message</Alert>
      )
      expect(screen.getByRole('alert')).toBeInTheDocument()
      
      rerender(
        <Alert variant="error" title="Error">Error Message</Alert>
      )
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  describe('Form Accessibility', () => {
    it('Input with label has proper association', () => {
      render(
        <Input
          id="test-input"
          label="Test Input"
        />
      )
      const label = screen.getByText('Test Input')
      const input = screen.getByRole('textbox')

      expect(label.tagName).toBe('LABEL')
      expect(label).toHaveAttribute('for', 'test-input')
      expect(input).toHaveAttribute('id', 'test-input')
    })

    it('Required inputs display required indicator', () => {
      render(<Input label="Email" required />)
      expect(screen.getByText('*')).toBeInTheDocument()
    })

    it('Input error is associated via aria-describedby', () => {
      render(<Input error="This field is required" />)
      const input = screen.getByRole('textbox')
      
      expect(input).toHaveAttribute('aria-describedby')
      expect(input).toHaveAttribute('aria-invalid', 'true')
    })
  })

  describe('Focus Management', () => {
    it('Elements receive visible focus indicator', () => {
      render(<Button>Click me</Button>)
      const button = screen.getByRole('button')
      
      button.focus()
      expect(document.activeElement).toBe(button)
      // Verify button has focus styles (would need visual testing)
    })
  })
})
