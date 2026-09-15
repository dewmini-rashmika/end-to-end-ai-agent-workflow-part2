import { useEffect, useRef } from 'react'
import type { SSEEvent } from '../types'

/**
 * Custom hook for SSE subscriptions.
 * Automatically closes the EventSource on unmount.
 */
export function useSSE(
  threadId: string | null,
  onEvent: (event: SSEEvent) => void,
  enabled = true,
) {
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!threadId || !enabled) return

    const token = localStorage.getItem('access_token')
    const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
    const url = `${baseUrl}/trips/stream/${threadId}${token ? `?token=${token}` : ''}`

    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as SSEEvent
        onEvent(data)
        if (data.type === 'end' || data.type === 'timeout') {
          es.close()
        }
      } catch {/* ignore */}
    }

    es.onerror = () => {
      es.close()
    }

    return () => {
      es.close()
      esRef.current = null
    }
  }, [threadId, enabled]) // onEvent intentionally excluded (use useCallback at call site)
}
