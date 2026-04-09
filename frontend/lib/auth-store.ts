/**
 * Utility for managing authentication state in the browser.
 * Uses cookies to store the base64-encoded credentials.
 */

import { parse, serialize } from "cookie";

const COOKIE_NAME = "auth_token";

export interface UserSession {
  email: string;
  token: string; // base64(email:password)
}

export const authStore = {
  saveSession(session: UserSession) {
    const cookie = serialize(COOKIE_NAME, JSON.stringify(session), {
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 1 week
      sameSite: "strict",
      secure: process.env.NODE_ENV === "production",
    });
    document.cookie = cookie;
  },

  getSession(): UserSession | null {
    if (typeof document === "undefined") return null;
    const cookies = parse(document.cookie);
    const sessionStr = cookies[COOKIE_NAME];
    if (!sessionStr) return null;
    try {
      return JSON.parse(sessionStr);
    } catch {
      return null;
    }
  },

  clearSession() {
    const cookie = serialize(COOKIE_NAME, "", {
      path: "/",
      maxAge: -1,
    });
    document.cookie = cookie;
  },
};
