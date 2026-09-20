import { authStore } from '../stores/AuthStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export interface ReceiptListItem {
  id: string
  amount: number
  description: string | null
  created_at: string
  has_photo: boolean
}

export function fetchHealth(): Promise<{ status: string }> {
  return requestJson('/health')
}

// RCP-16: every receipts request, including photo bytes, carries the bearer
// token — photos are never exposed as an unauthenticated URL an <img> can hit.
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (authStore.accessToken) {
    headers.set('Authorization', `Bearer ${authStore.accessToken}`)
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(
      (data as { detail?: string; error?: string }).detail ||
        (data as { error?: string }).error ||
        `Request failed with status ${response.status}`,
    )
  }
  return response.json() as Promise<T>
}

export async function fetchReceipts(): Promise<ReceiptListItem[]> {
  return requestJson<ReceiptListItem[]>('/api/v1/receipts')
}

export async function uploadReceiptPhoto(
  receiptId: string,
  file: File,
): Promise<{ message: string }> {
  const body = new FormData()
  body.append('file', file)
  return requestJson(`/api/v1/receipts/${receiptId}/photo`, {
    method: 'POST',
    body,
  })
}

export async function fetchReceiptPhotoBytes(receiptId: string): Promise<Blob> {
  const headers = new Headers()
  if (authStore.accessToken) {
    headers.set('Authorization', `Bearer ${authStore.accessToken}`)
  }
  const response = await fetch(
    `${API_BASE_URL}/api/v1/receipts/${receiptId}/photo`,
    { headers },
  )
  if (!response.ok) {
    throw new Error(`Could not load the receipt photo (${response.status})`)
  }
  return response.blob()
}
