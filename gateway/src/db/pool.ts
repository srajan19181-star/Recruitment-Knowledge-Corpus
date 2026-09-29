import pg from "pg";
import dotenv from "dotenv";

dotenv.config();

const { Pool } = pg;

export const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ||
    `postgresql://${process.env.POSTGRES_USER || "postgres"}:${
      process.env.POSTGRES_PASSWORD || "postgres"
    }@${process.env.POSTGRES_HOST || "postgres"}:${
      process.env.POSTGRES_PORT || "5432"
    }/${process.env.POSTGRES_DB || "recruiter_assistant"}`,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});
