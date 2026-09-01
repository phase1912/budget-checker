import React from 'react'
import { observer } from 'mobx-react-lite'
import { ThemeToggle } from './ThemeToggle'
import { authStore } from '../stores/AuthStore'
import { UserDropdown } from './UserDropdown'
import { AuthModal } from './AuthModal'
import { LogIn } from 'lucide-react'

export const Header: React.FC = observer(() => {
  return (
    <>
      <header className="border-b border-border bg-surface sticky top-0 z-40 backdrop-blur-md bg-surface/90">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 sm:px-6 py-4">
          <div className="flex items-center space-x-3">
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              Budget Checker
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <ThemeToggle />

            {authStore.isAuthenticated ? (
              <UserDropdown />
            ) : (
              <button
                onClick={() => authStore.openAuthModal('login')}
                className="flex items-center space-x-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity shadow-sm"
              >
                <LogIn className="h-4 w-4" />
                <span>Log In</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <AuthModal />
    </>
  )
})
