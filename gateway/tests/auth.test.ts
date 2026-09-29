import { describe, it } from "node:test";
import assert from "node:assert/strict";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { signToken } from "../src/middleware/auth.js";

describe("Gateway Auth Logic", () => {
  const secret = process.env.JWT_SECRET || "dev-secret-jwt-key-minimum-32-chars-long";

  it("should securely hash and verify passwords using bcryptjs", async () => {
    const rawPassword = "StrongPassword2026!";
    const hash = await bcrypt.hash(rawPassword, 10);

    assert.notEqual(hash, rawPassword);
    const isValid = await bcrypt.compare(rawPassword, hash);
    assert.equal(isValid, true);

    const isInvalid = await bcrypt.compare("WrongPassword", hash);
    assert.equal(isInvalid, false);
  });

  it("should generate a valid JWT containing user identity", () => {
    const user = { id: "test-user-uuid", email: "recruiter@joveo.com" };
    const token = signToken(user);

    assert.equal(typeof token, "string");
    const decoded = jwt.verify(token, secret) as { sub: string; email: string };
    assert.equal(decoded.sub, "test-user-uuid");
    assert.equal(decoded.email, "recruiter@joveo.com");
  });

  it("should reject expired or malformed tokens", () => {
    assert.throws(() => {
      jwt.verify("malformed.token.value", secret);
    });
  });
});
