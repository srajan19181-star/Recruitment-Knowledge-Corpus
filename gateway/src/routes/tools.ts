import { Router, Response } from "express";
import { z } from "zod";
import { requireAuth } from "../middleware/auth.js";
import { checkAdCompliance, draftJobAd } from "../services/aiClient.js";
import { AuthenticatedRequest } from "../types/index.js";

export const toolsRouter = Router();
toolsRouter.use(requireAuth);

const ComplianceSchema = z.object({
  ad_text: z.string().min(1, "Job advertisement text is required"),
  jurisdiction: z.string().min(1, "Jurisdiction is required"),
});

const DraftAdSchema = z.object({
  role: z.string().min(1),
  level: z.string().min(1),
  location: z.string().min(1),
  salary_range: z.string().min(1),
  must_haves: z.array(z.string()).default([]),
});

toolsRouter.post("/check-compliance", async (req: AuthenticatedRequest, res: Response) => {
  const parsed = ComplianceSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.issues[0].message });
    return;
  }

  try {
    const result = await checkAdCompliance(parsed.data.ad_text, parsed.data.jurisdiction);
    res.json(result);
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Compliance check failed";
    res.status(502).json({ error: errorMsg });
  }
});

toolsRouter.post("/draft-ad", async (req: AuthenticatedRequest, res: Response) => {
  const parsed = DraftAdSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.issues[0].message });
    return;
  }

  try {
    const result = await draftJobAd(parsed.data);
    res.json(result);
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Drafting job ad failed";
    res.status(502).json({ error: errorMsg });
  }
});
