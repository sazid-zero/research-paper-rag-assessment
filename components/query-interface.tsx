"use client"

import { useState } from "react"
import { Send, Loader2, Quote } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import MarkdownRenderer from "@/components/markdown-renderer"

export default function QueryInterface({ papers }) {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [selectedPapers, setSelectedPapers] = useState([])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: query,
          top_k: 5,
          paper_ids: selectedPapers.length > 0 ? selectedPapers : undefined,
        }),
      })

      if (!response.ok) throw new Error("Query failed")
      const data = await response.json()
      setResult(data)
    } catch (error) {
      alert("Failed to process query")
    } finally {
      setLoading(false)
    }
  }

  if (papers.length === 0) {
    return (
      <Card className="bg-slate-800/30 border-slate-700 p-12 text-center">
        <p className="text-slate-400">Upload some papers first to start querying</p>
      </Card>
    )
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Query Form */}
      <div className="lg:col-span-2 space-y-6">
        <Card className="bg-slate-800/50 border-slate-700 p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Your Question</label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
                placeholder="Ask anything about your papers..."
                className="w-full h-32 px-4 py-3 rounded-lg bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none disabled:opacity-50 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Filter by Papers (Optional)</label>
              <div className="grid gap-2 max-h-40 overflow-y-auto">
                {papers.map((paper) => (
                  <label
                    key={paper.paper_id}
                    className="flex items-center gap-2 p-2 rounded hover:bg-slate-700 transition cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedPapers.includes(paper.paper_id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedPapers([...selectedPapers, paper.paper_id])
                        } else {
                          setSelectedPapers(selectedPapers.filter((id) => id !== paper.paper_id))
                        }
                      }}
                      className="w-4 h-4 rounded accent-blue-600"
                    />
                    <span className="text-sm text-slate-300 truncate">{paper.metadata.title}</span>
                  </label>
                ))}
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white border-0"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Ask
                </>
              )}
            </Button>
          </form>
        </Card>
      </div>

      {/* Results */}
      <div className="lg:col-span-3">
        {result && (
          <Card className="bg-slate-800/50 border-slate-700 p-6 space-y-6">
            {/* Answer */}
            <div>
              <h3 className="text-sm font-semibold text-blue-400 mb-3 flex items-center gap-2">
                <Quote className="w-4 h-4" />
                Answer
              </h3>
              <MarkdownRenderer content={result.answer} />
              <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
                <span>Confidence: {(result.confidence * 100).toFixed(0)}%</span>
                <span>Response time: {result.response_time_ms.toFixed(0)}ms</span>
                <span className="px-2 py-1 rounded bg-slate-700 text-slate-300">{result.model_used}</span>
              </div>
            </div>

            {/* Citations */}
            {result.citations?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-blue-400 mb-3">Citations</h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {result.citations.map((citation, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-slate-900/50 border border-slate-700 text-sm space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium text-white">{citation.paper_title}</p>
                          <p className="text-xs text-slate-400">
                            {citation.section} (p. {citation.page_number})
                          </p>
                        </div>
                        <div className="px-2 py-1 rounded bg-cyan-500/20 text-cyan-300 text-xs font-medium whitespace-nowrap">
                          {(citation.relevance_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <p className="text-slate-300 italic line-clamp-2">{citation.text_snippet}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}
