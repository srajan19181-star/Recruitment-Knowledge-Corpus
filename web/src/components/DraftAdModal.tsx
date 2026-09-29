"use client";

import { useState } from "react";
import { X, Sparkles, Copy, Check, Loader2 } from "lucide-react";

interface DraftAdModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInsertToChat?: (adMarkdown: string) => void;
}

export function DraftAdModal({ isOpen, onClose, onInsertToChat }: DraftAdModalProps) {
  const [role, setRole] = useState("Full Stack Software Engineer");
  const [level, setLevel] = useState("Senior");
  const [location, setLocation] = useState("Remote (US)");
  const [salaryRange, setSalaryRange] = useState("$140,000 - $175,000");
  const [mustHaves, setMustHaves] = useState(
    "Proficiency with TypeScript and React\nExperience building RESTful APIs in Node.js or Python\nFamiliarity with SQL database design and vector search"
  );
  const [loading, setLoading] = useState(false);
  const [draftResult, setDraftResult] = useState<{ ad_markdown: string; compliance_notes: string[] } | null>(null);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setDraftResult(null);

    const mustHaveList = mustHaves
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      const res = await fetch("/api/tools/draft-ad", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role,
          level,
          location,
          salary_range: salaryRange,
          must_haves: mustHaveList,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Draft generation failed");
      setDraftResult(data);
    } catch {
      // Handle error gracefully
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!draftResult) return;
    navigator.clipboard.writeText(draftResult.ad_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-slate-900 font-semibold">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <span>Generate Compliant Job Advertisement</span>
          </div>
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-slate-700">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4">
          <form onSubmit={handleGenerate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Job Title</label>
                <input
                  type="text"
                  required
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Seniority Level</label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Intern">Intern</option>
                  <option value="Entry-Level">Entry-Level</option>
                  <option value="Mid-Level">Mid-Level</option>
                  <option value="Senior">Senior</option>
                  <option value="Lead / Staff">Lead / Staff</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Location / Work Mode</label>
                <input
                  type="text"
                  required
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Salary Range</label>
                <input
                  type="text"
                  required
                  value={salaryRange}
                  onChange={(e) => setSalaryRange(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Key Requirements (One per line)
              </label>
              <textarea
                rows={3}
                required
                value={mustHaves}
                onChange={(e) => setMustHaves(e.target.value)}
                className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg text-sm transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Draft Compliant Ad</span>}
            </button>
          </form>

          {draftResult && (
            <div className="pt-4 border-t border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase">Drafted Specification</span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={copyToClipboard}
                    className="px-2.5 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 flex items-center space-x-1"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? "Copied" : "Copy"}</span>
                  </button>
                  {onInsertToChat && (
                    <button
                      onClick={() => {
                        onInsertToChat(draftResult.ad_markdown);
                        onClose();
                      }}
                      className="px-2.5 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Insert to Chat
                    </button>
                  )}
                </div>
              </div>

              <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap max-h-60">
                {draftResult.ad_markdown}
              </pre>

              <div className="bg-blue-50 p-2.5 rounded-lg border border-blue-200">
                <p className="text-xs font-bold text-blue-900 mb-1">Built-in Compliance Features:</p>
                <ul className="list-disc pl-4 text-xs text-blue-800 space-y-0.5">
                  {draftResult.compliance_notes.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
