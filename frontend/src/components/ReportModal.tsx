import { useState } from 'react'
import './ReportModal.css'

interface ReportModalProps {
  isOpen: boolean
  onClose: () => void
  _storyId: string
  _segmentId: string
  onSubmit: (email: string, description: string) => Promise<void>
}

export default function ReportModal({
  isOpen,
  onClose,
  onSubmit
}: ReportModalProps) {
  const [email, setEmail] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !description) return

    setLoading(true)
    setError(null)
    try {
      await onSubmit(email, description)
      setSubmitted(true)
      setTimeout(() => {
        onClose()
        setEmail('')
        setDescription('')
        setSubmitted(false)
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit report')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        {submitted ? (
          <div className="modal-success">
            <div className="success-icon">✓</div>
            <h3>Report Submitted</h3>
            <p>Thank you for helping us maintain a safe community.</p>
          </div>
        ) : (
          <>
            <h2>Report Inappropriate Content</h2>
            <p className="modal-subtitle">
              Help us keep the story safe for everyone
            </p>

            {error && (
              <div className="modal-error">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="email">Your Email</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  disabled={loading}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">What's wrong?</label>
                <textarea
                  id="description"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Please describe what you found inappropriate..."
                  rows={5}
                  disabled={loading}
                  required
                />
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className="button secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !email || !description}
                  className="button primary"
                >
                  {loading ? 'Submitting...' : 'Submit Report'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
