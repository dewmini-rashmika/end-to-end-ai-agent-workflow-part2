import { Plane, Clock } from 'lucide-react'
import type { FlightOption } from '../../types'

interface Props {
  flights: FlightOption[]
}

export function FlightCard({ flights }: Props) {
  if (!flights?.length) return null

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-300">
        <Plane className="h-4 w-4 text-brand-400" /> Flight Options
      </h3>
      {flights.slice(0, 3).map((f, i) => (
        <div key={i} className={`card p-4 ${i === 0 ? 'border-brand-700/50 bg-brand-950/30' : ''}`}>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <p className="font-semibold text-white text-sm">
                {f.airline} <span className="text-slate-500 font-normal">{f.flight_number}</span>
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                {f.origin} → {f.destination} · {f.stops === 0 ? 'Non-stop' : `${f.stops} stop(s)`}
              </p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-white">${f.total_price_usd.toLocaleString()}</p>
              <p className="text-xs text-slate-500">${f.price_per_person_usd}/person</p>
            </div>
          </div>
          <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {Math.floor(f.duration_minutes / 60)}h {f.duration_minutes % 60}m
            </span>
            <span className="capitalize">{f.cabin_class}</span>
            {i === 0 && (
              <span className="ml-auto badge bg-brand-900/40 text-brand-400 border border-brand-800/40">
                Best Value
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
