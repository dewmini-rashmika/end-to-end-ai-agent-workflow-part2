import { Cloud, Umbrella, AlertTriangle } from 'lucide-react'
import type { WeatherResults } from '../../types'


export function WeatherCard({ weather }: { weather: WeatherResults | { raw_content: string } }) {
  if ('raw_content' in weather) {
    return (
      <div className="space-y-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-300">
          <Cloud className="h-4 w-4 text-blue-400" /> Weather Forecast
        </h3>
        <div className="card p-4">
          <p className="text-sm text-slate-400 whitespace-pre-wrap">{weather.raw_content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-300">
        <Cloud className="h-4 w-4 text-blue-400" /> Weather Forecast
      </h3>
      <div className="card p-4 space-y-4">
        {/* Daily forecast chips */}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {weather.daily_forecast?.slice(0, 7).map((day, i) => (
            <div
              key={i}
              className="flex-shrink-0 flex flex-col items-center gap-1 px-3 py-2 rounded-xl bg-slate-800/60 border border-slate-700/50 min-w-[72px]"
            >
              <p className="text-xs text-slate-500">
                {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
              </p>
              <p className="text-base font-bold text-white">{Math.round(day.temp_max_c)}°</p>
              <p className="text-xs text-slate-500">{Math.round(day.temp_min_c)}°</p>
              <p className="text-[10px] text-slate-400 text-center leading-tight line-clamp-1">
                {day.condition}
              </p>
              {day.precipitation_chance_pct > 40 && (
                <span className="flex items-center gap-0.5 text-[10px] text-blue-400">
                  <Umbrella className="h-2.5 w-2.5" />
                  {day.precipitation_chance_pct}%
                </span>
              )}
            </div>
          ))}
        </div>

        {/* Activity warnings */}
        {weather.activity_warnings?.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-amber-400 flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5" /> Weather Alerts
            </p>
            {weather.activity_warnings.slice(0, 3).map((w, i) => (
              <p key={i} className="text-xs text-slate-400 pl-4">{w}</p>
            ))}
          </div>
        )}

        {/* Packing */}
        {weather.packing_suggestions?.length > 0 && (
          <div>
            <p className="text-xs font-medium text-slate-400 mb-1.5">What to pack:</p>
            <div className="flex flex-wrap gap-1.5">
              {weather.packing_suggestions.slice(0, 8).map((item, i) => (
                <span
                  key={i}
                  className="badge bg-slate-800 text-slate-300 border border-slate-700"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
