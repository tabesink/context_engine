import { getAccessToken, resolveApiBase } from "@/lib/api/client";

export function resolveAssetUrl(url?: string | null) {
  if (!url) return null;
  if (/^(https?:|blob:|data:)/i.test(url)) return url;
  const base = resolveApiBase().replace(/\/$/, "");
  const path = url.startsWith("/") ? url : `/${url}`;
  return `${base}${path}`;
}

export async function fetchAuthenticatedAssetBlob(url: string, init: RequestInit = {}) {
  const resolvedUrl = resolveAssetUrl(url);
  if (!resolvedUrl) {
    throw new Error("Asset image request failed: missing URL");
  }
  const token = getAccessToken();
  const headers = new Headers(init.headers ?? {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Accept")) headers.set("Accept", "*/*");

  const response = await fetch(resolvedUrl, {
    ...init,
    credentials: "omit",
    headers,
  });
  if (!response.ok) {
    throw new Error(`Asset image request failed: ${response.status}`);
  }
  return response.blob();
}
