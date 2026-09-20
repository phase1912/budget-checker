import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, vi } from 'vitest'

// The DOM environment this suite runs in does not implement
// URL.createObjectURL, which ReceiptsStore.loadPhoto uses to render fetched
// photo bytes locally (RCP-16). Without a stub the call throws and the store's
// catch (written for RCP-12's ordinary missing-photo case) swallows it, so no
// <img> ever renders and the RCP-14/RCP-15 UI tests cannot see one. A stable
// fake URL is enough: these tests assert on rendering and alt text, not on the
// URL's contents.
beforeAll(() => {
  if (typeof URL.createObjectURL !== 'function') {
    URL.createObjectURL = vi.fn(
      () => 'blob:mock-photo-url',
    ) as unknown as typeof URL.createObjectURL
  }
  if (typeof URL.revokeObjectURL !== 'function') {
    URL.revokeObjectURL = vi.fn() as unknown as typeof URL.revokeObjectURL
  }
})

afterEach(() => {
  cleanup()
})
