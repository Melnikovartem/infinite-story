import { useState } from 'react'
import './CustomChoiceInput.css'

interface CustomChoiceInputProps {
  onSubmit: (text: string) => void
  loading?: boolean
}

export default function CustomChoiceInput({ onSubmit, loading }: CustomChoiceInputProps) {
  const [text, setText] = useState('')
  const [charCount, setCharCount] = useState(0)

  const minLength = 10
  const maxLength = 200

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value
    if (newText.length <= maxLength) {
      setText(newText)
      setCharCount(newText.length)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (text.trim().length >= minLength) {
      onSubmit(text.trim())
      setText('')
      setCharCount(0)
    }
  }

  const isValid = text.trim().length >= minLength
  const isEmpty = text.length === 0

  return (
    <form className="custom-choice-input" onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={handleChange}
        placeholder="Describe what you do or say..."
        rows={3}
        disabled={loading}
        className="choice-textarea"
      />

      <div className="input-footer">
        <div className="char-count">
          {charCount}/{maxLength}
        </div>
        <button
          type="submit"
          disabled={!isValid || loading}
          className="submit-button"
        >
          {loading ? (
            <>
              <span className="spinner-mini"></span>
              Generating...
            </>
          ) : (
            'Submit Custom Choice'
          )}
        </button>
      </div>

      {!isEmpty && !isValid && (
        <p className="help-text">
          Minimum {minLength} characters required
        </p>
      )}
    </form>
  )
}
