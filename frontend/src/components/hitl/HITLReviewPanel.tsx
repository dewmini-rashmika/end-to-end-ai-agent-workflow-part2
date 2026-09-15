import { useState } from 'react'
import { CheckCircle2, Edit3, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import type { HitlPayload } from '../../types'
import { FlightCard } from '../trip/FlightCard'
import { HotelCard } from '../trip/HotelCard'
import { WeatherCard } from '../trip/WeatherCard'
import { BudgetCard } from '../trip/BudgetCard'
import { tryParseFallback } from '../../utils/parseFallback'
import { cn } from '../../utils/cn'

interface Props {
  payload: HitlPayload
  onDecision: (decision: 'approve' | 'request_changes' | 'reject', feedback?: string) => void
  isLoading: boolean
}

export function HITLReviewPanel({ payload, onDecision, isLoading }: Props) {
  const [feedback, setFeedback] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)
  const [expandedSection, setExpandedSection] = useState<string | null>('itinerary')

  const handleRequestChanges = () => {
    if (!feedback.trim()) {
      setShowFeedback(true)
      return
    }
    onDecision('request_changes', feedback)
  }

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Header */}
      <div className="card p-5 border-amber-700/40 bg-amber-950/20">
        <div className="flex items-start gap-3">
          <div className="h-8 w-8 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-lg">👀</span>
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Review Your Trip Plan</h2>
            <p className="text-sm text-slate-400 mt-1">
              Our AI agents have crafted a plan for you. Review the details below, then approve,
              request changes, or start over.
            </p>
          </div>
        </div>
      </div>

      {/* Agent summary */}
      <div className="flex flex-wrap gap-2">
        {payload.agent_results?.map((r) => (
          <span
            key={r.agent_name}
            className={cn(
              'badge border',
              r.status === 'completed' ? 'bg-teal-900/30 text-teal-400 border-teal-800/40' :
              r.status === 'failed'    ? 'bg-red-900/30 text-red-400 border-red-800/40' :
              'bg-slate-800 text-slate-400 border-slate-700',
            )}
          >
            {r.agent_name.replace('_agent', '').replace('_', ' ')}
            {r.model_used && <span className="text-slate-600 ml-1">· {r.model_used.split('/').pop()}</span>}
          </span>
        ))}
      </div>

      {/* Collapsible sections */}
      <CollapsibleSection
        id="itinerary"
        title="🗺️ Day-by-Day Itinerary"
        expanded={expandedSection}
        onToggle={setExpandedSection}
      >
        <ItinerarySummary plan={payload.itinerary_plan} />
      </CollapsibleSection>

      {payload.flight_results || payload.agent_results?.some(a => a.agent_name === 'flight_agent') ? (
        <CollapsibleSection id="flights" title="✈️ Flights" expanded={expandedSection} onToggle={setExpandedSection}>
          {payload.flight_results ? (() => {
            const fr = payload.flight_results as any
            if ('raw_content' in fr) {
              const parsed = tryParseFallback<any>(fr.raw_content, 'flights')
              if (parsed && Array.isArray(parsed) && parsed.length > 0) {
                return <FlightCard flights={parsed} />
              } else if (parsed && parsed.flights && Array.isArray(parsed.flights) && parsed.flights.length > 0) {
                return <FlightCard flights={parsed.flights} />
              }
              return <p className="text-sm text-slate-400 whitespace-pre-wrap">{fr.raw_content}</p>
            } else if (fr.flights && fr.flights.length > 0) {
              return <FlightCard flights={fr.flights} />
            }
            return <p className="text-sm text-slate-500">No flights found.</p>
          })() : <p className="text-sm text-red-400/80">Flight agent failed to retrieve data.</p>}
        </CollapsibleSection>
      ) : null}

      {payload.hotel_results || payload.agent_results?.some(a => a.agent_name === 'hotel_agent') ? (
        <CollapsibleSection id="hotels" title="🏨 Accommodation" expanded={expandedSection} onToggle={setExpandedSection}>
          {payload.hotel_results ? (() => {
            const hr = payload.hotel_results as any
            if ('raw_content' in hr) {
              const parsed = tryParseFallback<any>(hr.raw_content, 'hotels')
              if (parsed && Array.isArray(parsed) && parsed.length > 0) {
                return <HotelCard hotels={parsed} />
              } else if (parsed && parsed.hotels && Array.isArray(parsed.hotels) && parsed.hotels.length > 0) {
                return <HotelCard hotels={parsed.hotels} />
              }
              return <p className="text-sm text-slate-400 whitespace-pre-wrap">{hr.raw_content}</p>
            } else if (hr.hotels && hr.hotels.length > 0) {
              return <HotelCard hotels={hr.hotels} />
            }
            return <p className="text-sm text-slate-500">No hotels found.</p>
          })() : <p className="text-sm text-red-400/80">Hotel agent failed to retrieve data.</p>}
        </CollapsibleSection>
      ) : null}

      {payload.weather_results || payload.agent_results?.some(a => a.agent_name === 'weather_agent') ? (
        <CollapsibleSection id="weather" title="☀️ Weather & Packing" expanded={expandedSection} onToggle={setExpandedSection}>
          {payload.weather_results ? (() => {
            const wr = payload.weather_results as any
            if ('raw_content' in wr) {
              const parsed = tryParseFallback<any>(wr.raw_content, 'weather_results') ?? tryParseFallback<any>(wr.raw_content)
              if (parsed && parsed.daily_forecast) {
                return <WeatherCard weather={parsed} />
              }
              return <WeatherCard weather={wr} />
            }
            return <WeatherCard weather={wr} />
          })() : <p className="text-sm text-red-400/80">Weather agent failed to retrieve data.</p>}
        </CollapsibleSection>
      ) : null}

      {payload.budget_analysis || payload.agent_results?.some(a => a.agent_name === 'budget_agent') ? (
        <CollapsibleSection id="budget" title="💰 Budget" expanded={expandedSection} onToggle={setExpandedSection}>
          {payload.budget_analysis ? (() => {
            const br = payload.budget_analysis as any
            if ('raw_content' in br) {
              const parsed = tryParseFallback<any>(br.raw_content, 'budget_analysis') ?? tryParseFallback<any>(br.raw_content)
              if (parsed && parsed.total_estimated_usd) {
                return <BudgetCard budget={parsed} />
              }
              return <BudgetCard budget={br} />
            }
            return <BudgetCard budget={br} />
          })() : <p className="text-sm text-red-400/80">Budget agent failed to retrieve data.</p>}
        </CollapsibleSection>
      ) : null}

      {/* Feedback input */}
      {showFeedback && (
        <div className="card p-4 border-slate-700/50 animate-fade-in">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            What would you like to change?
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="e.g. Can you find cheaper hotels? I prefer business class flights. Add more outdoor activities."
            rows={3}
            className="input-field resize-none text-sm"
            autoFocus
          />
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={() => onDecision('approve')}
          disabled={isLoading}
          className="btn-primary flex-1 justify-center py-3"
        >
          <CheckCircle2 className="h-5 w-5" />
          Approve & Generate Plan
        </button>

        <button
          onClick={handleRequestChanges}
          disabled={isLoading}
          className="btn-secondary flex-1 justify-center py-3"
        >
          <Edit3 className="h-5 w-5" />
          {showFeedback ? 'Submit Changes' : 'Request Changes'}
        </button>

        <button
          onClick={() => onDecision('reject')}
          disabled={isLoading}
          className="btn-danger sm:w-auto justify-center py-3 px-4"
        >
          <XCircle className="h-5 w-5" />
          Start Over
        </button>
      </div>
    </div>
  )
}

