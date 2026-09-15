import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react'
import type { AgentResult } from '../../types'
import { cn } from '../../utils/cn'

const AGENT_LABELS: Record<string, string> = {
  supervisor: '🧠 Supervisor',
  flight_agent: '✈️ Flights',
  hotel_agent: '🏨 Hotels',
  weather_agent: '☀️ Weather',
  budget_agent: '💰 Budget',
  itinerary_agent: '🗺️ Itinerary',
  final_agent: '✨ Final Plan',
}

interface Props {
  agentResults: AgentResult[]
  selectedAgents: string[]
}

export function AgentProgressBar({ agentResults, selectedAgents }: Props) {
  const allAgents = ['supervisor', ...selectedAgents]

  return (
    <div className="card p-4 space-y-2">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
        Agent Pipeline
      </p>
      {allAgents.map((agentName) => {
        const result = agentResults.find((r) => r.agent_name === agentName)
        const status = result?.status ?? 'pending'

        return (
          <div key={agentName} className="flex items-center gap-3">
            <AgentStatusIcon status={status} />
            <span
              className={cn(
                'text-sm font-medium',
                status === 'completed' && 'text-teal-400',
                status === 'running' && 'text-brand-400',
                status === 'failed' && 'text-red-400',
                status === 'pending' && 'text-slate-500',
              )}
            >
              {AGENT_LABELS[agentName] ?? agentName}
            </span>
            {status === 'running' && (
              <span className="ml-auto text-xs text-slate-500 animate-pulse">working…</span>
            )}
            {status === 'completed' && result?.model_used && (
              <span className="ml-auto text-xs text-slate-600">{result.model_used}</span>
            )}
            {status === 'failed' && result?.error && (
              <span className="ml-auto text-xs text-red-500 truncate max-w-[120px]">
                {result.error}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function AgentStatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-teal-400 flex-shrink-0" />
    case 'running':
      return <Loader2 className="h-4 w-4 text-brand-400 animate-spin flex-shrink-0" />
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
    default:
      return <Circle className="h-4 w-4 text-slate-700 flex-shrink-0" />
  }
}
