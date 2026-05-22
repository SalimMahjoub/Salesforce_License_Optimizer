import { create } from 'zustand'

interface AppState {
  sidebarOpen: boolean
  // currentOrg defaults to "demo" so the app is usable out-of-the-box with the
  // backend's DemoDataProvider (no Salesforce credentials required).
  currentOrg: string
  toggleSidebar: () => void
  openSidebar: () => void
  closeSidebar: () => void
  setCurrentOrg: (org: string) => void
}

// Default the drawer open on desktop, closed on mobile. SSR-safe.
const isDesktop = typeof window !== 'undefined' && window.innerWidth >= 1024

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: isDesktop,
  currentOrg: 'demo',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  openSidebar: () => set({ sidebarOpen: true }),
  closeSidebar: () => set({ sidebarOpen: false }),
  setCurrentOrg: (org) => set({ currentOrg: org }),
}))
