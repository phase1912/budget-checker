import { describe, it, expect, beforeEach, vi } from 'vitest'
import { authStore } from './AuthStore'

describe('AuthStore', () => {
  beforeEach(() => {
    localStorage.clear()
    authStore.clearStorage()
    authStore.closeAuthModal()
    vi.restoreAllMocks()
  })

  it('registers a user successfully and saves token data', async () => {
    const fakeTokenResponse = {
      access_token: 'fake-access',
      refresh_token: 'fake-refresh',
      token_type: 'bearer',
      user: {
        id: 'u-1',
        email: 'test@example.com',
        role: 'user',
        is_active: true,
        created_at: new Date().toISOString(),
      },
    }

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => fakeTokenResponse,
    } as Response)

    await authStore.register({ email: 'test@example.com', password: 'password123' })

    expect(authStore.isAuthenticated).toBe(true)
    expect(authStore.user?.email).toBe('test@example.com')
    expect(localStorage.getItem('access_token')).toBe('fake-access')
    expect(localStorage.getItem('refresh_token')).toBe('fake-refresh')
  })

  it('handles registration error response gracefully', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'User with this email already exists' }),
    } as Response)

    await expect(
      authStore.register({ email: 'existing@example.com', password: 'password123' })
    ).rejects.toThrow('User with this email already exists')

    expect(authStore.isAuthenticated).toBe(false)
    expect(authStore.error).toBe('User with this email already exists')
  })
})
