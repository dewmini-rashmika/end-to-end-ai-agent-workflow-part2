import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { History, Trash2, ExternalLink, Search, Calendar, MapPin } from 'lucide-react'
import { format } from 'date-fns'
import { threadService } from '../services/threadService'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import type { ThreadSummary, ThreadStatus } from '../types'
import { cn } from '../utils/cn'

const STATUS_CONFIG: Record<ThreadStatus, { label: string; color: string }> = {
  active:        { label: 'Active',    color: 'bg-blue-900/30 text-blue-400 border-blue-800/40' },
  awaiting_hitl: { label: 'Review',    color: 'bg-amber-900/30 text-amber-400 border-amber-800/40' },
  completed:     { label: 'Completed', color: 'bg-teal-900/30 text-teal-400 border-teal-800/40' },
  rejected:      { label: 'Rejected',  color: 'bg-slate-800 text-slate-500 border-slate-700' },
  error:         { label: 'Error',     color: 'bg-red-900/30 text-red-400 border-red-800/40' },
}

export function HistoryPage() {
  const navigate = useNavigate()
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)

  const loadThreads = useCallback(async (p = 1) => {
    setIsLoading(true)
    try {
      const data = await threadService.listThreads({ page: p, page_size: 20 })
      if (p === 1) {
        setThreads(data.threads)
      } else {
        setThreads((prev) => [...prev, ...data.threads])
      }
      setHasMore(data.threads.length === 20)
    } catch {
      // handled by auth interceptor
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadThreads(1)
  }, [loadThreads])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!window.confirm('Delete this trip plan? This cannot be undone.')) return
    setDeletingId(id)
    try {
      await threadService.deleteThread(id)
      setThreads((prev) => prev.filter((t) => t.id !== id))
    } finally {
      setDeletingId(null)
    }
  }

  const filtered = threads.filter((t) => {
    const q = search.toLowerCase()
    return (
      !q ||
      t.title?.toLowerCase().includes(q) ||
      t.destination?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <History className="h-6 w-6 text-brand-400" />
            Trip History
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            All your trip planning sessions, sorted by most recent.
          </p>
        </div>
        <button onClick={() => navigate('/')} className="btn-primary text-sm py-2">
          + New Trip
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by destination or title…"
          className="input-field pl-10"
        />
      </div>

      {/* Thread list */}
      {isLoading && page === 1 ? (
        <LoadingSpinner label="Loading your trips…" className="py-16" />
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center space-y-4">
          <p className="text-4xl">🗺️</p>
          <p className="text-lg font-semibold text-slate-300">No trips yet</p>
          <p className="text-sm text-slate-500">
            {search ? 'No results match your search.' : 'Start planning your first adventure!'}
          </p>
          {!search && (
            <button onClick={() => navigate('/')} className="btn-primary mx-auto">
              Plan a Trip
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((thread) => (
            <ThreadCard
              key={thread.id}
              thread={thread}
              onOpen={() => navigate(`/history/${thread.id}`)}
              onDelete={(e) => handleDelete(e, thread.id)}
              isDeleting={deletingId === thread.id}
            />
          ))}

          {hasMore && (
            <button
              onClick={() => { setPage((p) => p + 1); loadThreads(page + 1) }}
              disabled={isLoading}
              className="btn-secondary w-full justify-center"
            >
              {isLoading ? <LoadingSpinner size="sm" /> : 'Load more'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

function ThreadCard({
  thread,
  onOpen,
  onDelete,
  isDeleting,
}: {
  thread: ThreadSummary
  onOpen: () => void
  onDelete: (e: React.MouseEvent) => void
  isDeleting: boolean
}) {
  const cfg = STATUS_CONFIG[thread.status] ?? STATUS_CONFIG.active

  return (
    <div
      className="card p-4 flex items-start gap-4 cursor-pointer hover:border-slate-600/60 transition-all hover:bg-slate-800/20 animate-fade-in"
      onClick={onOpen}
    >
      {/* Thread ID indicator */}
      <div className="flex-shrink-0 h-10 w-10 rounded-xl bg-brand-900/30 flex items-center justify-center">
        <MapPin className="h-5 w-5 text-brand-400" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="font-semibold text-white text-sm truncate">
            {thread.title || 'Untitled Trip'}
          </h3>
          <span className={cn('badge border', cfg.color)}>{cfg.label}</span>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-500 flex-wrap">
          <span className="font-mono text-slate-600 text-[10px]">
            {thread.id.slice(0, 8)}…
          </span>
          {thread.destination && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {thread.destination}
            </span>
          )}
          {thread.departure_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {thread.departure_date}
            </span>
          )}
          <span className="flex items-center gap-1 ml-auto">
            <Calendar className="h-3 w-3" />
            {format(new Date(thread.updated_at), 'MMM d, yyyy')}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 flex-shrink-0">
        <button
          onClick={(e) => { e.stopPropagation(); onOpen() }}
          className="h-8 w-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-700/50 transition-colors"
          title="Open thread"
        >
          <ExternalLink className="h-4 w-4" />
        </button>
        <button
          onClick={onDelete}
          disabled={isDeleting}
          className="h-8 w-8 flex items-center justify-center rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-950/30 transition-colors disabled:opacity-40"
          title="Delete thread"
        >
          {isDeleting ? <LoadingSpinner size="sm" /> : <Trash2 className="h-4 w-4" />}
        </button>
      </div>
    </div>
  )
}
