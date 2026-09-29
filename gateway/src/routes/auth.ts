import { Router, Response } from "express";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { pool } from "../db/pool.js";
import { signToken, requireAuth } from "../middleware/auth.js";
import { authLimiter } from "../middleware/rateLimiter.js";
import { AuthenticatedRequest } from "../types/index.js";

export const authRouter = Router();

const AuthSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8, "Password must be at least 8 characters long"),
});

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
};

authRouter.post("/register", authLimiter, async (req, res: Response) => {
  const parsed = AuthSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.issues[0].message });
    return;
  }

  const { email, password } = parsed.data;
  const client = await pool.connect();
  try {
    const existing = await client.query("SELECT id FROM users WHERE email = $1", [email]);
    if (existing.rowCount && existing.rowCount > 0) {
      res.status(409).json({ error: "Email is already registered" });
      return;
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const result = await client.query(
      "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email, created_at",
      [email, passwordHash]
    );

    const user = { id: result.rows[0].id, email: result.rows[0].email };
    const token = signToken(user);

    res.cookie("token", token, COOKIE_OPTIONS);
    res.status(201).json({ user });
  } finally {
    client.release();
  }
});

authRouter.post("/login", authLimiter, async (req, res: Response) => {
  const parsed = AuthSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.issues[0].message });
    return;
  }

  const { email, password } = parsed.data;
  const client = await pool.connect();
  try {
    const result = await client.query(
      "SELECT id, email, password_hash FROM users WHERE email = $1",
      [email]
    );

    if (result.rowCount === 0) {
      res.status(401).json({ error: "Invalid email or password" });
      return;
    }

    const userRow = result.rows[0];
    const passwordValid = await bcrypt.compare(password, userRow.password_hash);
    if (!passwordValid) {
      res.status(401).json({ error: "Invalid email or password" });
      return;
    }

    const user = { id: userRow.id, email: userRow.email };
    const token = signToken(user);

    res.cookie("token", token, COOKIE_OPTIONS);
    res.json({ user });
  } finally {
    client.release();
  }
});

authRouter.post("/logout", (_req, res: Response) => {
  res.clearCookie("token", { httpOnly: true, sameSite: "lax" });
  res.json({ success: true });
});

authRouter.get("/me", requireAuth, (req: AuthenticatedRequest, res: Response) => {
  res.json({ user: req.user });
});
