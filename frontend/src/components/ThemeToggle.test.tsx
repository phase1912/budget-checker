import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { ThemeToggle } from './ThemeToggle'
import { themeStore } from '../stores/ThemeStore'

describe('ThemeToggle', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark')
  })

  afterEach(() => {
    if (themeStore.theme === 'dark') {
      themeStore.toggle()
    }
  })

  it('switches the active theme when activated', () => {
    render(<ThemeToggle />)

    expect(themeStore.theme).toBe('light')

    fireEvent.click(screen.getByRole('button', { name: /switch to dark theme/i }))

    expect(themeStore.theme).toBe('dark')
    expect(screen.getByRole('button', { name: /switch to light theme/i })).toBeInTheDocument()
  })
})
