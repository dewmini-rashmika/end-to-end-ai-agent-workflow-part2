import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Download, Share2, RotateCcw } from 'lucide-react'

interface Props {
  response: string
  onNewTrip: () => void
}

export function FinalPlanView({ response, onNewTrip }: Props) {
  const handleDownload = () => {
    const blob = new Blob([response], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tripmate-plan.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(response)
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
          <span className="text-sm font-medium text-teal-400">Your trip plan is ready!</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleCopy} className="btn-secondary py-1.5 px-3 text-xs">
            <Share2 className="h-3.5 w-3.5" /> Copy
          </button>
          <button onClick={handleDownload} className="btn-secondary py-1.5 px-3 text-xs">
            <Download className="h-3.5 w-3.5" /> Download
          </button>
          <button onClick={onNewTrip} className="btn-primary py-1.5 px-3 text-xs">
            <RotateCcw className="h-3.5 w-3.5" /> New Trip
          </button>
        </div>
      </div>

      {/* Markdown content */}
      <div className="card p-6 sm:p-8">
        <div className="prose-tripmate max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{response}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
