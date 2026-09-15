import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'
import { authService } from '../services/authService'
import { clearAuth } from '../services/api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>
  logout: () => Promise<void>
  loadUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          await authService.login({ email, password })
          const user = await authService.getMe()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : 'Login failed'
          set({ error: msg, isLoading: false })
          throw err
        }
      },

      register: async (email, username, password, fullName) => {
        set({ isLoading: true, error: null })
        try {
          await authService.register({ email, username, password, full_name: fullName })
          await get().login(email, password)
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : 'Registration failed'
          set({ error: msg, isLoading: false })
          throw err
        }
      },

      logout: async () => {
        set({ isLoading: true })
        try {
          await authService.logout()
        } finally {
          clearAuth()
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },

      loadUser: async () => {
        const token = localStorage.getItem('access_token')
        if (!token) return
        set({ isLoading: true })
        try {
          const user = await authService.getMe()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch {
          clearAuth()
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'tripmate-auth',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    },
  ),
)
