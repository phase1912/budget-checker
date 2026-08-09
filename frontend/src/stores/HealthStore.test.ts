import { beforeEach, describe, expect, it, vi } from 'vitest'
import { HealthStore } from './HealthStore'

vi.mock('../api/client', () => ({
  fetchHealth: vi.fn(),
}))

import { fetchHealth } from '../api/client'

describe('HealthStore', () => {
  beforeEach(() => {
    vi.mocked(fetchHealth).mockReset()
  })

  it('requests the backend health-check endpoint and reports it as available', async () => {
    vi.mocked(fetchHealth).mockResolvedValue({ status: 'ok' })
    const store = new HealthStore()

    expect(store.status).toBe('unknown')
    await store.check()

    expect(fetchHealth).toHaveBeenCalledTimes(1)
    expect(store.status).toBe('available')
  })

  it('reports the backend as unreachable when the health check fails', async () => {
    vi.mocked(fetchHealth).mockRejectedValue(new Error('network error'))
    const store = new HealthStore()

    await store.check()

    expect(store.status).toBe('unreachable')
  })
})
