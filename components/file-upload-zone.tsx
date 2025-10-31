"use client"

import { useState, useRef } from "react"
import { Upload, Loader2, CheckCircle2 } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function FileUploadZone({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [files, setFiles] = useState([])
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleFiles = async (fileList) => {
    const pdfFiles = Array.from(fileList).filter((file) => file.type === "application/pdf")

    if (pdfFiles.length === 0) {
      alert("Please select PDF files")
      return
    }

    setFiles(pdfFiles)
    setUploading(true)

    let uploadedCount = 0
    const errors = []

    for (const file of pdfFiles) {
      try {
        const formData = new FormData()
        formData.append("file", file)

        const response = await fetch("http://localhost:8000/api/papers/upload", {
          method: "POST",
          body: formData,
        })

        if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`)

        uploadedCount++
      } catch (error) {
        errors.push(`${file.name}: ${error.message}`)
      }
    }

    setUploading(false)

    if (uploadedCount > 0) {
      setFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
      onUploadSuccess()
    }

    if (errors.length > 0) {
      alert(`Uploaded ${uploadedCount}/${pdfFiles.length} files.\nErrors:\n${errors.join("\n")}`)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  const handleFileInput = (e) => {
    handleFiles(e.target.files)
  }

  return (
    <Card
      className={`border-2 border-dashed transition-all p-12 text-center cursor-pointer ${
        isDragging ? "border-blue-500 bg-blue-500/5" : "border-slate-700 bg-slate-800/30 hover:border-slate-600"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input ref={fileInputRef} type="file" multiple accept=".pdf" onChange={handleFileInput} className="hidden" />

      <div className="flex flex-col items-center gap-4">
        <div className="p-3 rounded-lg bg-gradient-to-br from-blue-500/10 to-cyan-500/10">
          {uploading ? (
            <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
          ) : (
            <Upload className="w-8 h-8 text-blue-400" />
          )}
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-1">
            {uploading ? "Uploading papers..." : "Drag & drop your papers here"}
          </h3>
          <p className="text-sm text-slate-400 mb-4">or click to select PDF files (max 50MB each)</p>
        </div>

        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white border-0"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4 mr-2" />
              Select Files
            </>
          )}
        </Button>

        {files.length > 0 && (
          <div className="mt-6 pt-6 border-t border-slate-700 w-full">
            <p className="text-sm text-slate-300 mb-3">Ready to upload ({files.length}):</p>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {files.map((file, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm text-slate-400 p-2 rounded bg-slate-900/50">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  <span className="truncate">{file.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
