import { app } from "./app.js";
import { runMigrations } from "./db/migrate.js";
import { seedDatabase } from "./db/seed.js";
import { logger } from "./middleware/errorHandler.js";

const PORT = parseInt(process.env.PORT || "5000", 10);

async function startServer(): Promise<void> {
  try {
    logger.info("Applying database migrations...");
    await runMigrations();
    logger.info("Migrations completed.");

    if (process.env.AUTO_SEED === "true" || process.env.NODE_ENV !== "production") {
      logger.info("Seeding initial demo data...");
      await seedDatabase();
      logger.info("Database seeding completed.");
    }

    app.listen(PORT, "0.0.0.0", () => {
      logger.info({ port: PORT }, `Gateway listening on port ${PORT}`);
    });
  } catch (err) {
    logger.fatal({ err }, "Fatal startup error; server shutting down");
    process.exit(1);
  }
}

startServer();
