import { create } from 'zustand'

interface AppState {
  sidebarOpen: boolean
  currentOrg: string | null
  toggleSidebar: () => void
  setCurrentOrg: (org: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  currentOrg: null,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setCurrentOrg: (org) => set({ currentOrg: org }),
}))

