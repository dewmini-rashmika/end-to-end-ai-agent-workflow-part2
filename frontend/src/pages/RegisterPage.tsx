import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plane, Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { getApiError } from '../services/api'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

export function RegisterPage() {
  const navigate = useNavigate()
  const { register, isLoading, clearError } = useAuthStore()

  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const passwordValid = password.length >= 8 && /\d/.test(password) && /[a-zA-Z]/.test(password)
  const usernameValid = /^[a-zA-Z0-9_-]{3,64}$/.test(username)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    clearError()
    try {
      await register(email, username, password, fullName || undefined)
      navigate('/', { replace: true })
    } catch (err) {
      setError(getApiError(err))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="mx-auto h-14 w-14 rounded-2xl bg-brand-600 flex items-center justify-center shadow-xl shadow-brand-900/50">
            <Plane className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-sm text-slate-500">Start planning trips with AI</p>
        </div>

        {/* Form */}
        <div className="card p-6 space-y-4">
          {error && (
            <div className="flex items-start gap-2 rounded-xl bg-red-950/30 border border-red-800/40 px-4 py-3 text-sm text-red-300">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Full Name <span className="text-slate-600">(optional)</span>
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Smith"
                className="input-field"
                autoComplete="name"
              />
            </div>

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
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Username</label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="travel_jane"
                  className="input-field pr-8"
                  required
                  autoComplete="username"
                  pattern="^[a-zA-Z0-9_\-]+$"
                />
                {username && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    {usernameValid
                      ? <CheckCircle2 className="h-4 w-4 text-teal-400" />
                      : <AlertCircle className="h-4 w-4 text-red-400" />
                    }
                  </div>
                )}
              </div>
              <p className="text-[11px] text-slate-600 mt-1">3-64 chars, letters/numbers/_ only</p>
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
                  autoComplete="new-password"
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
              <div className="flex items-center gap-1.5 mt-1.5">
                <div className={`h-1 flex-1 rounded-full ${password.length >= 8 ? 'bg-teal-500' : 'bg-slate-700'}`} />
                <div className={`h-1 flex-1 rounded-full ${/\d/.test(password) ? 'bg-teal-500' : 'bg-slate-700'}`} />
                <div className={`h-1 flex-1 rounded-full ${/[A-Z]/.test(password) ? 'bg-teal-500' : 'bg-slate-700'}`} />
              </div>
              <p className="text-[11px] text-slate-600 mt-1">
                Min. 8 chars with letters and numbers
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading || !email || !username || !passwordValid || !usernameValid}
              className="btn-primary w-full justify-center py-3"
            >
              {isLoading ? <LoadingSpinner size="sm" /> : 'Create Account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
