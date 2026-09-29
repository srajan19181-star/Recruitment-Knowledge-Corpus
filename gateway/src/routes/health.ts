import { Router, Request, Response } from "express";
import { pool } from "../db/pool.js";

export const healthRouter = Router();

healthRouter.get("/", async (_req: Request, res: Response) => {
  try {
    const client = await pool.connect();
    await client.query("SELECT 1");
    client.release();

    res.json({
      status: "ok",
      service: "gateway",
      database: "connected",
      timestamp: new Date().toISOString(),
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Database unavailable";
    res.status(503).json({
      status: "degraded",
      service: "gateway",
      database: "disconnected",
      error: errorMsg,
    });
  }
});
