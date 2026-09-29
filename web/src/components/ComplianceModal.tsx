"use client";

import { useState } from "react";
import { X, ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2, Loader2 } from "lucide-react";

interface ComplianceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ComplianceResult {
  compliant: boolean;
  jurisdiction: string;
  violations: string[];
  warnings: string[];
  recommendations: string[];
}

export function ComplianceModal({ isOpen, onClose }: ComplianceModalProps) {
  const [adText, setAdText] = useState("");
  const [jurisdiction, setJurisdiction] = useState("nyc");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/tools/check-compliance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad_text: adText, jurisdiction }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Compliance check failed");
      }
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-slate-900 font-semibold">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            <span>Job Advertisement Statutory Compliance Checker</span>
          </div>
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-slate-700">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4">
          <form onSubmit={handleCheck} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Target Jurisdiction</label>
              <select
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="nyc">New York City (Local Law 32 - Mandatory Salary Range)</option>
                <option value="colorado">Colorado (EPEW Act - Salary Range & Benefits Disclosures)</option>
                <option value="california">California (SB 1162 - Pay Scale Transparency)</option>
                <option value="washington">Washington State (EPOA - Wage Scale Disclosure)</option>
                <option value="general_us">General US (Salary History Ban & Bias Auditing)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Job Advertisement Text</label>
              <textarea
                required
                rows={6}
                value={adText}
                onChange={(e) => setAdText(e.target.value)}
                placeholder="Paste the drafted job advertisement or requirements section here..."
                className="w-full p-3 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !adText.trim()}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg text-sm transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Run Compliance Audit</span>}
            </button>
          </form>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {result && (
            <div className="pt-4 border-t border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase">Audit Result</span>
                {result.compliant ? (
                  <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Statutory Checks Passed</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                    <AlertOctagon className="w-4 h-4 text-red-600" />
                    <span>Compliance Violations Detected</span>
                  </span>
                )}
              </div>

              {result.violations.length > 0 && (
                <div className="bg-red-50 border border-red-200 p-3.5 rounded-lg space-y-1.5">
                  <h4 className="text-xs font-bold text-red-900 flex items-center space-x-1">
                    <AlertOctagon className="w-4 h-4 text-red-600" />
                    <span>Mandatory Legal Corrections Required</span>
                  </h4>
                  <ul className="list-disc pl-5 text-xs text-red-800 space-y-1">
                    {result.violations.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.warnings.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 p-3.5 rounded-lg space-y-1.5">
                  <h4 className="text-xs font-bold text-amber-900 flex items-center space-x-1">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Bias / Phrasing Warnings</span>
                  </h4>
                  <ul className="list-disc pl-5 text-xs text-amber-800 space-y-1">
                    {result.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.recommendations.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 p-3.5 rounded-lg space-y-1.5">
                  <h4 className="text-xs font-bold text-blue-900">Optimization Recommendations</h4>
                  <ul className="list-disc pl-5 text-xs text-blue-800 space-y-1">
                    {result.recommendations.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
