const ACCESS_TOKEN_KEY = "context_engine_access_token";

export class APIError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.body = body;
  }
}

const DEFAULT_API_HOST = "127.0.0.1";
const DEFAULT_API_PORT = "8010";

function normalizeBaseUrl(url: string) {
  return url.trim().replace(/\/+$/, "");
}

export function resolveApiBase() {
  const configured =
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    process.env.NEXT_PUBLIC_BACKEND_BASE_URL?.trim();
  if (configured) {
    return normalizeBaseUrl(configured);
  }

  const port = process.env.NEXT_PUBLIC_API_PORT?.trim() || DEFAULT_API_PORT;
  return `http://${DEFAULT_API_HOST}:${port}`;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

export function hasAccessToken() {
  return Boolean(getAccessToken());
}

type RequestOptions = RequestInit & {
  auth?: boolean;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = `${resolveApiBase()}${path.startsWith("/") ? path : `/${path}`}`;
  const token = options.auth === false ? null : getAccessToken();
  const headers = new Headers(options.headers ?? {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const response = await fetch(url, {
    ...options,
    credentials: "omit",
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await readBody(response);
  if (!response.ok) {
    const detail = extractDetail(body) || `${response.status} ${response.statusText}`;
    throw new APIError(detail, response.status, body);
  }
  return body as T;
}

async function readBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }
  const text = await response.text();
  return text || null;
}

function extractDetail(body: unknown) {
  if (typeof body === "string") return body;
  if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
    return body.detail;
  }
  return "";
}
