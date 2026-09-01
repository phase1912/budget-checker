export function Footer() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 py-6 text-sm text-muted-foreground">
        © {new Date().getFullYear()} Budget Checker
      </div>
    </footer>
  )
}
