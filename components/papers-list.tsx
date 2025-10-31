"use client"

import { useState } from "react"
import { Trash2, FileText, Calendar, User } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function PapersList({ papers, onPapersChange }) {
  const [deleting, setDeleting] = useState(null)

  const handleDelete = async (paperId) => {
    if (!confirm("Are you sure you want to delete this paper?")) return

    setDeleting(paperId)
    try {
      const response = await fetch(`http://localhost:8000/api/papers/${paperId}`, {
        method: "DELETE",
      })

      if (!response.ok) throw new Error("Failed to delete")
      onPapersChange()
    } catch (error) {
      alert("Failed to delete paper")
    } finally {
      setDeleting(null)
    }
  }

  if (papers.length === 0) {
    return (
      <Card className="bg-slate-800/30 border-slate-700 p-12 text-center">
        <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <p className="text-slate-400">No papers uploaded yet</p>
        <p className="text-sm text-slate-500 mt-2">Upload your first research paper to get started</p>
      </Card>
    )
  }

  return (
    <div className="grid gap-4">
      {papers.map((paper) => (
        <Card
          key={paper.paper_id}
          className="bg-slate-800/50 border-slate-700 p-6 hover:bg-slate-800/70 transition-colors"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-white truncate mb-2">{paper.metadata.title}</h3>

              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                {paper.metadata.authors?.length > 0 && (
                  <div className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    <span className="truncate">
                      {paper.metadata.authors[0]}
                      {paper.metadata.authors.length > 1 ? " et al." : ""}
                    </span>
                  </div>
                )}

                {paper.metadata.year && (
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {paper.metadata.year}
                  </div>
                )}

                <div className="px-2 py-1 rounded bg-blue-500/20 text-blue-300 text-xs font-medium">
                  {paper.metadata.chunks} chunks
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDelete(paper.paper_id)}
              disabled={deleting === paper.paper_id}
              className="text-slate-400 hover:text-red-400 hover:bg-red-500/10"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </Card>
      ))}
    </div>
  )
}
