import { makeAutoObservable, runInAction } from 'mobx'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'budget-checker-theme'

function readStoredTheme(): Theme | null {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : null
  } catch {
    return null
  }
}

function readSystemTheme(): Theme | null {
  if (typeof window.matchMedia !== 'function') {
    return null
  }
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return null
}

function resolveInitialTheme(): Theme {
  return readStoredTheme() ?? readSystemTheme() ?? 'light'
}

function persistTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Best-effort: DS-11 requires the toggle to keep switching the theme
    // even when localStorage is unavailable (e.g. private browsing).
  }
}

function applyThemeClass(theme: Theme): void {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

export class ThemeStore {
  theme: Theme

  constructor() {
    makeAutoObservable(this)
    this.theme = resolveInitialTheme()
    applyThemeClass(this.theme)
  }

  toggle(): void {
    const next: Theme = this.theme === 'light' ? 'dark' : 'light'
    runInAction(() => {
      this.theme = next
    })
    applyThemeClass(next)
    persistTheme(next)
  }
}

export const themeStore = new ThemeStore()
