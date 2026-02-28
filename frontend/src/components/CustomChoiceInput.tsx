import React, { useState } from 'react'
import { Textarea } from './Input'
import { Button } from './Button'
import { Card } from './Card'

interface CustomChoiceInputProps {
  onSubmit: (text: string) => void
  loading?: boolean
  placeholder?: string
  maxLength?: number
}

export const CustomChoiceInput: React.FC<CustomChoiceInputProps> = ({
  onSubmit,
  loading = false,
  placeholder = 'Write your own choice...',
  maxLength = 500,
}) => {
  const [value, setValue] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = () => {
    if (!value.trim()) {
      setError('Please enter a choice')
      return
    }

    if (value.length < 5) {
      setError('Choice must be at least 5 characters')
      return
    }

    setError('')
    onSubmit(value)
    setValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleSubmit()
    }
  }

  return (
    <Card className="space-y-md">
      <h3 className="text-lg font-semibold text-neutral-900">
        Write your own choice
      </h3>

      <Textarea
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          setError('')
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        maxLength={maxLength}
        showCharCount
        error={error}
        helperText="Press Ctrl+Enter to submit"
        disabled={loading}
      />

      <div className="flex gap-md">
        <Button
          onClick={handleSubmit}
          disabled={loading || !value.trim()}
          isLoading={loading}
          variant="secondary"
        >
          Submit Choice
        </Button>
        <Button
          onClick={() => {
            setValue('')
            setError('')
          }}
          variant="ghost"
          disabled={loading}
        >
          Clear
        </Button>
      </div>
    </Card>
  )
}
