/**
 * Accessibility utilities for WCAG 2.1 AA compliance
 */

/**
 * Generate unique ID for aria-labelledby and aria-describedby
 */
export const generateId = (prefix: string): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Skip to main content shortcut for keyboard navigation
 */
export const createSkipToMainLink = (): void => {
  const skipLink = document.createElement('a')
  skipLink.href = '#main'
  skipLink.textContent = 'Skip to main content'
  skipLink.className = `
    absolute
    top-0
    left-0
    -translate-y-full
    focus:translate-y-0
    bg-primary
    text-white
    px-md
    py-sm
    z-50
    transition-transform
  `
  document.body.prepend(skipLink)
}

/**
 * Check color contrast ratio (WCAG AA: 4.5:1 for normal text, 3:1 for large text)
 * Returns luminance value for contrast calculation
 */
export const getLuminance = (color: string): number => {
  const rgb = parseInt(color.replace('#', ''), 16)
  const r = (rgb >> 16) & 0xff
  const g = (rgb >> 8) & 0xff
  const b = (rgb >> 0) & 0xff

  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

  return luminance <= 0.03928
    ? luminance / 12.92
    : Math.pow((luminance + 0.055) / 1.055, 2.4)
}

/**
 * Calculate contrast ratio between two colors
 * Formula: (L1 + 0.05) / (L2 + 0.05) where L1 is lighter
 */
export const getContrastRatio = (color1: string, color2: string): number => {
  const l1 = getLuminance(color1)
  const l2 = getLuminance(color2)

  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)

  return (lighter + 0.05) / (darker + 0.05)
}

/**
 * Check if contrast is sufficient for WCAG AA
 * normalText: 4.5:1, largeText: 3:1
 */
export const isContrastSufficient = (
  color1: string,
  color2: string,
  isLargeText: boolean = false
): boolean => {
  const ratio = getContrastRatio(color1, color2)
  return isLargeText ? ratio >= 3 : ratio >= 4.5
}

/**
 * Keyboard event helpers
 */
export const isEnterKey = (e: React.KeyboardEvent): boolean => {
  return e.key === 'Enter' || e.code === 'Enter'
}

export const isEscapeKey = (e: React.KeyboardEvent): boolean => {
  return e.key === 'Escape' || e.code === 'Escape'
}

export const isArrowUp = (e: React.KeyboardEvent): boolean => {
  return e.key === 'ArrowUp' || e.code === 'ArrowUp'
}

export const isArrowDown = (e: React.KeyboardEvent): boolean => {
  return e.key === 'ArrowDown' || e.code === 'ArrowDown'
}

export const isArrowLeft = (e: React.KeyboardEvent): boolean => {
  return e.key === 'ArrowLeft' || e.code === 'ArrowLeft'
}

export const isArrowRight = (e: React.KeyboardEvent): boolean => {
  return e.key === 'ArrowRight' || e.code === 'ArrowRight'
}

export const isSpace = (e: React.KeyboardEvent): boolean => {
  return e.key === ' ' || e.code === 'Space'
}

/**
 * Announce to screen readers
 */
export const announce = (
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
): void => {
  const announcement = document.createElement('div')
  announcement.setAttribute('role', 'status')
  announcement.setAttribute('aria-live', priority)
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message

  document.body.appendChild(announcement)

  // Remove after announcement
  setTimeout(() => {
    announcement.remove()
  }, 1000)
}

/**
 * Screen reader only content class
 * CSS: .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
 */
export const srOnly = 'sr-only'
