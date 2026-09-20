import { makeAutoObservable, runInAction } from 'mobx'
import {
  fetchReceiptPhotoBytes,
  fetchReceipts,
  uploadReceiptPhoto,
  type ReceiptListItem,
} from '../api/client'

class ReceiptsStore {
  receipts: ReceiptListItem[] = []
  isLoading = false
  error: string | null = null
  /** receipt id -> object URL of the fetched photo bytes (RCP-16: rendered locally) */
  photoUrls: Record<string, string> = {}
  uploadingReceiptId: string | null = null
  uploadErrorReceiptId: string | null = null

  constructor() {
    makeAutoObservable(this)
  }

  async load() {
    this.isLoading = true
    this.error = null
    try {
      const data = await fetchReceipts()
      runInAction(() => {
        this.receipts = data
      })
    } catch (err: any) {
      runInAction(() => {
        this.error = err.message || 'Failed to load receipts'
      })
    } finally {
      runInAction(() => {
        this.isLoading = false
      })
    }
  }

  /** RCP-16: fetch the bytes with the bearer token and render locally. */
  async loadPhoto(receiptId: string) {
    try {
      const blob = await fetchReceiptPhotoBytes(receiptId)
      const url = URL.createObjectURL(blob)
      runInAction(() => {
        const previous = this.photoUrls[receiptId]
        if (previous) URL.revokeObjectURL(previous)
        this.photoUrls[receiptId] = url
      })
    } catch {
      // a missing photo is an ordinary state, not a fault (RCP-12)
    }
  }

  /** RCP-1/RCP-13: attach one photo from the receipt's own entry. */
  async attachPhoto(receiptId: string, file: File): Promise<boolean> {
    this.uploadingReceiptId = receiptId
    this.uploadErrorReceiptId = null
    try {
      await uploadReceiptPhoto(receiptId, file)
      runInAction(() => {
        const receipt = this.receipts.find((r) => r.id === receiptId)
        if (receipt) receipt.has_photo = true
      })
      return true
    } catch (err: any) {
      runInAction(() => {
        this.error = err.message || 'Photo could not be attached'
        this.uploadErrorReceiptId = receiptId
      })
      return false
    } finally {
      runInAction(() => {
        this.uploadingReceiptId = null
      })
    }
  }

  reportUploadError(receiptId: string, message: string) {
    this.error = message
    this.uploadErrorReceiptId = receiptId
  }
}

export const receiptsStore = new ReceiptsStore()
