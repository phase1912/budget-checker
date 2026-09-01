export function Footer() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto w-full px-4 sm:px-6 sm:max-w-2xl md:max-w-4xl lg:max-w-6xl xl:max-w-7xl py-6 text-sm text-muted-foreground">
        © {new Date().getFullYear()} Budget Checker
      </div>
    </footer>
  )
}
