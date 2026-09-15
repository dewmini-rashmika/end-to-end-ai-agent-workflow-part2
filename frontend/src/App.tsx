import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Navbar } from './components/common/Navbar'
import { HomePage } from './pages/HomePage'
import { HistoryPage } from './pages/HistoryPage'
import { ThreadDetailPage } from './pages/ThreadDetailPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { useAuthStore } from './stores/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { loadUser } = useAuthStore()

  useEffect(() => {
    // Restore session on app load
    loadUser()
  }, [loadUser])

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <HistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/history/:id"
              element={
                <ProtectedRoute>
                  <ThreadDetailPage />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/60 py-6">
          <p className="text-center text-xs text-slate-600">
            © {new Date().getFullYear()} TripMate AI · Powered by LiteLLM + LangGraph-style agents
          </p>
        </footer>
      </div>
    </BrowserRouter>
  )
}
