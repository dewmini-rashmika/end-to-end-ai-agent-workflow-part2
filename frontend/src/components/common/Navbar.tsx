import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Plane, History, User, LogOut, LogIn, Sparkles } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { cn } from '../../utils/cn'

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 shadow-lg shadow-brand-900/50 group-hover:bg-brand-500 transition-colors">
              <Plane className="h-5 w-5 text-white" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-base font-bold text-white">TripMate</span>
              <span className="text-[10px] font-medium text-teal-400 uppercase tracking-widest">AI</span>
            </div>
            <span className="ml-1 rounded-full bg-brand-900/60 px-2 py-0.5 text-[10px] font-semibold text-brand-400 border border-brand-800/50">
              Beta
            </span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            <NavLink
              to="/"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'text-white bg-slate-800'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60',
                )
              }
            >
              <Sparkles className="h-4 w-4" />
              Plan Trip
            </NavLink>

            {isAuthenticated && (
              <NavLink
                to="/history"
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'text-white bg-slate-800'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60',
                  )
                }
              >
                <History className="h-4 w-4" />
                History
              </NavLink>
            )}
          </div>

          {/* Auth */}
          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800/60 transition-colors"
                >
                  <div className="h-7 w-7 rounded-full bg-gradient-to-br from-brand-500 to-teal-500 flex items-center justify-center text-xs font-bold text-white">
                    {user?.username?.[0]?.toUpperCase() ?? <User className="h-3.5 w-3.5" />}
                  </div>
                  <span className="text-sm text-slate-300 hidden sm:block">
                    {user?.username}
                  </span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden sm:block">Logout</span>
                </button>
              </>
            ) : (
              <Link to="/login" className="btn-primary py-2 px-4 text-sm">
                <LogIn className="h-4 w-4" />
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
