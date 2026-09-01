import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './Layout'

describe('Layout', () => {
  it('renders the shared header and footer around the routed content', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<p>Route content</p>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('banner')).toBeInTheDocument()
    const headerContainer = screen.getByRole('banner').querySelector('div')
    expect(headerContainer).toHaveClass('sm:max-w-2xl', 'md:max-w-4xl', 'lg:max-w-6xl', 'xl:max-w-7xl')
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
    expect(screen.getByText('Route content')).toBeInTheDocument()
  })
})
