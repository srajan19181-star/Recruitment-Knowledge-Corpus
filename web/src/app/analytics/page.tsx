"use client";

import { useState, useEffect } from "react";
import {
  Zap,
  Clock,
  MessageSquare,
  ThumbsUp,
  FileText,
  Loader2,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

interface AnalyticsData {
  totalQueries: number;
  cacheHitRate: number;
  avgLatencyMs: number;
  p95LatencyMs: number;
  positiveFeedbackRatio: number;
  queriesPerDay: Array<{ date: string; count: number }>;
  topDocumentsCited: Array<{ doc_id: string; citations_count: number }>;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/analytics")
      .then((res) => (res.ok ? res.json() : null))
      .then((res) => {
        if (res && res.analytics) {
          setData(res.analytics);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        <span>Loading production analytics from Postgres...</span>
      </div>
    );
  }

  const stats = data || {
    totalQueries: 0,
    cacheHitRate: 0,
    avgLatencyMs: 0,
    p95LatencyMs: 0,
    positiveFeedbackRatio: 1.0,
    queriesPerDay: [],
    topDocumentsCited: [],
  };

  return (
    <div className="flex-1 max-w-6xl w-full mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">RAG Pipeline System Analytics</h1>
        <p className="text-xs text-slate-500 mt-1">
          Real-time metrics computed directly from PostgreSQL message and feedback records
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>Semantic Cache Hit Rate</span>
            <Zap className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {(stats.cacheHitRate * 100).toFixed(1)}%
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Queries served without LLM compute</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>Latency (Avg / p95)</span>
            <Clock className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {stats.avgLatencyMs}ms / <span className="text-slate-500 text-lg">{stats.p95LatencyMs}ms</span>
          </p>
          <p className="text-[11px] text-slate-400 mt-1">End-to-end pipeline response time</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>Total Recruiter Queries</span>
            <MessageSquare className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.totalQueries}</p>
          <p className="text-[11px] text-slate-400 mt-1">Logged across all conversations</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>Positive Feedback Ratio</span>
            <ThumbsUp className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {(stats.positiveFeedbackRatio * 100).toFixed(1)}%
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Recruiter thumbs up vs thumbs down</p>
        </div>
      </div>

      {/* Real Charts via Recharts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Query Volume Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Daily Query Volume Trend
          </h3>
          <div className="h-64 w-full">
            {stats.queriesPerDay.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.queriesPerDay}>
                  <defs>
                    <linearGradient id="colorQuery" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} />
                  <YAxis tick={{ fontSize: 10 }} tickLine={false} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="#2563eb"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorQuery)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Insufficient temporal query data
              </div>
            )}
          </div>
        </div>

        {/* Top Documents Cited Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Top Cited Documents in RAG Answers
          </h3>
          <div className="h-64 w-full">
            {stats.topDocumentsCited.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.topDocumentsCited} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis
                    dataKey="doc_id"
                    type="category"
                    tick={{ fontSize: 9 }}
                    width={130}
                    tickFormatter={(v) => (v.length > 18 ? v.substring(0, 18) + "..." : v)}
                  />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <Bar dataKey="citations_count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No document citations recorded yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
