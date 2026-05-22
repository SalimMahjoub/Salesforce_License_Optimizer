import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { UsersTable } from './UsersTable'
import type { ClassifiedUser } from '../../lib/types'

const user: ClassifiedUser = {
  id: '005Sb0000012345AAA',
  username: 'jane.doe@example.com',
  email: 'jane.doe@example.com',
  full_name: 'Jane Doe',
  license_type: 'Sales Cloud',
  activity_score: 8,
  category: 'inactive',
  last_login_date: null,
  days_inactive: 200,
  license_cost_monthly: '150.00',
}

describe('<UsersTable>', () => {
  it('shows loading state', () => {
    render(<UsersTable users={[]} loading />)
    expect(screen.getByText(/Chargement/i)).toBeInTheDocument()
  })

  it('shows empty message when no users', () => {
    render(<UsersTable users={[]} emptyMessage="Aucun zombie" />)
    expect(screen.getByText('Aucun zombie')).toBeInTheDocument()
  })

  it('renders a user row with full name and inactive badge', () => {
    render(<UsersTable users={[user]} />)
    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
    expect(screen.getByText('Inactif')).toBeInTheDocument()
    expect(screen.getByText('Jamais')).toBeInTheDocument()
  })

  it('renders score and license type', () => {
    render(<UsersTable users={[user]} />)
    expect(screen.getByText('8/100')).toBeInTheDocument()
    expect(screen.getByText('Sales Cloud')).toBeInTheDocument()
  })
})
