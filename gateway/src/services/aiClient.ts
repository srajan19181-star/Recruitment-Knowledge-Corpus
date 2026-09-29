import { CitationItem } from "../types/index.js";

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://ai-service:8000";
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY || "dev-internal-secret-key";

export interface StreamResult {
  fullText: string;
  citations: CitationItem[];
  cacheHit: boolean;
  latencyMs: number;
}

export async function proxyQueryStream(
  query: string,
  userId: string,
  onToken: (token: string) => void,
  abortSignal: AbortSignal
): Promise<StreamResult> {
  const startTime = Date.now();
  const url = `${AI_SERVICE_URL}/query`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-api-key": INTERNAL_API_KEY,
      "x-user-id": userId,
    },
    body: JSON.stringify({ query, user_id: userId }),
    signal: abortSignal,
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => "");
    throw new Error(`AI service error [${response.status}]: ${errorBody}`);
  }

  if (!response.body) {
    throw new Error("AI service returned empty stream body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";
  let citations: CitationItem[] = [];
  let cacheHit = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      let currentEvent = "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("event:")) {
          currentEvent = trimmed.replace("event:", "").trim();
        } else if (trimmed.startsWith("data:")) {
          const dataStr = trimmed.replace("data:", "").trim();
          if (currentEvent === "token") {
            fullText += dataStr;
            onToken(dataStr);
          } else if (currentEvent === "done") {
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.citations) citations = parsed.citations;
              if (parsed.cache_hit) cacheHit = true;
            } catch {
              // Ignore non-JSON done event payload
            }
          } else if (currentEvent === "error") {
            throw new Error(`AI generation error: ${dataStr}`);
          }
        }
      }
    }
  } catch (err: unknown) {
    if (abortSignal.aborted) {
      throw new Error("Client aborted query stream");
    }
    throw err;
  }

  const latencyMs = Date.now() - startTime;
  return { fullText, citations, cacheHit, latencyMs };
}

export async function reloadAiRetrieval(): Promise<{ chunks_indexed: number }> {
  const res = await fetch(`${AI_SERVICE_URL}/retrieval/reload`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-api-key": INTERNAL_API_KEY,
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to reload AI retrieval index [${res.status}]`);
  }

  return (await res.json()) as { chunks_indexed: number };
}

export async function checkAdCompliance(adText: string, jurisdiction: string) {
  const res = await fetch(`${AI_SERVICE_URL}/tools/check-compliance`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-api-key": INTERNAL_API_KEY,
    },
    body: JSON.stringify({ ad_text: adText, jurisdiction }),
  });

  if (!res.ok) {
    throw new Error(`Compliance tool call failed [${res.status}]`);
  }

  return await res.json();
}

export async function draftJobAd(params: {
  role: string;
  level: string;
  location: string;
  salary_range: string;
  must_haves: string[];
}) {
  const res = await fetch(`${AI_SERVICE_URL}/tools/draft-ad`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-api-key": INTERNAL_API_KEY,
    },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    throw new Error(`Draft tool call failed [${res.status}]`);
  }

  return await res.json();
}
