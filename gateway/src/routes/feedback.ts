import { Router, Response } from "express";
import { z } from "zod";
import { pool } from "../db/pool.js";
import { requireAuth } from "../middleware/auth.js";
import { AuthenticatedRequest } from "../types/index.js";

export const feedbackRouter = Router();
feedbackRouter.use(requireAuth);

const FeedbackSchema = z.object({
  value: z.union([z.literal(1), z.literal(-1)]),
  comment: z.string().max(500).optional(),
});

// POST /api/messages/:id/feedback
feedbackRouter.post("/:id/feedback", async (req: AuthenticatedRequest, res: Response) => {
  const { id: messageId } = req.params;
  const userId = req.user!.id;

  const parsed = FeedbackSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.issues[0].message });
    return;
  }

  const { value, comment } = parsed.data;

  // Verify message exists
  const msgCheck = await pool.query("SELECT id FROM messages WHERE id = $1", [messageId]);
  if (msgCheck.rowCount === 0) {
    res.status(404).json({ error: "Message not found" });
    return;
  }

  const result = await pool.query(
    `INSERT INTO feedback (message_id, user_id, value, comment)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (message_id, user_id)
     DO UPDATE SET value = EXCLUDED.value, comment = EXCLUDED.comment, created_at = NOW()
     RETURNING id, message_id, user_id, value, comment, created_at`,
    [messageId, userId, value, comment || null]
  );

  res.json({ success: true, feedback: result.rows[0] });
});
