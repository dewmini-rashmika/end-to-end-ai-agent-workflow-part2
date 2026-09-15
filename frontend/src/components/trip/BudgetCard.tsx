import { TrendingUp, TrendingDown, Minus, Lightbulb } from 'lucide-react'
import type { BudgetAnalysis } from '../../types'
import { cn } from '../../utils/cn'


const CATEGORY_LABELS: Record<string, string> = {
  flights: '✈️ Flights',
  accommodation: '🏨 Accommodation',
  meals: '🍽️ Meals',
  local_transport: '🚇 Local Transport',
  activities_attractions: '🎭 Activities',
  shopping_misc: '🛍️ Shopping',
  tips_fees: '💳 Tips & Fees',
  contingency_10pct: '🛡️ Contingency',
}

export function BudgetCard({ budget }: { budget: BudgetAnalysis | { raw_content: string } }) {
  if ('raw_content' in budget) {
    return (
      <div className="space-y-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-300">
          💰 Budget Analysis
        </h3>
        <div className="card p-4">
          <p className="text-sm text-slate-400 whitespace-pre-wrap">{budget.raw_content}</p>
        </div>
      </div>
    )
  }

  const statusConfig = {
    within_budget: { icon: TrendingDown, color: 'text-teal-400', label: 'Within Budget' },
    over_budget: { icon: TrendingUp, color: 'text-red-400', label: 'Over Budget' },
    under_budget: { icon: TrendingDown, color: 'text-teal-400', label: 'Under Budget' },
    no_budget_set: { icon: Minus, color: 'text-slate-400', label: 'Estimated Total' },
  }

  const { icon: Icon, color, label } = statusConfig[budget.budget_status] ?? statusConfig.no_budget_set

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-300">
        💰 Budget Analysis
      </h3>
      <div className="card p-4 space-y-4">
        {/* Total */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-3xl font-bold text-white">
              ${budget.total_estimated_usd.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              ${budget.cost_per_person_usd?.toLocaleString()} per person
            </p>
          </div>
          <div className={cn('flex items-center gap-1.5', color)}>
            <Icon className="h-5 w-5" />
            <span className="text-sm font-medium">{label}</span>
          </div>
        </div>

        {/* Breakdown bar chart */}
        {budget.breakdown && (
          <div className="space-y-2">
            {Object.entries(budget.breakdown).map(([key, value]) => {
              const pct = Math.round((value / budget.total_estimated_usd) * 100)
              return (
                <div key={key}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-slate-400">{CATEGORY_LABELS[key] ?? key}</span>
                    <span className="text-slate-300 font-medium">${value.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-brand-600 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Savings tips */}
        {budget.savings_tips?.length > 0 && (
          <div className="border-t border-slate-800 pt-3">
            <p className="text-xs font-medium text-amber-400 flex items-center gap-1 mb-2">
              <Lightbulb className="h-3.5 w-3.5" /> Money-saving tips
            </p>
            <ul className="space-y-1">
              {budget.savings_tips.slice(0, 4).map((tip, i) => (
                <li key={i} className="text-xs text-slate-400 pl-3 relative before:absolute before:left-0 before:content-['•'] before:text-slate-600">
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
