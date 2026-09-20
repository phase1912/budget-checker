import { observer } from 'mobx-react-lite'
import React, { useEffect, useRef } from 'react'
import { receiptsStore } from '../stores/ReceiptsStore'
import { authStore } from '../stores/AuthStore'

// Mirrors backend MAX_PHOTO_SIZE_BYTES; enforced here first so an oversized
// file is refused without spending the upload (RCP-4's message names both sizes).
const MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024
const ACCEPTED_TYPES = 'image/jpeg,image/png'

function formatAmount(amount: number): string {
  return amount.toFixed(2)
}

function photoAltText(receipt: { amount: number; description: string | null }): string {
  // INV-NFR-3: alt text naming the receipt the photo belongs to.
  return `Receipt photo for £${formatAmount(receipt.amount)}${
    receipt.description ? ` — ${receipt.description}` : ''
  }`
}

export const ReceiptsPage: React.FC = observer(() => {
  useEffect(() => {
    if (authStore.isAuthenticated) {
      void receiptsStore.load()
    }
  }, [authStore.isAuthenticated])

  if (!authStore.isAuthenticated) {
    return (
      <div className="mx-auto w-full px-4 py-16 sm:max-w-2xl">
        <h1 className="text-2xl font-bold text-foreground">Receipts</h1>
        <p className="mt-4 text-muted-foreground">Sign in to see your receipts.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto w-full px-4 py-16 sm:px-6 sm:max-w-2xl md:max-w-4xl">
      <h1 className="text-2xl font-bold text-foreground">Receipts</h1>
      {receiptsStore.isLoading && (
        <p className="mt-4 text-muted-foreground" role="status">
          Loading receipts…
        </p>
      )}
      {receiptsStore.error && (
        <p className="mt-4 text-destructive" role="alert">
          {receiptsStore.error}
        </p>
      )}
      {!receiptsStore.isLoading && receiptsStore.receipts.length === 0 && (
        <p className="mt-4 text-muted-foreground">No receipts recorded yet.</p>
      )}
      <ul className="mt-6 space-y-4">
        {receiptsStore.receipts.map((receipt) => (
          <ReceiptEntry key={receipt.id} receipt={receipt} />
        ))}
      </ul>
    </div>
  )
})

const ReceiptEntry: React.FC<{
  receipt: {
    id: string
    amount: number
    description: string | null
    created_at: string
    has_photo: boolean
  }
}> = observer(({ receipt }) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const photoUrl = receiptsStore.photoUrls[receipt.id]

  useEffect(() => {
    if (receipt.has_photo && !photoUrl) {
      void receiptsStore.loadPhoto(receipt.id)
    }
  }, [receipt.has_photo, photoUrl])

  const onFileChosen = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (file.size > MAX_PHOTO_SIZE_BYTES) {
      receiptsStore.reportUploadError(
        receipt.id,
        `Photo is ${file.size} bytes; the limit is ${MAX_PHOTO_SIZE_BYTES} bytes`,
      )
      return
    }
    const ok = await receiptsStore.attachPhoto(receipt.id, file)
    if (ok) {
      void receiptsStore.loadPhoto(receipt.id)
    }
  }

  return (
    <li className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold text-foreground">
            £{formatAmount(receipt.amount)}
            {receipt.description ? ` — ${receipt.description}` : ''}
          </p>
          <p className="text-sm text-muted-foreground">
            {new Date(receipt.created_at).toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            className="hidden"
            onChange={(e) => void onFileChosen(e)}
          />
          {/* RCP-13: attach is offered from this receipt's own entry. Once it
              carries its one photo the control goes — replacement is
              explicitly deferred. */}
          {!receipt.has_photo && (
            <button
              type="button"
              disabled={receiptsStore.uploadingReceiptId === receipt.id}
              onClick={() => fileInputRef.current?.click()}
              className="rounded-xl bg-primary px-3 py-1.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {receiptsStore.uploadingReceiptId === receipt.id ? 'Attaching…' : 'Attach photo'}
            </button>
          )}
        </div>
      </div>
      {receiptsStore.uploadErrorReceiptId === receipt.id && receiptsStore.error && (
        <p className="mt-2 text-sm text-destructive" role="alert">
          {receiptsStore.error}
        </p>
      )}
      {/* RCP-14/RCP-16: the photo shows from this receipt's own entry, bytes
          fetched with the bearer token and rendered from a local blob URL. */}
      {photoUrl && (
        <img
          src={photoUrl}
          alt={photoAltText(receipt)}
          className="mt-3 max-h-72 rounded-lg border border-border object-contain"
        />
      )}
    </li>
  )
})
