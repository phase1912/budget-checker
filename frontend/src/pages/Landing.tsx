import type { BackendStatus } from '../stores/HealthStore'

type LandingProps = {
  backendStatus: BackendStatus
}

export function Landing({ backendStatus }: LandingProps) {
  return (
    <div className="mx-auto w-full px-4 sm:px-6 sm:max-w-2xl md:max-w-4xl lg:max-w-6xl xl:max-w-7xl py-16">
      <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
        Budget Checker
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
        Set a monthly and a yearly financial goal, and track how close you are
        to reaching them — without manually re-entering every expense.
      </p>
      {backendStatus === 'available' && (
        <p className="mt-6 inline-flex items-center rounded-full bg-success px-3 py-1 text-sm font-medium text-success-foreground">
          Backend: available
        </p>
      )}
    </div>
  )
}
