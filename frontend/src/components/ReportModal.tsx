import React, { useState } from 'react'
import { Modal } from './Modal'
import { Textarea } from './Input'
import { Button } from './Button'
import { Alert } from './Alert'

export type ReportReason = 
  | 'offensive' 
  | 'inappropriate' 
  | 'spam' 
  | 'error' 
  | 'other'

interface ReportModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (reason: ReportReason, description: string) => Promise<void>
  segmentId?: string
}

const reportReasons: { value: ReportReason; label: string; description: string }[] = [
  {
    value: 'offensive',
    label: 'Offensive Content',
    description: 'Contains hateful, discriminatory, or offensive language',
  },
  {
    value: 'inappropriate',
    label: 'Inappropriate Content',
    description: 'Contains sexually explicit or otherwise inappropriate material',
  },
  {
    value: 'spam',
    label: 'Spam',
    description: 'Low-quality or repetitive content',
  },
  {
    value: 'error',
    label: 'Story Error',
    description: 'Contains plot holes, inconsistencies, or technical errors',
  },
  {
    value: 'other',
    label: 'Other',
    description: 'Something else',
  },
]

export const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  segmentId,
}) => {
  const [selectedReason, setSelectedReason] = useState<ReportReason | ''>('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!selectedReason) {
      setError('Please select a reason')
      return
    }

    if (!description.trim()) {
      setError('Please provide a description')
      return
    }

    try {
      setLoading(true)
      setError('')
      await onSubmit(selectedReason as ReportReason, description)
      setSuccess(true)

      setTimeout(() => {
        setSelectedReason('')
        setDescription('')
        setSuccess(false)
        onClose()
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Report Inappropriate Content"
      size="md"
    >
      <div className="space-y-lg" role="form" aria-labelledby="modal-title">
        {success && (
          <Alert
            variant="success"
            title="Report Submitted"
            dismissible
            onClose={() => setSuccess(false)}
          >
            Thank you for helping us improve! We'll review your report shortly.
          </Alert>
        )}

        {error && (
          <Alert
            variant="error"
            title="Error"
            dismissible
            onClose={() => setError('')}
          >
            {error}
          </Alert>
        )}

        <div className="space-y-md">
          <fieldset className="space-y-md">
            <legend className="text-sm font-semibold text-neutral-900">
              What's the issue?
            </legend>

            <div className="space-y-sm">
              {reportReasons.map((reason) => (
                <label
                  key={reason.value}
                  className="flex items-start gap-md p-md border border-neutral-200 rounded-lg hover:border-primary cursor-pointer transition-colors"
                >
                  <input
                    type="radio"
                    name="report-reason"
                    value={reason.value}
                    checked={selectedReason === reason.value}
                    onChange={(e) => setSelectedReason(e.target.value as ReportReason)}
                    disabled={loading}
                    className="mt-sm"
                    aria-describedby={`reason-${reason.value}`}
                  />
                  <div className="flex-1">
                    <p className="font-medium text-neutral-900">
                      {reason.label}
                    </p>
                    <p id={`reason-${reason.value}`} className="text-xs text-neutral-600">
                      {reason.description}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </fieldset>

          <Textarea
            label="Additional details"
            placeholder="Please provide more information about the issue..."
            value={description}
            onChange={(e) => {
              setDescription(e.target.value)
              setError('')
            }}
            maxLength={500}
            showCharCount
            disabled={loading}
          />
        </div>

        <div className="flex gap-md justify-end pt-md border-t border-neutral-200">
          <Button
            onClick={onClose}
            variant="ghost"
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="primary"
            isLoading={loading}
            disabled={!selectedReason || !description.trim()}
          >
            Submit Report
          </Button>
        </div>
      </div>
    </Modal>
  )
}
