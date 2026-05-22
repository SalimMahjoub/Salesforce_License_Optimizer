import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Skeleton, StatGridSkeleton, TableRowsSkeleton } from './Skeleton'

describe('<Skeleton>', () => {
  it('applies the variant class', () => {
    const { container } = render(<Skeleton variant="stat" />)
    const el = container.firstChild as HTMLElement
    expect(el).toHaveClass('animate-pulse')
    expect(el).toHaveClass('h-32')
  })

  it('hides from screen readers', () => {
    const { container } = render(<Skeleton variant="row" />)
    const el = container.firstChild as HTMLElement
    expect(el).toHaveAttribute('aria-hidden', 'true')
  })
})

describe('<StatGridSkeleton>', () => {
  it('renders 4 stat skeletons by default', () => {
    const { container } = render(<StatGridSkeleton />)
    // 4 child stat skeletons inside the grid
    expect(container.querySelectorAll('.animate-pulse')).toHaveLength(4)
  })

  it('respects custom count', () => {
    const { container } = render(<StatGridSkeleton count={2} />)
    expect(container.querySelectorAll('.animate-pulse')).toHaveLength(2)
  })
})

describe('<TableRowsSkeleton>', () => {
  it('renders the requested number of rows', () => {
    const { container } = render(<TableRowsSkeleton rows={7} />)
    expect(container.querySelectorAll('.animate-pulse')).toHaveLength(7)
  })
})
