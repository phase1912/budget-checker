import type { BackendStatus } from '../stores/HealthStore'

type LandingProps = {
  backendStatus: BackendStatus
}

export function Landing({ backendStatus }: LandingProps) {
  return (
    <main>
      <h1>Budget Checker</h1>
      <p>
        Set a monthly and a yearly financial goal, and track how close you are
        to reaching them — without manually re-entering every expense.
      </p>
      {backendStatus === 'available' && <p className="status">Backend: available</p>}
    </main>
  )
}
