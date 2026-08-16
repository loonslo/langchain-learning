const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");
const TOKEN_KEY = "day79_access_token";

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getAccessToken() {
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function saveAccessToken(token) {
  const normalized = token.trim();
  if (normalized) window.localStorage.setItem(TOKEN_KEY, normalized);
  else window.localStorage.removeItem(TOKEN_KEY);
  return normalized;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("无法连接 Day78 API，请确认后端已启动。", 0);
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : `请求失败（${response.status}）`;
    throw new ApiError(detail, response.status);
  }
  return payload;
}

export function health() {
  return request("/health");
}

export function chat({ question, sessionId, orderId, idempotencyKey }) {
  return request("/chat", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ question, session_id: sessionId, order_id: orderId }),
  });
}

export function submitFeedback({ traceId, rating, reason }) {
  return request("/feedback", {
    method: "POST",
    body: JSON.stringify({ trace_id: traceId, rating, reason }),
  });
}
