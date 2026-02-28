import React from 'react'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  interactive?: boolean
  children: React.ReactNode
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ interactive = false, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`
          ${interactive ? 'card-interactive' : 'card'}
          ${className}
        `.trim()}
        {...props}
      />
    )
  }
)

Card.displayName = 'Card'

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`border-b border-neutral-200 pb-md mb-lg ${className}`.trim()}
      {...props}
    />
  )
)

CardHeader.displayName = 'CardHeader'

interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode
}

export const CardTitle = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className = '', ...props }, ref) => (
    <h3
      ref={ref}
      className={`text-2xl font-bold text-neutral-900 ${className}`.trim()}
      {...props}
    />
  )
)

CardTitle.displayName = 'CardTitle'

interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const CardBody = React.forwardRef<HTMLDivElement, CardBodyProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`space-y-md ${className}`.trim()}
      {...props}
    />
  )
)

CardBody.displayName = 'CardBody'

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`border-t border-neutral-200 pt-md mt-lg flex gap-md ${className}`.trim()}
      {...props}
    />
  )
)

CardFooter.displayName = 'CardFooter'
