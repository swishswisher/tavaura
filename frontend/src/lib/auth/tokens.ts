"use client";

const TOKEN_STORAGE_KEY = "tavaura_admin_access_token";

function getStorage() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function saveToken(token: string) {
  const normalizedToken = token.trim();
  const storage = getStorage();

  if (!normalizedToken) {
    throw new Error("Login did not return a usable access token.");
  }

  if (!storage) {
    throw new Error("Unable to save your login session in this browser.");
  }

  storage.setItem(TOKEN_STORAGE_KEY, normalizedToken);
}

export function getToken() {
  const storage = getStorage();

  if (!storage) {
    return null;
  }

  const token = storage.getItem(TOKEN_STORAGE_KEY)?.trim();
  return token || null;
}

export function removeToken() {
  const storage = getStorage();

  if (!storage) {
    return;
  }

  storage.removeItem(TOKEN_STORAGE_KEY);
}

export function isLoggedIn() {
  return Boolean(getToken());
}
