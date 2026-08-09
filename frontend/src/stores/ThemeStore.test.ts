import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ThemeStore } from './ThemeStore'

const STORAGE_KEY = 'budget-checker-theme'

function stubSystemPreference(preference: 'dark' | 'light' | 'none'): void {
  window.matchMedia = vi.fn((query: string) => ({
    matches: preference !== 'none' && query.includes(preference),
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
    onchange: null,
  })) as unknown as typeof window.matchMedia
}

describe('ThemeStore', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.classList.remove('dark')
    stubSystemPreference('none')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('applies the stored theme preference on load', () => {
    window.localStorage.setItem(STORAGE_KEY, 'dark')

    const store = new ThemeStore()

    expect(store.theme).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('falls back to the OS preference when no theme is stored', () => {
    stubSystemPreference('dark')

    const store = new ThemeStore()

    expect(store.theme).toBe('dark')
  })

  it('falls back to the OS preference when localStorage is unavailable', () => {
    vi.spyOn(window.localStorage, 'getItem').mockImplementation(() => {
      throw new Error('localStorage unavailable')
    })
    stubSystemPreference('light')

    const store = new ThemeStore()

    expect(store.theme).toBe('light')
  })

  it('defaults to light when neither a stored nor an OS preference is available', () => {
    stubSystemPreference('none')

    const store = new ThemeStore()

    expect(store.theme).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('switches the active theme when toggled', () => {
    const store = new ThemeStore()
    expect(store.theme).toBe('light')

    store.toggle()
    expect(store.theme).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    store.toggle()
    expect(store.theme).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('persists the new theme to localStorage when toggled', () => {
    const store = new ThemeStore()

    store.toggle()

    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })

  it('still switches the theme even if persisting the choice fails', () => {
    const store = new ThemeStore()
    vi.spyOn(window.localStorage, 'setItem').mockImplementation(() => {
      throw new Error('quota exceeded')
    })

    expect(() => store.toggle()).not.toThrow()
    expect(store.theme).toBe('dark')
  })
})
