import { api } from './api'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from '../types'

export const authService = {
  async register(data: RegisterRequest): Promise<User> {
    const res = await api.post<User>('/auth/register', data)
    return res.data
  },

  async login(data: LoginRequest): Promise<TokenResponse> {
    const res = await api.post<TokenResponse>('/auth/login', data)
    const { access_token, refresh_token } = res.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    return res.data
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout')
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
  },

  async getMe(): Promise<User> {
    const res = await api.get<User>('/auth/me')
    return res.data
  },

  async updateProfile(data: { full_name?: string; avatar_url?: string }): Promise<User> {
    const res = await api.patch<User>('/auth/me', data)
    return res.data
  },
}
