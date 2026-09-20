import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { authStore } from '../stores/AuthStore'
import { receiptsStore } from '../stores/ReceiptsStore'
import { ReceiptsPage } from './ReceiptsPage'

// RCP-8/RCP-13/RCP-14/INV-NFR-3: the receipts screen lists the signed-in
// person's receipts, offers attaching from each entry, presents the photo from
// that entry, and alt-texts the image with the receipt it belongs to.

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/client')>()
  return {
    ...actual,
    fetchReceipts: vi.fn(),
    fetchReceiptPhotoBytes: vi.fn(),
    uploadReceiptPhoto: vi.fn(),
  }
})

import {
  fetchReceiptPhotoBytes,
  fetchReceipts,
} from '../api/client'

const photoBlob = new Blob([new Uint8Array([1, 2, 3])], { type: 'image/jpeg' })

describe('ReceiptsPage', () => {
  beforeEach(() => {
    vi.mocked(fetchReceipts).mockReset()
    vi.mocked(fetchReceiptPhotoBytes).mockReset()
    receiptsStore.receipts = []
    receiptsStore.error = null
    receiptsStore.isLoading = false
    receiptsStore.photoUrls = {}
    authStore.clearStorage()
  })

  it('asks a signed-out visitor to sign in (RCP-8 precondition)', () => {
    render(<ReceiptsPage />)
    expect(screen.getByText(/sign in to see your receipts/i)).toBeInTheDocument()
  })

  it('lists the signed-in person\'s receipts (RCP-8)', async () => {
    authStore.saveTokensToStorage('a', 'r', {
      id: 'u1', email: 'dee@example.com', role: 'user', is_active: true, created_at: '2026-01-01T00:00:00Z',
    })
    vi.mocked(fetchReceipts).mockResolvedValue([
      { id: 'r1', amount: 12.5, description: 'team lunch', created_at: '2026-01-01T00:00:00Z', has_photo: false },
    ])
    render(<ReceiptsPage />)
    expect(await screen.findByText(/team lunch/i)).toBeInTheDocument()
  })

  it('presents an attached photo from the receipt\'s own entry, alt-texted with its receipt (RCP-14, INV-NFR-3)', async () => {
    authStore.saveTokensToStorage('a', 'r', {
      id: 'u1', email: 'dee@example.com', role: 'user', is_active: true, created_at: '2026-01-01T00:00:00Z',
    })
    vi.mocked(fetchReceipts).mockResolvedValue([
      { id: 'r1', amount: 12.5, description: 'team lunch', created_at: '2026-01-01T00:00:00Z', has_photo: true },
    ])
    vi.mocked(fetchReceiptPhotoBytes).mockResolvedValue(photoBlob)
    render(<ReceiptsPage />)
    const img = await screen.findByRole('img')
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('alt', expect.stringContaining('team lunch'))
    expect(fetchReceiptPhotoBytes).toHaveBeenCalledWith('r1')
  })

  it('offers attaching a photo from the receipt\'s own entry when it has none (RCP-13)', async () => {
    authStore.saveTokensToStorage('a', 'r', {
      id: 'u1', email: 'dee@example.com', role: 'user', is_active: true, created_at: '2026-01-01T00:00:00Z',
    })
    vi.mocked(fetchReceipts).mockResolvedValue([
      { id: 'r1', amount: 12.5, description: 'team lunch', created_at: '2026-01-01T00:00:00Z', has_photo: false },
    ])
    render(<ReceiptsPage />)
    expect(await screen.findByRole('button', { name: /attach photo/i })).toBeInTheDocument()
  })

  it('does not offer a second attach once the receipt carries its one photo (RCP-15 UI side)', async () => {
    authStore.saveTokensToStorage('a', 'r', {
      id: 'u1', email: 'dee@example.com', role: 'user', is_active: true, created_at: '2026-01-01T00:00:00Z',
    })
    vi.mocked(fetchReceipts).mockResolvedValue([
      { id: 'r1', amount: 12.5, description: 'team lunch', created_at: '2026-01-01T00:00:00Z', has_photo: true },
    ])
    vi.mocked(fetchReceiptPhotoBytes).mockResolvedValue(photoBlob)
    render(<ReceiptsPage />)
    await screen.findByRole('img')
    expect(screen.queryByRole('button', { name: /attach photo/i })).not.toBeInTheDocument()
  })
})
