import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ToastViewport, toast, useToastStore } from './Toast'

describe('<ToastViewport>', () => {
  afterEach(() => {
    // Wipe store between tests
    useToastStore.setState({ toasts: [] })
    vi.useRealTimers()
  })

  it('renders nothing when no toasts', () => {
    render(<ToastViewport />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('renders a success toast pushed via helper', () => {
    render(<ToastViewport />)
    act(() => {
      toast.success('Done', 'Tout va bien')
    })
    expect(screen.getByText('Done')).toBeInTheDocument()
    expect(screen.getByText('Tout va bien')).toBeInTheDocument()
  })

  it('auto-dismisses after 4 seconds', () => {
    vi.useFakeTimers()
    render(<ToastViewport />)
    act(() => {
      toast.info('Hello')
    })
    expect(screen.getByText('Hello')).toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(4001)
    })
    expect(screen.queryByText('Hello')).not.toBeInTheDocument()
  })

  it('dismisses on user click', () => {
    render(<ToastViewport />)
    act(() => {
      toast.error('Oops')
    })
    const closeBtn = screen.getByRole('button', { name: /fermer/i })
    act(() => closeBtn.click())
    expect(screen.queryByText('Oops')).not.toBeInTheDocument()
  })
})
