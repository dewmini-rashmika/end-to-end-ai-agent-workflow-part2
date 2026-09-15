import { create } from 'zustand'
import type {
  PlanResponse,
  HitlPayload,
  SSEEvent,
  Message,
  ThreadStatus,
} from '../types'
import { tripService } from '../services/tripService'
import { getApiError } from '../services/api'

interface TripState {
  // Current planning session
  currentThreadId: string | null
  planResponse: PlanResponse | null
  hitlPayload: HitlPayload | null
  finalResponse: string | null
  agentMessages: Message[]
  streamStatus: ThreadStatus | null
  isPlanning: boolean
  isSubmittingHITL: boolean
  error: string | null
  streamCleanup: (() => void) | null

  // Actions
  startPlan: (userInput: string) => Promise<void>
  submitHITL: (decision: 'approve' | 'request_changes' | 'reject', feedback?: string) => Promise<void>
  connectStream: (threadId: string) => void
  disconnectStream: () => void
  reset: () => void
  clearError: () => void
}

const initialState = {
  currentThreadId: null,
  planResponse: null,
  hitlPayload: null,
  finalResponse: null,
  agentMessages: [],
  streamStatus: null,
  isPlanning: false,
  isSubmittingHITL: false,
  error: null,
  streamCleanup: null,
}

export const useTripStore = create<TripState>((set, get) => ({
  ...initialState,

  startPlan: async (userInput: string) => {
    set({ ...initialState, isPlanning: true, error: null })
    try {
      const response = await tripService.planTrip({ user_input: userInput })
      set({
        planResponse: response,
        currentThreadId: response.thread_id,
        hitlPayload: response.hitl_payload ?? null,
        finalResponse: response.final_response ?? null,
        isPlanning: false,
      })

      // Start SSE stream if we have a thread
      if (response.thread_id) {
        get().connectStream(response.thread_id)
      }
    } catch (err) {
      set({ error: getApiError(err), isPlanning: false })
      throw err
    }
  },

  submitHITL: async (decision, feedback = '') => {
    const threadId = get().currentThreadId
    if (!threadId) return

    set({ isSubmittingHITL: true, error: null })
    try {
      const response = await tripService.submitHITL({
        thread_id: threadId,
        decision,
        feedback,
        change_agents: [],
      })
      set({
        planResponse: response,
        hitlPayload: response.hitl_payload ?? null,
        finalResponse: response.final_response ?? null,
        isSubmittingHITL: false,
      })

      if (decision === 'request_changes' && response.thread_id) {
        get().connectStream(response.thread_id)
      }
    } catch (err) {
      set({ error: getApiError(err), isSubmittingHITL: false })
    }
  },

  connectStream: (threadId: string) => {
    get().disconnectStream()

    const cleanup = tripService.streamThread(
      threadId,
      (event: SSEEvent) => {
        switch (event.type) {
          case 'status':
            set({ streamStatus: event.status })
            break
          case 'message':
            set((state) => ({
              agentMessages: [
                ...state.agentMessages,
                {
                  id: Date.now().toString(),
                  role: event.role,
                  content: event.content,
                  agent_name: event.agent_name,
                  created_at: event.created_at,
                  metadata: null,
                  model_used: null,
                } as Message,
              ],
            }))
            break
          case 'hitl_required':
            set({ streamStatus: 'awaiting_hitl' })
            break
          case 'complete':
            set({ finalResponse: event.final_response, streamStatus: 'completed' })
            break
          case 'end':
            set({ streamStatus: event.status })
            break
        }
      },
      () => set({ error: 'Lost connection to server. Please refresh.' }),
    )

    set({ streamCleanup: cleanup })
  },

  disconnectStream: () => {
    const cleanup = get().streamCleanup
    if (cleanup) {
      cleanup()
      set({ streamCleanup: null })
    }
  },

  reset: () => {
    get().disconnectStream()
    set(initialState)
  },

  clearError: () => set({ error: null }),
}))
