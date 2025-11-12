// Centralized API base URL for the frontend
// Uses NEXT_PUBLIC_API_BASE_URL if provided; otherwise matches the current hostname
// This ensures cookies are same-site in local dev (localhost vs 127.0.0.1)
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:8000`;


