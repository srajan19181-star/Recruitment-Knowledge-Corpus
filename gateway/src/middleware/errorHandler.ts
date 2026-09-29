import { Request, Response, NextFunction } from "express";
import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
});

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  logger.error({ err }, "Unhandled server exception");

  if (res.headersSent) {
    return;
  }

  res.status(500).json({
    error: process.env.NODE_ENV === "production" ? "Internal server error" : err.message,
  });
}
