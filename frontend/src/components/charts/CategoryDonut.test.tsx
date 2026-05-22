import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CategoryDonut, CategoryLegend } from './CategoryDonut'

const counts = {
  inactive: 80,
  underutilized: 20,
  optimizable: 30,
  efficient: 70,
} as const

describe('<CategoryDonut>', () => {
  it('renders the total in the center', () => {
    render(<CategoryDonut counts={counts} />)
    // 80+20+30+70 = 200, formatted fr-FR (no thousands separator below 1000)
    expect(screen.getByText('200')).toBeInTheDocument()
    expect(screen.getByText(/total/i)).toBeInTheDocument()
  })

  it('handles empty counts gracefully', () => {
    render(<CategoryDonut counts={{ inactive: 0, underutilized: 0, optimizable: 0, efficient: 0 }} />)
    expect(screen.getByText('0')).toBeInTheDocument()
  })
})

describe('<CategoryLegend>', () => {
  it('lists all four categories with counts and percentages', () => {
    render(<CategoryLegend counts={counts} />)
    expect(screen.getByText('Inactifs')).toBeInTheDocument()
    expect(screen.getByText('Sous-utilisés')).toBeInTheDocument()
    expect(screen.getByText('Optimisables')).toBeInTheDocument()
    expect(screen.getByText('Efficaces')).toBeInTheDocument()
    // 80/200 = 40%
    expect(screen.getByText(/40\.0 %/)).toBeInTheDocument()
  })
})
