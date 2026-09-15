import { api } from './api'
import type {
  PlanTripRequest,
  PlanResponse,
  HITLDecisionRequest,
  SSEEvent,
} from '../types'

export const tripService = {
  async planTrip(data: PlanTripRequest): Promise<PlanResponse> {
    const res = await api.post<PlanResponse>('/trips/plan', data)
    return res.data
  },

  async submitHITL(data: HITLDecisionRequest): Promise<PlanResponse> {
    const res = await api.post<PlanResponse>('/trips/hitl', data)
    return res.data
  },

  /**
   * Connect to the SSE stream for a thread and call onEvent for each event.
   * Returns a cleanup function to close the EventSource.
   */
  streamThread(
    threadId: string,
    onEvent: (event: SSEEvent) => void,
    onError?: (err: Event) => void,
  ): () => void {
    const token = localStorage.getItem('access_token')
    const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
    const url = `${baseUrl}/trips/stream/${threadId}${token ? `?token=${token}` : ''}`

    // Note: EventSource doesn't support custom headers; pass token via query param
    // The backend should accept token as query param OR use cookie auth for SSE
    const es = new EventSource(url)

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as SSEEvent
        onEvent(data)
        if (data.type === 'end' || data.type === 'timeout' || data.type === 'complete') {
          es.close()
        }
      } catch {
        // ignore parse errors
      }
    }

    if (onError) {
      es.onerror = onError
    }

    return () => es.close()
  },
}
