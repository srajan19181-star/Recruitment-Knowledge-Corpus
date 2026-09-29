import { Router, Response } from "express";
import { z } from "zod";
import { pool } from "../db/pool.js";
import { requireAuth } from "../middleware/auth.js";
import { proxyQueryStream } from "../services/aiClient.js";
import { AuthenticatedRequest } from "../types/index.js";

export const conversationsRouter = Router();
conversationsRouter.use(requireAuth);

const CreateConvSchema = z.object({
  title: z.string().min(1).max(200).optional(),
});

const SendMessageSchema = z.object({
  content: z.string().min(1, "Message content cannot be empty"),
});

// GET /api/conversations
conversationsRouter.get("/", async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user!.id;
  const result = await pool.query(
    "SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE user_id = $1 ORDER BY updated_at DESC",
    [userId]
  );
  res.json({ conversations: result.rows });
});

// POST /api/conversations
conversationsRouter.post("/", async (req: AuthenticatedRequest, res: Response) => {
  const parsed = CreateConvSchema.safeParse(req.body);
  const title = parsed.success && parsed.data.title ? parsed.data.title : "New Conversation";
  const userId = req.user!.id;

  const result = await pool.query(
    "INSERT INTO conversations (user_id, title) VALUES ($1, $2) RETURNING id, user_id, title, created_at, updated_at",
    [userId, title]
  );
  res.status(201).json({ conversation: result.rows[0] });
});

// GET /api/conversations/:id
conversationsRouter.get("/:id", async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user!.id;
  const { id } = req.params;

  const convResult = await pool.query(
    "SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE id = $1 AND user_id = $2",
    [id, userId]
  );

  if (convResult.rowCount === 0) {
    res.status(404).json({ error: "Conversation not found" });
    return;
  }

  const messagesResult = await pool.query(
    `SELECT m.id, m.conversation_id, m.role, m.content, m.citations, m.cache_hit, m.latency_ms, m.created_at,
            f.value as feedback_value, f.comment as feedback_comment
     FROM messages m
     LEFT JOIN feedback f ON f.message_id = m.id AND f.user_id = $2
     WHERE m.conversation_id = $1
     ORDER BY m.created_at ASC`,
    [id, userId]
  );

  res.json({
    conversation: convResult.rows[0],
    messages: messagesResult.rows,
  });
});

// DELETE /api/conversations/:id
conversationsRouter.delete("/:id", async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user!.id;
  const { id } = req.params;

  const result = await pool.query(
    "DELETE FROM conversations WHERE id = $1 AND user_id = $2 RETURNING id",
    [id, userId]
  );

  if (result.rowCount === 0) {
    res.status(404).json({ error: "Conversation not found" });
    return;
  }

  res.json({ success: true });
});

// POST /api/conversations/:id/messages (Streaming SSE proxy with client disconnect abort)
conversationsRouter.post("/:id/messages", async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user!.id;
  const { id: conversationId } = req.params;

  const parsed = SendMessageSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.issues[0].message });
    return;
  }

  const { content } = parsed.data;

  // Verify conversation ownership
  const convCheck = await pool.query(
    "SELECT id, title FROM conversations WHERE id = $1 AND user_id = $2",
    [conversationId, userId]
  );
  if (convCheck.rowCount === 0) {
    res.status(404).json({ error: "Conversation not found" });
    return;
  }

  // 1. Insert user message into Postgres
  const userMsgResult = await pool.query(
    "INSERT INTO messages (conversation_id, role, content) VALUES ($1, 'user', $2) RETURNING id, created_at",
    [conversationId, content]
  );
  const userMessageId = userMsgResult.rows[0].id;

  // Auto-generate title if it's the first message
  if (convCheck.rows[0].title === "New Conversation") {
    const generatedTitle = content.slice(0, 40).trim() + (content.length > 40 ? "..." : "");
    await pool.query(
      "UPDATE conversations SET title = $1, updated_at = NOW() WHERE id = $2",
      [generatedTitle, conversationId]
    );
  }

  // Set SSE response headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders?.();

  // Send initial acknowledgment of user message id
  res.write(`event: user_message\ndata: ${JSON.stringify({ id: userMessageId })}\n\n`);

  // Prepare abort controller linked to client disconnect
  const abortController = new AbortController();
  req.on("close", () => {
    abortController.abort();
  });

  try {
    const streamResult = await proxyQueryStream(
      content,
      userId,
      (token) => {
        if (!res.writableEnded) {
          res.write(`event: token\ndata: ${token}\n\n`);
        }
      },
      abortController.signal
    );

    // 2. Persist assistant message in Postgres
    const assistantResult = await pool.query(
      `INSERT INTO messages (conversation_id, role, content, citations, cache_hit, latency_ms)
       VALUES ($1, 'assistant', $2, $3, $4, $5)
       RETURNING id, created_at`,
      [
        conversationId,
        streamResult.fullText,
        JSON.stringify(streamResult.citations),
        streamResult.cacheHit,
        streamResult.latencyMs,
      ]
    );

    await pool.query("UPDATE conversations SET updated_at = NOW() WHERE id = $1", [conversationId]);

    // Send final done event with full message metadata
    const assistantId = assistantResult.rows[0].id;
    res.write(
      `event: done\ndata: ${JSON.stringify({
        message_id: assistantId,
        citations: streamResult.citations,
        cache_hit: streamResult.cacheHit,
        latency_ms: streamResult.latencyMs,
      })}\n\n`
    );
    res.end();
  } catch (err: unknown) {
    if (abortController.signal.aborted) {
      return;
    }
    const errorMsg = err instanceof Error ? err.message : "Generation failed";
    if (!res.writableEnded) {
      res.write(`event: error\ndata: ${JSON.stringify({ error: errorMsg })}\n\n`);
      res.end();
    }
  }
});
