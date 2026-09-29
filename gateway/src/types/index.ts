import { Request } from "express";

export interface UserRecord {
  id: string;
  email: string;
  password_hash: string;
  created_at: Date;
}

export interface AuthUser {
  id: string;
  email: string;
}

export interface AuthenticatedRequest extends Request {
  user?: AuthUser;
}

export interface CitationItem {
  chunk_id: string;
  doc_id: string;
  page?: number;
}

export interface MessageRecord {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: CitationItem[];
  cache_hit: boolean;
  latency_ms: number | null;
  created_at: Date;
}

export interface ConversationRecord {
  id: string;
  user_id: string;
  title: string;
  created_at: Date;
  updated_at: Date;
}

export interface DocumentRecord {
  id: string;
  owner_id: string | null;
  filename: string;
  status: "processing" | "ready" | "failed";
  page_count: number;
  chunk_count: number;
  created_at: Date;
}

export interface FeedbackRecord {
  id: string;
  message_id: string;
  user_id: string;
  value: -1 | 1;
  comment: string | null;
  created_at: Date;
}

export interface AnalyticsSummary {
  totalQueries: number;
  cacheHitRate: number;
  avgLatencyMs: number;
  p95LatencyMs: number;
  positiveFeedbackRatio: number;
  queriesPerDay: Array<{ date: string; count: number }>;
  topDocumentsCited: Array<{ doc_id: string; citations_count: number }>;
}
