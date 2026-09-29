import bcrypt from "bcryptjs";
import { pool } from "./pool.js";

export async function seedDatabase(): Promise<void> {
  const client = await pool.connect();
  try {
    const demoEmail = process.env.DEMO_USER_EMAIL || "demo@example.com";
    const demoPassword = process.env.DEMO_USER_PASSWORD || "DemoPassword123!";

    // 1. Create or retrieve demo user
    let userRes = await client.query(
      "SELECT id, email FROM users WHERE email = $1",
      [demoEmail]
    );

    let userId: string;
    if (userRes.rowCount === 0) {
      const passwordHash = await bcrypt.hash(demoPassword, 10);
      const inserted = await client.query(
        "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
        [demoEmail, passwordHash]
      );
      userId = inserted.rows[0].id;
    } else {
      userId = userRes.rows[0].id;
    }

    // 2. Check if sample conversation exists
    const convRes = await client.query(
      "SELECT id FROM conversations WHERE user_id = $1 LIMIT 1",
      [userId]
    );

    if (convRes.rowCount === 0) {
      const newConv = await client.query(
        "INSERT INTO conversations (user_id, title) VALUES ($1, $2) RETURNING id",
        [userId, "Pay Transparency Rules (NYC & Colorado)"]
      );
      const convId = newConv.rows[0].id;

      // User question
      await client.query(
        `INSERT INTO messages (conversation_id, role, content) 
         VALUES ($1, 'user', 'What are the mandatory salary disclosure rules for remote job postings in NYC and Colorado?')`,
        [convId]
      );

      // Assistant answer with citations
      const citations = [
        { chunk_id: "seed-nyc-1", doc_id: "pay_transparency_nyc", page: 1 },
        { chunk_id: "seed-co-1", doc_id: "pay_transparency_colorado", page: 1 },
      ];

      const assistantMsg = await client.query(
        `INSERT INTO messages (conversation_id, role, content, citations, cache_hit, latency_ms)
         VALUES ($1, 'assistant', $2, $3, false, 480) RETURNING id`,
        [
          convId,
          "Under New York City Local Law 32, employers with 4+ employees must state a good-faith minimum and maximum salary range for any role that can be performed in NYC, including remote roles [pay_transparency_nyc, p. 1].\n\nSimilarly, Colorado's Equal Pay for Equal Work Act mandates base salary ranges plus a general disclosure of benefits and incentive compensation [pay_transparency_colorado, p. 1].",
          JSON.stringify(citations),
        ]
      );

      // Add sample feedback
      const msgId = assistantMsg.rows[0].id;
      await client.query(
        `INSERT INTO feedback (message_id, user_id, value, comment)
         VALUES ($1, $2, 1, 'Clear summary of statutory salary disclosure differences.')
         ON CONFLICT (message_id, user_id) DO NOTHING`,
        [msgId, userId]
      );
    }

    // 3. Seed recruitment corpus document entries if table is empty
    const docCountRes = await client.query("SELECT COUNT(*) FROM documents");
    if (parseInt(docCountRes.rows[0].count, 10) === 0) {
      const corpusFiles = [
        "pay_transparency_nyc.pdf",
        "pay_transparency_colorado.pdf",
        "pay_transparency_california.pdf",
        "pay_transparency_washington.pdf",
        "job_ad_writing_best_practices.pdf",
        "inclusive_language_and_bias_reduction.pdf",
        "recruitment_marketing_fundamentals.pdf",
        "ats_and_application_funnel_metrics.pdf",
        "candidate_experience_guidelines.pdf",
        "structured_interviewing_and_rubrics.pdf",
      ];

      for (const filename of corpusFiles) {
        await client.query(
          `INSERT INTO documents (owner_id, filename, status, page_count, chunk_count)
           VALUES ($1, $2, 'ready', 2, 4)`,
          [userId, filename]
        );
      }
    }
  } finally {
    client.release();
  }
}

if (process.argv[1] && process.argv[1].endsWith("seed.ts")) {
  seedDatabase()
    .then(() => {
      console.log("Database seeded successfully.");
      process.exit(0);
    })
    .catch((err) => {
      console.error("Database seeding failed:", err);
      process.exit(1);
    });
}
