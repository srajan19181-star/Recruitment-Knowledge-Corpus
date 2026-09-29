import { Router, Response } from "express";
import { pool } from "../db/pool.js";
import { requireAuth } from "../middleware/auth.js";
import { AuthenticatedRequest, AnalyticsSummary } from "../types/index.js";

export const analyticsRouter = Router();
analyticsRouter.use(requireAuth);

// GET /api/analytics
analyticsRouter.get("/", async (_req: AuthenticatedRequest, res: Response) => {
  const client = await pool.connect();
  try {
    // 1. Total queries and cache hit rate
    const queryStats = await client.query(`
      SELECT 
        COUNT(CASE WHEN role = 'user' THEN 1 END) as total_queries,
        COUNT(CASE WHEN role = 'assistant' AND cache_hit = true THEN 1 END) as cache_hits,
        COUNT(CASE WHEN role = 'assistant' THEN 1 END) as total_answers,
        AVG(CASE WHEN role = 'assistant' AND latency_ms IS NOT NULL THEN latency_ms END) as avg_latency,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency
      FROM messages
    `);

    const statsRow = queryStats.rows[0];
    const totalQueries = parseInt(statsRow.total_queries || "0", 10);
    const cacheHits = parseInt(statsRow.cache_hits || "0", 10);
    const totalAnswers = parseInt(statsRow.total_answers || "0", 10);
    const cacheHitRate = totalAnswers > 0 ? Number((cacheHits / totalAnswers).toFixed(3)) : 0;
    const avgLatencyMs = statsRow.avg_latency ? Math.round(Number(statsRow.avg_latency)) : 0;
    const p95LatencyMs = statsRow.p95_latency ? Math.round(Number(statsRow.p95_latency)) : 0;

    // 2. Feedback ratio (thumbs up / total feedback)
    const feedbackStats = await client.query(`
      SELECT 
        COUNT(CASE WHEN value = 1 THEN 1 END) as positive_feedback,
        COUNT(*) as total_feedback
      FROM feedback
    `);
    const posFb = parseInt(feedbackStats.rows[0].positive_feedback || "0", 10);
    const totalFb = parseInt(feedbackStats.rows[0].total_feedback || "0", 10);
    const positiveFeedbackRatio = totalFb > 0 ? Number((posFb / totalFb).toFixed(3)) : 1.0;

    // 3. Queries per day for past 14 days
    const dailyStats = await client.query(`
      SELECT 
        TO_CHAR(DATE_TRUNC('day', created_at), 'YYYY-MM-DD') as date,
        COUNT(*) as count
      FROM messages
      WHERE role = 'user' AND created_at >= NOW() - INTERVAL '14 days'
      GROUP BY DATE_TRUNC('day', created_at)
      ORDER BY date ASC
    `);

    // 4. Top documents cited
    const citationsStats = await client.query(`
      SELECT 
        citation->>'doc_id' as doc_id,
        COUNT(*) as citations_count
      FROM messages,
      LATERAL jsonb_array_elements(citations) as citation
      WHERE role = 'assistant' AND citations IS NOT NULL AND jsonb_array_length(citations) > 0
      GROUP BY citation->>'doc_id'
      ORDER BY citations_count DESC
      LIMIT 6
    `);

    const analytics: AnalyticsSummary = {
      totalQueries,
      cacheHitRate,
      avgLatencyMs,
      p95LatencyMs,
      positiveFeedbackRatio,
      queriesPerDay: dailyStats.rows.map((r) => ({
        date: r.date,
        count: parseInt(r.count, 10),
      })),
      topDocumentsCited: citationsStats.rows.map((r) => ({
        doc_id: r.doc_id,
        citations_count: parseInt(r.citations_count, 10),
      })),
    };

    res.json({ analytics });
  } finally {
    client.release();
  }
});
