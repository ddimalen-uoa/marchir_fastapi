const developmentApiBaseUrl = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");

// Production is served by nginx, which proxies same-origin /api requests.
export const API_BASE_URL = import.meta.env.PROD ? "" : developmentApiBaseUrl;

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}
