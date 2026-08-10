import { Link } from 'react-router-dom'

export function NotFound() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col items-center gap-4 px-6 py-24 text-center">
      <h1 className="text-2xl font-semibold text-foreground">Page not found</h1>
      <p className="text-muted-foreground">The page you're looking for doesn't exist.</p>
      <Link
        to="/"
        className="text-primary underline underline-offset-4 hover:text-primary-hover"
      >
        Back to the homepage
      </Link>
    </div>
  )
}
