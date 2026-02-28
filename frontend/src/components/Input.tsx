import React from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className = '', ...props }, ref) => {
    const id = props.id || `input-${Math.random().toString(36).substr(2, 9)}`
    
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="label">
            {label}
            {props.required && <span className="text-error ml-xs">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={`
            input
            ${error ? 'border-error focus-visible:border-error' : ''}
            ${className}
          `.trim()}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
          {...props}
        />
        {error && (
          <p id={`${id}-error`} className="mt-sm text-sm text-error">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${id}-helper`} className="mt-sm text-sm text-neutral-600">
            {helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  maxLength?: number
  showCharCount?: boolean
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ 
    label, 
    error, 
    helperText, 
    maxLength, 
    showCharCount = false,
    value = '',
    className = '',
    ...props 
  }, ref) => {
    const id = props.id || `textarea-${Math.random().toString(36).substr(2, 9)}`
    const charCount = typeof value === 'string' ? value.length : 0
    
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="label">
            {label}
            {props.required && <span className="text-error ml-xs">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={id}
          maxLength={maxLength}
          value={value}
          className={`
            input
            resize-none
            min-h-24
            ${error ? 'border-error focus-visible:border-error' : ''}
            ${className}
          `.trim()}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
          {...props}
        />
        <div className="flex justify-between items-center mt-sm gap-md">
          <div>
            {error && (
              <p id={`${id}-error`} className="text-sm text-error">
                {error}
              </p>
            )}
            {helperText && !error && (
              <p id={`${id}-helper`} className="text-sm text-neutral-600">
                {helperText}
              </p>
            )}
          </div>
          {showCharCount && maxLength && (
            <span className="text-xs text-neutral-600">
              {charCount}/{maxLength}
            </span>
          )}
        </div>
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'
