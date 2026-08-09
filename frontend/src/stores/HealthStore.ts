import { makeAutoObservable, runInAction } from 'mobx'
import { fetchHealth } from '../api/client'

export type BackendStatus = 'unknown' | 'available' | 'unreachable'

export class HealthStore {
  status: BackendStatus = 'unknown'

  constructor() {
    makeAutoObservable(this)
  }

  async check(): Promise<void> {
    try {
      await fetchHealth()
      runInAction(() => {
        this.status = 'available'
      })
    } catch {
      runInAction(() => {
        this.status = 'unreachable'
      })
    }
  }
}

export const healthStore = new HealthStore()