function CollapsibleSection({
  id,
  title,
  expanded,
  onToggle,
  children,
}: {
  id: string
  title: string
  expanded: string | null
  onToggle: (id: string | null) => void
  children: React.ReactNode
}) {
  const isOpen = expanded === id
  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => onToggle(isOpen ? null : id)}
        className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-slate-200 hover:bg-slate-800/40 transition-colors"
      >
        {title}
        {isOpen ? <ChevronUp className="h-4 w-4 text-slate-500" /> : <ChevronDown className="h-4 w-4 text-slate-500" />}
      </button>
      {isOpen && <div className="px-5 pb-5">{children}</div>}
    </div>
  )
}

function ItinerarySummary({ plan }: { plan: HitlPayload['itinerary_plan'] | { raw_content: string } }) {
  if (!plan) return <p className="text-sm text-slate-500">Itinerary not yet generated.</p>

  let parsedPlan = plan as any
  if ('raw_content' in plan) {
    const parsed = tryParseFallback<any>(plan.raw_content, 'itinerary_plan') ?? tryParseFallback<any>(plan.raw_content)
    if (parsed && parsed.days) {
      parsedPlan = parsed
    } else {
      return (
        <div className="space-y-4">
          <p className="text-sm text-slate-400 whitespace-pre-wrap">{plan.raw_content}</p>
        </div>
      )
    }
  } else if (parsedPlan && parsedPlan.itinerary_plan) {
    parsedPlan = parsedPlan.itinerary_plan
  }

  if (!parsedPlan.days || !Array.isArray(parsedPlan.days)) {
    return <p className="text-sm text-slate-500">No itinerary days found.</p>
  }

  return (
    <div className="space-y-4">
      {parsedPlan.summary && (
        <p className="text-sm text-slate-300 italic border-l-2 border-brand-600 pl-3">
          {parsedPlan.summary}
        </p>
      )}
      {parsedPlan.days?.map((day: any, i: number) => (
        <div key={i} className="border-l-2 border-slate-700 pl-4 space-y-1">
          <p className="text-xs font-semibold text-brand-400 uppercase tracking-wide">
            Day {i + 1} — {day.date}
          </p>
          <p className="text-xs text-slate-400"><span className="text-slate-300">🌅 Morning:</span> {day.morning?.activity || day.morning}</p>
          <p className="text-xs text-slate-400"><span className="text-slate-300">☀️ Afternoon:</span> {day.afternoon?.activity || day.afternoon}</p>
          <p className="text-xs text-slate-400"><span className="text-slate-300">🌙 Evening:</span> {day.evening?.activity || day.evening}</p>
          {day.meals && <p className="text-xs text-slate-500">🍽️ {typeof day.meals === 'string' ? day.meals : 'Planned meals'}</p>}
          {day.estimated_day_cost_usd && (
            <p className="text-xs text-slate-600">~${day.estimated_day_cost_usd}/day</p>
          )}
        </div>
      ))}
      {parsedPlan.total_trip_cost_usd && (
        <p className="text-sm font-semibold text-white pt-2 border-t border-slate-800">
          Total estimated: ${parsedPlan.total_trip_cost_usd.toLocaleString()}
        </p>
      )}
    </div>
  )
}
