import { useState, type FormEvent } from 'react'
import { ArrowRight, Plane, MapPin, Calendar, RotateCcw, Loader2 } from 'lucide-react'
import { cn } from '../../utils/cn'

interface Props {
  onSubmit: (input: string) => void
  isLoading: boolean
}

const EXAMPLES = [
  'Plan a 5-day trip from London to Dubai in October 2026 for 2 people with a mid-range budget. We love food and beaches.',
  'Plan a 7-day honeymoon trip from New York to Paris in April 2027, luxury budget, interested in art and fine dining.',
  'Plan a 10-day backpacking trip from Colombo to Bangkok in December 2026 for 1 person on a budget. Love temples and street food.',
]

export function TripForm({ onSubmit, isLoading }: Props) {
  const [input, setInput] = useState('')
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [departure, setDeparture] = useState('')
  const [returnDate, setReturnDate] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || isLoading) return
    onSubmit(text)
  }

  const fillExample = (ex: string) => {
    setInput(ex)
  }

  const buildFromFields = () => {
    if (!destination) return
    const parts: string[] = []
    if (origin) parts.push(`from ${origin}`)
    parts.push(`to ${destination}`)
    if (departure) parts.push(`departing ${departure}`)
    if (returnDate) parts.push(`returning ${returnDate}`)
    const natural = `Plan a trip ${parts.join(' ')}`
    setInput(natural)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Main text input */}
      <div className="relative">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your trip — where, when, how long, budget, interests…"
          rows={3}
          className={cn(
            'input-field resize-none text-base pr-14',
            isLoading && 'opacity-60 cursor-not-allowed',
          )}
          disabled={isLoading}
          maxLength={2000}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className={cn(
            "absolute right-3 bottom-3 flex h-9 items-center justify-center rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-brand-900/50",
            isLoading ? "w-auto px-3" : "w-9"
          )}
          aria-label="Plan trip"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 text-white animate-spin mr-2" />
              <span className="text-white text-sm font-medium">Searching...</span>
            </>
          ) : (
            <ArrowRight className="h-4 w-4 text-white" />
          )}
        </button>
      </div>

      {/* Optional structured fields */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="relative">
          <Plane className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="From"
            className="input-field pl-9 text-sm py-2.5"
            disabled={isLoading}
          />
        </div>
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="To"
            className="input-field pl-9 text-sm py-2.5"
            disabled={isLoading}
          />
        </div>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="date"
            value={departure}
            onChange={(e) => setDeparture(e.target.value)}
            className="input-field pl-9 text-sm py-2.5"
            disabled={isLoading}
          />
        </div>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="date"
            value={returnDate}
            onChange={(e) => setReturnDate(e.target.value)}
            className="input-field pl-9 text-sm py-2.5"
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Build from fields button */}
      {(origin || destination) && (
        <button
          type="button"
          onClick={buildFromFields}
          className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
        >
          <RotateCcw className="h-3 w-3" />
          Build description from fields
        </button>
      )}

      {/* Example prompts */}
      <div className="space-y-2">
        <p className="text-xs text-slate-600 font-medium">Try an example:</p>
        <div className="flex flex-col gap-1.5">
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              type="button"
              onClick={() => fillExample(ex)}
              disabled={isLoading}
              className="text-left text-xs text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 px-3 py-2 rounded-lg transition-colors line-clamp-1 disabled:opacity-40"
            >
              &ldquo;{ex}&rdquo;
            </button>
          ))}
        </div>
      </div>
    </form>
  )
}
