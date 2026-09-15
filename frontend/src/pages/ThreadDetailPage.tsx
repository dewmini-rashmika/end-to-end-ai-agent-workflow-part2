import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, User, Bot, Wrench, Eye } from 'lucide-react'
import { format } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { threadService } from '../services/threadService'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import type { ThreadDetail, Message, MessageRole } from '../types'
import { cn } from '../utils/cn'

const ROLE_CONFIG: Record<MessageRole, { label: string; icon: typeof User; color: string }> = {
  user:      { label: 'You',        icon: User,    color: 'text-brand-400' },
  assistant: { label: 'TripMate',   icon: Bot,     color: 'text-teal-400' },
  agent:     { label: 'Agent',      icon: Wrench,  color: 'text-purple-400' },
  tool:      { label: 'Tool',       icon: Wrench,  color: 'text-slate-500' },
  system:    { label: 'System',     icon: Bot,     color: 'text-slate-600' },
  hitl:      { label: 'Review',     icon: Eye,     color: 'text-amber-400' },
}

export function ThreadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [thread, setThread] = useState<ThreadDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    threadService.getThread(id)
      .then(setThread)
      .finally(() => setIsLoading(false))
  }, [id])

  if (isLoading) return <LoadingSpinner label="Loading thread…" className="py-32" />
  if (!thread) return (
    <div className="text-center py-32 text-slate-500">Thread not found.</div>
  )

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/history')}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to History
      </button>

      {/* Header */}
      <div className="card p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">{thread.title || 'Trip Plan'}</h1>
            <p className="text-xs text-slate-600 font-mono mt-1">Thread ID: {thread.id}</p>
          </div>
          <span className={cn(
            'badge border text-xs',
            thread.status === 'completed' ? 'bg-teal-900/30 text-teal-400 border-teal-800/40' :
            thread.status === 'awaiting_hitl' ? 'bg-amber-900/30 text-amber-400 border-amber-800/40' :
            'bg-slate-800 text-slate-400 border-slate-700'
          )}>
            {thread.status.replace('_', ' ')}
          </span>
        </div>

        <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
          <span>Created {format(new Date(thread.created_at), 'PPp')}</span>
          <span>Updated {format(new Date(thread.updated_at), 'PPp')}</span>
          <span>{thread.messages.length} messages</span>
        </div>
      </div>

      {/* Messages */}
      <div className="space-y-3">
        {thread.messages.filter((m) => m.role !== 'system' && m.role !== 'tool').map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>

      {/* HITL feedback */}
      {thread.hitl_feedback && (
        <div className="card p-4 border-amber-700/30 bg-amber-950/10">
          <p className="text-xs font-semibold text-amber-400 mb-1.5">Change Request</p>
          <p className="text-sm text-slate-300">{thread.hitl_feedback}</p>
        </div>
      )}
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const cfg = ROLE_CONFIG[message.role] ?? ROLE_CONFIG.agent
  const Icon = cfg.icon
  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  return (
    <div className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <div className={cn(
        'h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5',
        isUser ? 'bg-brand-900/40' : 'bg-slate-800',
      )}>
        <Icon className={cn('h-4 w-4', cfg.color)} />
      </div>

      <div className={cn(
        'max-w-[80%] space-y-1',
        isUser ? 'items-end' : 'items-start',
      )}>
        <div className="flex items-center gap-2">
          <span className={cn('text-xs font-medium', cfg.color)}>
            {message.agent_name ?? cfg.label}
          </span>
          <span className="text-[10px] text-slate-600">
            {format(new Date(message.created_at), 'HH:mm')}
          </span>
        </div>

        <div className={cn(
          'rounded-2xl px-4 py-3 text-sm',
          isUser
            ? 'bg-brand-900/40 text-slate-200 rounded-tr-sm'
            : isAssistant
            ? 'card text-slate-200 rounded-tl-sm'
            : 'bg-slate-800/50 text-slate-400 rounded-tl-sm text-xs',
        )}>
          {isAssistant ? (
            <div className="prose-tripmate">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          )}
        </div>
      </div>
    </div>
  )
}
