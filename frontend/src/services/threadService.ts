import { api } from './api'
import type { ThreadListResponse, ThreadDetail, Message } from '../types'

export const threadService = {
  async listThreads(params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<ThreadListResponse> {
    const res = await api.get<ThreadListResponse>('/threads', { params })
    return res.data
  },

  async getThread(threadId: string): Promise<ThreadDetail> {
    const res = await api.get<ThreadDetail>(`/threads/${threadId}`)
    return res.data
  },

  async getMessages(threadId: string, params?: { limit?: number; offset?: number }): Promise<Message[]> {
    const res = await api.get<Message[]>(`/threads/${threadId}/messages`, { params })
    return res.data
  },

  async deleteThread(threadId: string): Promise<void> {
    await api.delete(`/threads/${threadId}`)
  },
}
