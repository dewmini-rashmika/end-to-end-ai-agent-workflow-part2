import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Plane, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { getApiError } from '../services/api'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isLoading, error, clearError } = useAuthStore()

  const from = (location.state as { from?: string })?.from ?? '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    clearError()
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setLocalError(getApiError(err))
    }
  }

  const displayError = localError ?? error

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="mx-auto h-14 w-14 rounded-2xl bg-brand-600 flex items-center justify-center shadow-xl shadow-brand-900/50">
            <Plane className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Welcome back</h1>
          <p className="text-sm text-slate-500">Sign in to your TripMate account</p>
        </div>

        {/* Form */}
        <div className="card p-6 space-y-4">
          {displayError && (
            <div className="flex items-start gap-2 rounded-xl bg-red-950/30 border border-red-800/40 px-4 py-3 text-sm text-red-300">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              {displayError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input-field"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPwd ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pr-10"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  tabIndex={-1}
                >
                  {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !email || !password}
              className="btn-primary w-full justify-center py-3"
            >
              {isLoading ? <LoadingSpinner size="sm" /> : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}
