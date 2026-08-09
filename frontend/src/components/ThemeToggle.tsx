import { observer } from 'mobx-react-lite'
import { Moon, Sun } from 'lucide-react'
import { themeStore } from '../stores/ThemeStore'

export const ThemeToggle = observer(function ThemeToggle() {
  const isDark = themeStore.theme === 'dark'

  return (
    <button
      type="button"
      onClick={() => themeStore.toggle()}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className="inline-flex items-center justify-center rounded-full border border-border bg-surface p-2 text-foreground transition-colors hover:bg-muted"
    >
      {isDark ? <Sun className="h-5 w-5" aria-hidden="true" /> : <Moon className="h-5 w-5" aria-hidden="true" />}
    </button>
  )
})
