import { useNavigate } from 'react-router-dom'
import { Sparkles, Shield, Map, Heart } from 'lucide-react'
import { TripForm } from '../components/trip/TripForm'
import { AgentProgressBar } from '../components/common/AgentProgressBar'
import { HITLReviewPanel } from '../components/hitl/HITLReviewPanel'
import { FinalPlanView } from '../components/trip/FinalPlanView'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useTripStore } from '../stores/tripStore'
import { useAuthStore } from '../stores/authStore'

const FEATURES = [
  { icon: Sparkles, label: 'AI Powered Plans', desc: 'Smart itineraries tailored to your interests' },
  { icon: Map, label: 'Best Flights & Hotels', desc: 'Find the best deals across top providers' },
  { icon: Map, label: 'Day-by-Day Itineraries', desc: 'Explore, eat, and experience like a local' },
  { icon: Heart, label: 'Personalised for You', desc: 'Your style. Your budget. Your trip.' },
]

export function HomePage() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const {
    isPlanning,
    isSubmittingHITL,
    planResponse,
    hitlPayload,
    finalResponse,
    agentMessages,
    error,
    startPlan,
    submitHITL,
    reset,
    clearError,
  } = useTripStore()

  const handleSubmit = async (input: string) => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/', pendingInput: input } })
      return
    }
    clearError()
    await startPlan(input)
  }

  const handleHITL = async (decision: 'approve' | 'request_changes' | 'reject', feedback?: string) => {
    await submitHITL(decision, feedback)
  }

  const isIdle = !planResponse && !isPlanning

  // Build agent results from stream messages for progress bar
  const agentResults = planResponse?.hitl_payload?.agent_results ??
    agentMessages
      .filter((m) => m.role === 'agent')
      .map((m) => ({
        agent_name: m.agent_name ?? 'unknown',
        status: 'completed' as const,
        error: null,
        prompt_tokens: 0,
        completion_tokens: 0,
        model_used: m.model_used,
      }))

  return (
    <div className="min-h-screen">
      {/* Hero section */}
      {isIdle && (
        <div className="relative overflow-hidden">
          {/* Background image overlay */}
          <div
            className="absolute inset-0 bg-cover bg-center opacity-20"
            style={{ backgroundImage: "url('/hero-bg.jpg')" }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-slate-950/60 via-slate-950/80 to-slate-950" />

          <div className="relative mx-auto max-w-4xl px-4 pt-20 pb-12 text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight">
              Plan Your{' '}
              <span className="bg-gradient-to-r from-brand-400 to-teal-400 bg-clip-text text-transparent">
                Perfect Trip
              </span>
              <br />in Seconds
            </h1>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Tell us where you want to go. Our AI agents search flights, curate hotels,
              and craft a personalised day-by-day itinerary — all from one sentence.
            </p>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="mx-auto max-w-4xl px-4 py-8 space-y-8">

        {/* Trip form — always visible */}
        {(isIdle || isPlanning) && (
          <div className="card p-6 space-y-2">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-4 w-4 text-brand-400" />
              <span className="text-sm font-medium text-slate-300">Describe your trip</span>
              {!isAuthenticated && (
                <span className="ml-auto text-xs text-slate-500">
                  Sign in to save your plans
                </span>
              )}
            </div>
            <TripForm onSubmit={handleSubmit} isLoading={isPlanning} />
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="card p-4 border-red-700/40 bg-red-950/20">
            <div className="flex items-start gap-3">
              <Shield className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-300">Unable to plan trip</p>
                <p className="text-sm text-slate-400 mt-0.5">{error}</p>
              </div>
              <button onClick={clearError} className="ml-auto text-slate-600 hover:text-slate-400 text-xs">
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Blocked by guardrail */}
        {planResponse?.status === 'blocked' && (
          <div className="card p-5 border-amber-700/40 bg-amber-950/20 text-center space-y-3">
            <p className="text-2xl">🚫</p>
            <p className="text-base font-semibold text-amber-300">Request Blocked</p>
            <p className="text-sm text-slate-400">{planResponse.reason}</p>
            <button onClick={reset} className="btn-secondary mx-auto">
              Try a different request
            </button>
          </div>
        )}

        {/* Planning in progress */}
        {isPlanning && (
          <div className="space-y-4">
            <LoadingSpinner label="AI agents are researching your trip…" size="lg" className="py-8" />
            {agentResults.length > 0 && (
              <AgentProgressBar
                agentResults={agentResults}
                selectedAgents={planResponse?.hitl_payload?.selected_agents ?? []}
              />
            )}
          </div>
        )}

        {/* Stream agent messages (while planning) */}
        {isPlanning && agentMessages.length > 0 && (
          <div className="card p-4 space-y-2 max-h-48 overflow-y-auto">
            {agentMessages.map((msg, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="text-slate-600 flex-shrink-0">
                  {msg.agent_name ?? msg.role}:
                </span>
                <span className="text-slate-400 line-clamp-2">{msg.content}</span>
              </div>
            ))}
          </div>
        )}

        {/* HITL review */}
        {planResponse?.status === 'awaiting_review' && hitlPayload && (
          <HITLReviewPanel
            payload={hitlPayload}
            onDecision={handleHITL}
            isLoading={isSubmittingHITL}
          />
        )}

        {/* Replanning spinner */}
        {isSubmittingHITL && (
          <LoadingSpinner label="Updating your plan…" size="lg" className="py-8" />
        )}

        {/* Final result */}
        {finalResponse && (
          <FinalPlanView response={finalResponse} onNewTrip={reset} />
        )}

        {/* Rejected */}
        {planResponse?.status === 'rejected' && (
          <div className="card p-6 text-center space-y-4">
            <p className="text-2xl">👋</p>
            <p className="text-base font-semibold text-slate-300">Plan discarded</p>
            <p className="text-sm text-slate-500">Ready to plan something new?</p>
            <button onClick={reset} className="btn-primary mx-auto">
              Start a new trip
            </button>
          </div>
        )}

        {/* Feature grid — only on idle */}
        {isIdle && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
            {FEATURES.map(({ icon: Icon, label, desc }, i) => (
              <div key={i} className="card p-4 text-center space-y-2 hover:border-slate-600/60 transition-colors">
                <div className="mx-auto h-10 w-10 rounded-xl bg-brand-900/40 flex items-center justify-center">
                  <Icon className="h-5 w-5 text-brand-400" />
                </div>
                <p className="text-sm font-semibold text-white">{label}</p>
                <p className="text-xs text-slate-500">{desc}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
