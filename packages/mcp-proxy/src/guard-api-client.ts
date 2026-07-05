/**
 * HTTP client for Tehuti Guard decision API (v2 compile-decision path).
 */

export type GuardDecision =
  | "allow"
  | "deny"
  | "review"
  | "quarantine"
  | "escalate";

export interface GuardDecisionRequest {
  machine_id: string;
  correlation_id?: string;
  actor: { id: string; role: string };
  action: {
    kind: string;
    resource: string;
    risk: "low" | "medium" | "high" | "protected";
    metadata?: Record<string, unknown>;
  };
  raw_model_output?: string;
}

export interface GuardDecisionResponse {
  decision: GuardDecision;
  reason: string;
  correlation_id?: string;
  matched_rules?: string[];
  evidence?: Record<string, unknown>;
}

export async function compileDecision(
  baseUrl: string,
  body: GuardDecisionRequest,
  timeoutMs = 15000
): Promise<GuardDecisionResponse> {
  const url = `${baseUrl.replace(/\/$/, "")}/compile-decision`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Guard API ${res.status}: ${text.slice(0, 500)}`);
    }
    return (await res.json()) as GuardDecisionResponse;
  } finally {
    clearTimeout(timer);
  }
}

export function shouldBlockToolCall(decision: GuardDecision): boolean {
  return decision === "deny" || decision === "quarantine";
}

export function shouldHoldToolCall(decision: GuardDecision): boolean {
  return decision === "review" || decision === "escalate";
}
