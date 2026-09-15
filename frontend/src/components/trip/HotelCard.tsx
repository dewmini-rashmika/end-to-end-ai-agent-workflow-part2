import { Hotel, Star, CheckCircle2, XCircle } from 'lucide-react'
import type { HotelOption } from '../../types'

interface Props {
  hotels: HotelOption[]
}

export function HotelCard({ hotels }: Props) {
  if (!hotels?.length) return null

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-300">
        <Hotel className="h-4 w-4 text-teal-400" /> Accommodation Options
      </h3>
      {hotels.slice(0, 3).map((h, i) => (
        <div key={i} className={`card p-4 ${i === 0 ? 'border-teal-700/50 bg-teal-950/20' : ''}`}>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-white text-sm">{h.name}</p>
              <div className="flex items-center gap-1 mt-0.5">
                {Array.from({ length: h.star_rating }).map((_, si) => (
                  <Star key={si} className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{h.description}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-lg font-bold text-white">${h.total_price_usd.toLocaleString()}</p>
              <p className="text-xs text-slate-500">${h.price_per_night_usd}/night · {h.nights} nights</p>
            </div>
          </div>
          <div className="flex items-center gap-3 mt-3 text-xs">
            {h.free_cancellation ? (
              <span className="flex items-center gap-1 text-teal-400">
                <CheckCircle2 className="h-3.5 w-3.5" /> Free cancellation
              </span>
            ) : (
              <span className="flex items-center gap-1 text-slate-500">
                <XCircle className="h-3.5 w-3.5" /> Check cancellation policy
              </span>
            )}
            {i === 0 && (
              <span className="ml-auto badge bg-teal-900/40 text-teal-400 border border-teal-800/40">
                Top Pick
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
