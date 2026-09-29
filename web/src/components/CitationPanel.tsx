"use client";

import { X, FileText, ExternalLink } from "lucide-react";

export interface CitationData {
  chunk_id: string;
  doc_id: string;
  page?: number;
  text?: string;
}

interface CitationPanelProps {
  citation: CitationData | null;
  onClose: () => void;
}

export function CitationPanel({ citation, onClose }: CitationPanelProps) {
  if (!citation) return null;

  return (
    <aside className="w-80 border-l border-slate-200 bg-white h-full flex flex-col shadow-sm">
      <div className="p-4 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-sm font-semibold text-slate-800">
          <FileText className="w-4 h-4 text-blue-600" />
          <span>Source Citation</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-slate-100 text-slate-500 hover:text-slate-800"
          aria-label="Close citation details"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-4 text-sm">
        <div>
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
            Referenced Document
          </label>
          <p className="font-medium text-slate-900 break-words">{citation.doc_id}.pdf</p>
        </div>

        {citation.page && (
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Page Reference
            </label>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
              Page {citation.page}
            </span>
          </div>
        )}

        <div>
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
            Chunk ID (Qdrant Vector)
          </label>
          <code className="text-xs bg-slate-100 p-1.5 rounded block text-slate-700 font-mono break-all">
            {citation.chunk_id}
          </code>
        </div>

        <div className="pt-2 border-t border-slate-100">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
            Verification Notice
          </label>
          <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded border border-slate-200">
            This passage was retrieved via hybrid search (Qdrant Dense + BM25 Sparse fused via RRF).
            For regulatory and statutory compliance, always corroborate against official state labor resources.
          </p>
        </div>
      </div>
    </aside>
  );
}
