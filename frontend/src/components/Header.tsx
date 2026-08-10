import { ThemeToggle } from './ThemeToggle'

export function Header() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
        <span className="text-lg font-semibold text-foreground">Budget Checker</span>
        <ThemeToggle />
      </div>
    </header>
  )
}
