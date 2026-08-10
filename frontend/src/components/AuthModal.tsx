import React, { useState } from 'react'
import { observer } from 'mobx-react-lite'
import { authStore } from '../stores/AuthStore'
import { X, Lock, Mail, User, AlertCircle, Loader2 } from 'lucide-react'

export const AuthModal: React.FC = observer(() => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [clientError, setClientError] = useState<string | null>(null)

  if (!authStore.isAuthModalOpen) return null

  const isLogin = authStore.authModalTab === 'login'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setClientError(null)

    if (!email.trim() || !password) {
      setClientError('Please fill in all required fields.')
      return
    }

    if (!isLogin) {
      if (password !== confirmPassword) {
        setClientError('Passwords do not match.')
        return
      }
      if (password.length < 6) {
        setClientError('Password must be at least 6 characters long.')
        return
      }
    }

    try {
      if (isLogin) {
        await authStore.login({ email, password })
      } else {
        await authStore.register({
          email,
          password,
          first_name: firstName || undefined,
          last_name: lastName || undefined,
        })
      }
      setEmail('')
      setPassword('')
      setConfirmPassword('')
      setFirstName('')
      setLastName('')
    } catch {
      // Error is handled in store
    }
  }

  const errorMessage = clientError || authStore.error

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-surface shadow-2xl p-6 overflow-hidden">
        <button
          onClick={authStore.closeAuthModal}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground transition-colors p-1 rounded-lg hover:bg-muted"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex border-b border-border mb-6">
          <button
            onClick={() => {
              setClientError(null)
              authStore.setAuthModalTab('login')
            }}
            className={`flex-1 py-3 text-sm font-semibold border-b-2 transition-colors ${
              isLogin
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => {
              setClientError(null)
              authStore.setAuthModalTab('register')
            }}
            className={`flex-1 py-3 text-sm font-semibold border-b-2 transition-colors ${
              !isLogin
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Create Account
          </button>
        </div>

        {errorMessage && (
          <div className="mb-4 flex items-center gap-2 rounded-xl bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  First Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="Alex"
                    className="w-full rounded-xl border border-border bg-background pl-9 pr-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Smith"
                  className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full rounded-xl border border-border bg-background pl-9 pr-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-border bg-background pl-9 pr-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-border bg-background pl-9 pr-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={authStore.isLoading}
            className="w-full flex items-center justify-center rounded-xl bg-primary py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-opacity mt-6 shadow-lg shadow-primary/25"
          >
            {authStore.isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : isLogin ? (
              'Sign In'
            ) : (
              'Register'
            )}
          </button>
        </form>
      </div>
    </div>
  )
})
