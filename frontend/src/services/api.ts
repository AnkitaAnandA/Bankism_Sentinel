export type Verdict = "ALLOW" | "BLOCK" | "REVIEW";
export type Risk = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Category =
  | "NONE"
  | "DIRECT_INJECTION"
  | "POLICY_OVERRIDE"
  | "ROLE_SPOOFING"
  | "ROLEPLAY_JAILBREAK"
  | "OBFUSCATION"
  | "ENCODED_PAYLOAD"
  | "MEMO_INJECTION"
  | "DATA_EXFILTRATION"
  | "CROSS_TURN_MANIPULATION"
  | "REPLAY"
  | "PARAMETER_TAMPERING"
  | "UNKNOWN_BENEFICIARY"
  | "POLICY_VIOLATION"
  | "CLASSIFIER_UNAVAILABLE"
  | "AMBIGUOUS_INTENT";
export interface Transaction {
  amount_minor: number;
  currency: string;
  beneficiary_name: string;
  masked_account: string;
  source_account: string;
  expires_at: number;
  integrity_tag: string;
  status:
    | "DRAFT"
    | "VALIDATED"
    | "PENDING_CONFIRMATION"
    | "CONFIRMED"
    | "EXECUTED"
    | "BLOCKED"
    | "CANCELLED"
    | "EXPIRED";
  transaction_id: string | null;
}
export interface Account {
  id: string;
  name: string;
  masked_account: string;
  balance_minor: number;
  currency: string;
}
export interface History {
  id: string;
  amount_minor: number;
  currency: string;
  beneficiary_name: string;
  timestamp: number;
}
export interface Event {
  request_id: string;
  category: Category;
  risk: Risk;
  verdict: Verdict;
  evidence: string;
  timestamp: number;
}
export interface Evaluation {
  configuration: string;
  dataset_size: number;
  recall: number;
  false_positive_rate: number;
  unauthorized_transfers: number;
  schema_validity: number;
  valid_transfer_completion: number;
  duplicate_prevention: number;
  tamper_rejection: number;
}
export interface Result {
  request_id: string;
  verdict: Verdict;
  approved: boolean;
  risk_level: Risk;
  threat_category: Category;
  detected_intent:
    | "BALANCE"
    | "HISTORY"
    | "TRANSFER"
    | "INFORMATIONAL"
    | "UNKNOWN";
  reason: string;
  policy_checks: {
    injection_safe: boolean;
    account_authorized: boolean;
    transaction_valid: boolean;
  };
  requires_confirmation: boolean;
  execution_allowed: boolean;
  transaction: Transaction | null;
  intent_id: string | null;
  classifier_mode: string;
  findings: {
    category: Category;
    risk: Risk;
    evidence: string;
    view: string;
  }[];
  accounts: Account[];
  history: History[];
  events: Event[];
  metrics: {
    total: number;
    allow: number;
    block: number;
    review: number;
    categories: Record<string, number>;
  } | null;
  evaluation: Evaluation[];
  demo_token: string | null;
}
const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
let token = "";
export function configured() {
  return Boolean(base);
}
export const money = (value: number, currency = "INR") =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency }).format(
    value / 100,
  );
export async function api(path: string, body?: unknown): Promise<Result> {
  if (!base)
    throw new Error(
      "Set VITE_API_BASE_URL to the backend URL, then rebuild the frontend.",
    );
  try {
    const response = await fetch(base + path, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      signal: AbortSignal.timeout(15000),
    });
    const result: Result = await response.json();
    if (response.status >= 500)
      throw new Error(
        result.reason || "Secure server temporarily unavailable. Please retry.",
      );
    return result;
  } catch (error) {
    if (
      error instanceof Error &&
      !["TypeError", "TimeoutError", "AbortError"].includes(error.name)
    )
      throw error;
    throw new Error(
      "The secure server is waking up or temporarily unreachable. Please retry shortly.",
    );
  }
}
export async function login(user: string): Promise<void> {
  token = "";
  const result = await api("/api/demo/session/" + user, {});
  if (!result.demo_token) throw new Error(result.reason);
  token = result.demo_token;
}
export async function wake(): Promise<void> {
  for (let i = 0; i < 5; i++) {
    try {
      await api("/health");
      return;
    } catch (error) {
      if (i === 4) throw error;
      await new Promise((r) => setTimeout(r, Math.min(1000 * 2 ** i, 8000)));
    }
  }
}
