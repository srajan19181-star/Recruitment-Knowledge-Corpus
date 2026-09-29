import express from "express";
import helmet from "helmet";
import cors from "cors";
import cookieParser from "cookie-parser";
import { pinoHttp } from "pino-http";
import { logger, errorHandler } from "./middleware/errorHandler.js";
import { apiLimiter } from "./middleware/rateLimiter.js";
import { authRouter } from "./routes/auth.js";
import { conversationsRouter } from "./routes/conversations.js";
import { feedbackRouter } from "./routes/feedback.js";
import { documentsRouter } from "./routes/documents.js";
import { analyticsRouter } from "./routes/analytics.js";
import { toolsRouter } from "./routes/tools.js";
import { healthRouter } from "./routes/health.js";

export const app = express();

// Security headers
app.use(helmet());

// CORS configuration locked to frontend web origin
const webOrigin = process.env.WEB_ORIGIN || "http://localhost:3000";
app.use(
  cors({
    origin: [webOrigin, "http://127.0.0.1:3000", "http://localhost:3000"],
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "x-internal-api-key"],
  })
);

// Logging and body parsing
if (process.env.NODE_ENV !== "test") {
  app.use(pinoHttp({ logger }));
}
app.use(cookieParser());
app.use(express.json({ limit: "2mb" }));
app.use(express.urlencoded({ extended: true }));

// Global IP rate limiter
app.use("/api", apiLimiter);

// Route registrations
app.use("/health", healthRouter);
app.use("/api/auth", authRouter);
app.use("/api/conversations", conversationsRouter);
app.use("/api/messages", feedbackRouter);
app.use("/api/documents", documentsRouter);
app.use("/api/analytics", analyticsRouter);
app.use("/api/tools", toolsRouter);

// Central error handler
app.use(errorHandler);
