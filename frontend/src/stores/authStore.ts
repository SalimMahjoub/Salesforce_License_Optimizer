import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthSession {
  token: string
  email: string
  tenantId: string
}

interface AuthState {
  session: AuthSession | null
  setSession: (s: AuthSession | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      session: null,
      setSession: (session) => set({ session }),
      logout: () => set({ session: null }),
    }),
    {
      name: 'slo-auth',
      partialize: (state) => ({ session: state.session }),
    },
  ),
)
