import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Landing } from './Landing'

describe('Landing', () => {
  it('shows the product description to an anonymous visitor', () => {
    render(<Landing backendStatus="unknown" />)
    expect(screen.getByRole('heading', { name: 'Budget Checker' })).toBeInTheDocument()
    expect(screen.getByText(/track how close you are/i)).toBeInTheDocument()
  })

  it('is never gated behind a login, regardless of backend status', () => {
    render(<Landing backendStatus="unreachable" />)
    expect(screen.getByText(/track how close you are/i)).toBeInTheDocument()
    expect(screen.queryByText(/sign in/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })
})
