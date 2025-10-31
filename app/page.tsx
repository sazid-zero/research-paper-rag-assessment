"use client"

import { useState, useEffect } from "react"
import { Upload, Search, BookOpen, AlertCircle } from "lucide-react"
import { Card } from "@/components/ui/card"
import FileUploadZone from "@/components/file-upload-zone"
import PapersList from "@/components/papers-list"
import QueryInterface from "@/components/query-interface"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function Home() {
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [activeTab, setActiveTab] = useState("upload")

  useEffect(() => {
    fetchPapers()
  }, [])

  const fetchPapers = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/papers")
      const data = await response.json()
      setPapers(data.papers || [])
      setError("")
    } catch (err) {
      setError("Failed to fetch papers")
      console.error(err)
    }
  }

  const handleUploadSuccess = () => {
    fetchPapers()
    setActiveTab("query")
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Research Paper RAG</h1>
                <p className="text-sm text-slate-400">Intelligent document analysis with AI</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/50 border border-slate-700">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-sm text-slate-300">System Ready</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 pb-20">
        {error && (
          <Card className="mb-6 bg-red-950/50 border-red-900 text-red-200 p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            {error}
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/50 border border-slate-700 p-1 mb-8">
            <TabsTrigger value="upload" className="data-[state=active]:bg-blue-600">
              <Upload className="w-4 h-4 mr-2" />
              Upload Papers
            </TabsTrigger>
            <TabsTrigger value="papers" className="data-[state=active]:bg-blue-600">
              <BookOpen className="w-4 h-4 mr-2" />
              Papers ({papers.length})
            </TabsTrigger>
            <TabsTrigger value="query" className="data-[state=active]:bg-blue-600">
              <Search className="w-4 h-4 mr-2" />
              Query
            </TabsTrigger>
          </TabsList>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <FileUploadZone onUploadSuccess={handleUploadSuccess} />
              </div>
              <Card className="bg-slate-800/50 border-slate-700 p-6 h-fit">
                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-400" />
                  Quick Stats
                </h3>
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-700">
                    <p className="text-sm text-slate-400">Total Papers</p>
                    <p className="text-2xl font-bold text-white">{papers.length}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-700">
                    <p className="text-sm text-slate-400">Supported Format</p>
                    <p className="text-sm font-mono text-cyan-400">.pdf (max 50MB)</p>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* Papers Tab */}
          <TabsContent value="papers">
            <PapersList papers={papers} onPapersChange={fetchPapers} />
          </TabsContent>

          {/* Query Tab */}
          <TabsContent value="query">
            <QueryInterface papers={papers} />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}
