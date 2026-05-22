import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Header } from './Header'
import { useAppStore } from '../../stores/appStore'
import { useAuthStore } from '../../stores/authStore'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => vi.fn() }
})

function renderHeader() {
  return render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>,
  )
}

describe('<Header>', () => {
  beforeEach(() => {
    useAppStore.setState({ sidebarOpen: true })
    useAuthStore.setState({ session: null })
  })
  afterEach(() => {
    useAuthStore.setState({ session: null })
  })

  it('shows hamburger button with correct aria-label when sidebar is open', () => {
    renderHeader()
    expect(screen.getByRole('button', { name: /fermer le menu/i })).toBeInTheDocument()
  })

  it('shows logout button when authenticated', () => {
    useAuthStore.setState({ session: { token: 't', email: 'a@b.c', tenantId: 'demo' } })
    renderHeader()
    expect(screen.getByRole('button', { name: /se déconnecter/i })).toBeInTheDocument()
    expect(screen.getByText('a@b.c')).toBeInTheDocument()
  })

  it('toggles sidebar on hamburger click', () => {
    renderHeader()
    const btn = screen.getByRole('button', { name: /fermer le menu/i })
    fireEvent.click(btn)
    expect(useAppStore.getState().sidebarOpen).toBe(false)
  })
})
