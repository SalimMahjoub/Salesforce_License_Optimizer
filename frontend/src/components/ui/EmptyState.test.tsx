import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { EmptyState } from './EmptyState'

describe('<EmptyState>', () => {
  it('shows title only', () => {
    render(<EmptyState title="Rien à afficher" />)
    expect(screen.getByText('Rien à afficher')).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows description and action button when given', () => {
    render(
      <EmptyState
        title="Vide"
        description="Aucun élément trouvé."
        action={<button>Recharger</button>}
      />,
    )
    expect(screen.getByText('Aucun élément trouvé.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Recharger' })).toBeInTheDocument()
  })
})
