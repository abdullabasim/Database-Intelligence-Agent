/**
 * API client for the Database Intelligence Agent Backend.
 * Handles authentication headers and provides typed methods for all endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  auth?: {
    email?: string;
    password?: string;
    token?: string; // base64 encoded credentials
  };
}

class ApiClient {
  private getAuthHeader(auth?: FetchOptions["auth"]): Record<string, string> {
    if (!auth) return {};
    
    if (auth.token) {
      return { Authorization: `Basic ${auth.token}` };
    }
    
    if (auth.email && auth.password) {
      const token = btoa(`${auth.email}:${auth.password}`);
      return { Authorization: `Basic ${token}` };
    }
    
    return {};
  }

  async request<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { auth, ...rest } = options;
    const headers = {
      "Content-Type": "application/json",
      ...this.getAuthHeader(auth),
      ...rest.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...rest,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    if (response.status === 204) return {} as T;
    return response.json();
  }

  // Auth
  register(data: any) {
    return this.request("/auth/register", { method: "POST", body: JSON.stringify(data) });
  }

  login(auth: FetchOptions["auth"]) {
    return this.request("/auth/login", { method: "POST", auth });
  }

  // Databases
  getDatabases(auth: FetchOptions["auth"], limit = 10, offset = 0) {
    return this.request(`/databases?limit=${limit}&offset=${offset}`, { auth });
  }

  createDatabase(data: any, auth: FetchOptions["auth"]) {
    return this.request("/databases", { 
      method: "POST", 
      body: JSON.stringify(data), 
      auth 
    });
  }

  updateDatabase(id: string, data: any, auth: FetchOptions["auth"]) {
    return this.request(`/databases/${id}`, { 
      method: "PUT", 
      body: JSON.stringify(data), 
      auth 
    });
  }

  deleteDatabase(id: string, auth: FetchOptions["auth"]) {
    return this.request(`/databases/${id}`, { method: "DELETE", auth });
  }

  testConnection(id: string, auth: FetchOptions["auth"]) {
    return this.request(`/databases/${id}/test-connection`, { method: "POST", auth });
  }

  // MDL
  getLatestMDL(databaseId: string, auth: FetchOptions["auth"]) {
    return this.request(`/mdl/latest?database_id=${databaseId}`, { auth });
  }

  async askQuestion(data: { question: string; database_id: string }, auth: FetchOptions["auth"]) {
    return this.request<any>("/agent/ask", { 
      method: "POST", 
      body: JSON.stringify(data), 
      auth 
    });
  }

  async streamAskQuestion(
    data: { question: string; database_id: string },
    auth: { token?: string },
    onEvent: (event: string, data: any) => void
  ) {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...this.getAuthHeader(auth),
    };

    const response = await fetch(`${API_BASE_URL}/agent/ask/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Streaming request failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const jsonText = line.substring(6).trim();
            if (!jsonText) continue;
            const parsed = JSON.parse(jsonText);
            onEvent(parsed.event, parsed.data);
          } catch (e) {
            console.error("Error parsing SSE line:", line, e);
          }
        }
      }
    }
  }

  refreshMDL(data: { database_id: string; name: string }, auth: FetchOptions["auth"]) {
    return this.request("/mdl/refresh", { 
      method: "POST", 
      body: JSON.stringify(data), 
      auth 
    });
  }
}

export const api = new ApiClient();
