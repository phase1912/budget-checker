import React, { useState, useRef, useEffect } from 'react'
import { observer } from 'mobx-react-lite'
import { authStore } from '../stores/AuthStore'
import { LogOut, Settings, ShieldCheck } from 'lucide-react'

export const UserDropdown: React.FC = observer(() => {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const user = authStore.user

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!user) return null

  const roleLabel = user.role === 'admin' ? 'Admin' : 'User'

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 rounded-full border border-border bg-surface p-1.5 text-foreground hover:bg-muted focus:outline-none transition-colors"
        aria-label="User menu"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-medium text-sm">
          {user.first_name ? user.first_name[0].toUpperCase() : user.email[0].toUpperCase()}
        </div>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 rounded-xl border border-border bg-surface shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="px-4 py-3 border-b border-border">
            <p className="text-sm font-semibold text-foreground truncate">
              {authStore.userDisplayName}
            </p>
            <p className="text-xs text-muted-foreground truncate mt-0.5">{user.email}</p>
            <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              <ShieldCheck className="h-3 w-3" />
              <span>{roleLabel}</span>
            </div>
          </div>

          <div className="py-1">
            <button
              onClick={() => {
                setIsOpen(false)
                alert('Settings coming soon!')
              }}
              className="flex w-full items-center px-4 py-2 text-sm text-foreground hover:bg-muted transition-colors"
            >
              <Settings className="mr-2 h-4 w-4 text-muted-foreground" />
              Settings
            </button>
            <button
              onClick={() => {
                setIsOpen(false)
                authStore.logout()
              }}
              className="flex w-full items-center px-4 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  )
})
