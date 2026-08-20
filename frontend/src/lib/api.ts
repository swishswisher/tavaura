import { getToken, removeToken } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5225";

type ApiError = {
  message?: string;
};

type ApiRequestOptions = {
  authenticated?: boolean;
  headers?: HeadersInit;
};

async function parseJson<TResponse>(res: Response): Promise<TResponse | ApiError | null> {
  try {
    return (await res.json()) as TResponse;
  } catch {
    return null;
  }
}

function getErrorMessage(data: ApiError | null, status: number) {
  return data?.message ?? `Request failed with status ${status}.`;
}

function redirectToAdminLogin() {
  if (typeof window === "undefined") {
    return;
  }

  if (window.location.pathname === "/admin/login") {
    return;
  }

  window.location.assign("/admin/login");
}

function handleMissingToken(): never {
  removeToken();
  redirectToAdminLogin();
  throw new Error("Authentication required. Please sign in again.");
}

function getRequiredToken() {
  const token = getToken();

  if (!token) {
    handleMissingToken();
  }

  return token;
}

function handleUnauthorized(): never {
  removeToken();
  redirectToAdminLogin();
  throw new Error("Your session expired. Please sign in again.");
}

export async function postJson<TRequest, TResponse>(
  path: string,
  body: TRequest,
  options: ApiRequestOptions = {}
): Promise<TResponse> {
  const url = `${API_BASE_URL}${path}`;
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  if (options.authenticated) {
    headers.set("Authorization", `Bearer ${getRequiredToken()}`);
  }

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const data = await parseJson<TResponse>(res);

  if (options.authenticated && res.status === 401) {
    handleUnauthorized();
  }

  if (!res.ok) {
    throw new Error(getErrorMessage(data as ApiError | null, res.status));
  }

  return data as TResponse;
}

export async function authenticatedFetch<TResponse>(
  path: string,
  init: RequestInit = {}
): Promise<TResponse> {
  const url = `${API_BASE_URL}${path}`;
  const headers = new Headers(init.headers);
  const token = getRequiredToken();
  headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(url, {
    ...init,
    headers,
  });
  const data = await parseJson<TResponse>(res);

  if (res.status === 401) {
    handleUnauthorized();
  }

  if (!res.ok) {
    throw new Error(getErrorMessage(data as ApiError | null, res.status));
  }

  return data as TResponse;
}
