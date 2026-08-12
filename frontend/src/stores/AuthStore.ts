import { makeAutoObservable, runInAction } from 'mobx'

export interface User {
  id: string
  email: string
  first_name?: string
  last_name?: string
  role: string
  is_active: boolean
  created_at: string
}

export interface RegisterPayload {
  email: string
  password: string
  first_name?: string
  last_name?: string
}

export interface LoginPayload {
  email: string
  password: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

class AuthStore {
  user: User | null = null
  accessToken: string | null = null
  refreshToken: string | null = null
  isLoading = false
  error: string | null = null
  isAuthModalOpen = false
  authModalTab: 'login' | 'register' = 'login'

  constructor() {
    makeAutoObservable(this)
    this.loadTokensFromStorage()
  }

  get isAuthenticated(): boolean {
    return !!this.accessToken && !!this.user
  }

  get userDisplayName(): string {
    if (!this.user) return ''
    if (this.user.first_name || this.user.last_name) {
      return `${this.user.first_name || ''} ${this.user.last_name || ''}`.trim()
    }
    return this.user.email
  }

  openAuthModal = (tab: 'login' | 'register' = 'login') => {
    this.authModalTab = tab
    this.isAuthModalOpen = true
    this.error = null
  }

  closeAuthModal = () => {
    this.isAuthModalOpen = false
    this.error = null
  }

  setAuthModalTab = (tab: 'login' | 'register') => {
    this.authModalTab = tab
    this.error = null
  }

  loadTokensFromStorage() {
    const access = localStorage.getItem('access_token')
    const refresh = localStorage.getItem('refresh_token')
    const savedUser = localStorage.getItem('user_data')

    if (access && refresh && savedUser) {
      try {
        this.accessToken = access
        this.refreshToken = refresh
        this.user = JSON.parse(savedUser)
      } catch {
        this.clearStorage()
      }
    }
  }

  saveTokensToStorage(access: string, refresh: string, user: User) {
    this.accessToken = access
    this.refreshToken = refresh
    this.user = user

    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('user_data', JSON.stringify(user))
  }

  clearStorage() {
    this.accessToken = null
    this.refreshToken = null
    this.user = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_data')
  }

  async login(payload: LoginPayload) {
    this.isLoading = true
    this.error = null
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || data.error || 'Failed to sign in')
      }

      const data = await response.json()
      runInAction(() => {
        this.saveTokensToStorage(data.access_token, data.refresh_token, data.user)
        this.closeAuthModal()
      })
    } catch (err: any) {
      runInAction(() => {
        this.error = err.message || 'An unexpected error occurred'
      })
      throw err
    } finally {
      runInAction(() => {
        this.isLoading = false
      })
    }
  }

  async register(payload: RegisterPayload) {
    this.isLoading = true
    this.error = null
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || data.error || 'Failed to create account')
      }

      const data = await response.json()
      runInAction(() => {
        this.saveTokensToStorage(data.access_token, data.refresh_token, data.user)
        this.closeAuthModal()
      })
    } catch (err: any) {
      runInAction(() => {
        this.error = err.message || 'An unexpected error occurred'
      })
      throw err
    } finally {
      runInAction(() => {
        this.isLoading = false
      })
    }
  }

  async logout() {
    if (this.refreshToken) {
      try {
        await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        })
      } catch {
        // Ignore logout errors
      }
    }
    runInAction(() => {
      this.clearStorage()
    })
  }
}

export const authStore = new AuthStore()
