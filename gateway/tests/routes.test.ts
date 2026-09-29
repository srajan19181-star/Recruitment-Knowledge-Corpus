import { describe, it } from "node:test";
import assert from "node:assert/strict";
import request from "supertest";
import { app } from "../src/app.js";

describe("Gateway Route Handlers & Validation", () => {
  it("GET /health should return 200 or 503 structured status", async () => {
    const res = await request(app).get("/health");
    assert.ok(res.status === 200 || res.status === 503);
    assert.equal(res.body.service, "gateway");
  });

  it("POST /api/auth/register should reject invalid email format", async () => {
    const res = await request(app)
      .post("/api/auth/register")
      .send({ email: "invalid-email-string", password: "ValidPassword123!" });

    assert.equal(res.status, 400);
    assert.ok(res.body.error);
  });

  it("POST /api/auth/register should reject short passwords", async () => {
    const res = await request(app)
      .post("/api/auth/register")
      .send({ email: "recruiter@joveo.com", password: "short" });

    assert.equal(res.status, 400);
    assert.ok(res.body.error);
  });

  it("GET /api/conversations should require authentication", async () => {
    const res = await request(app).get("/api/conversations");
    assert.equal(res.status, 401);
    assert.equal(res.body.error, "Authentication required");
  });
});
