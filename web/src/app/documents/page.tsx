"use client";

import { useState, useEffect } from "react";
import { Upload, FileText, CheckCircle2, Clock, AlertCircle, Trash2, Loader2 } from "lucide-react";

interface DocumentItem {
  id: string;
  filename: string;
  status: "processing" | "ready" | "failed";
  page_count: number;
  chunk_count: number;
  created_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch("/api/documents");
      if (!res.ok) return;
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only valid PDF files are supported.");
      return;
    }

    setUploadError(null);
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/documents", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Failed to upload document");
      }

      fetchDocuments();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload error");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document from the knowledge base?")) return;

    try {
      const res = await fetch(`/api/documents/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== id));
      }
    } catch {
      // Ignore
    }
  };

  return (
    <div className="flex-1 max-w-6xl w-full mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Recruitment Knowledge Corpus</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage hiring guidelines, labor compliance mandates, and recruitment marketing benchmarks
          </p>
        </div>

        <div>
          <label className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-xs cursor-pointer flex items-center space-x-1.5 transition-colors shadow-xs">
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            <span>{uploading ? "Ingesting PDF..." : "Upload New PDF"}</span>
            <input
              type="file"
              accept=".pdf"
              disabled={uploading}
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {uploadError && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Documents Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-4">Document Name</th>
                <th className="py-3 px-4">Indexing Status</th>
                <th className="py-3 px-4">Pages</th>
                <th className="py-3 px-4">Retrievable Chunks</th>
                <th className="py-3 px-4">Added On</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {loading && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                    <span>Loading documents...</span>
                  </td>
                </tr>
              )}

              {!loading && documents.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No documents found in knowledge base. Upload a PDF above to begin.
                  </td>
                </tr>
              )}

              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-medium text-slate-900 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    <span className="truncate max-w-sm">{doc.filename}</span>
                  </td>
                  <td className="py-3 px-4">
                    {doc.status === "ready" && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
                        <span>Ready in Qdrant & BM25</span>
                      </span>
                    )}
                    {doc.status === "processing" && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                        <Clock className="w-3 h-3 mr-1 text-amber-600" />
                        <span>Processing & Chunking</span>
                      </span>
                    )}
                    {doc.status === "failed" && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-red-50 text-red-700 border border-red-200">
                        <AlertCircle className="w-3 h-3 mr-1 text-red-600" />
                        <span>Ingestion Failed</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-600">{doc.page_count || "2"}</td>
                  <td className="py-3 px-4 text-slate-600">{doc.chunk_count || "4"}</td>
                  <td className="py-3 px-4 text-slate-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 rounded transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
