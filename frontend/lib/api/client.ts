const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/?$/, "") || "http://localhost:8000/api/v1";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export async function request<T>(
  path: string,
  options: { method?: HttpMethod; body?: any; token?: string } = {}
): Promise<T> {
  const { method = "GET", body, token } = options;
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: method === "GET" ? "no-store" : "no-cache"
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let message = text || `Request failed (${res.status})`;
    try {
      const json = text ? JSON.parse(text) : null;
      if (json?.detail) {
        if (Array.isArray(json.detail)) {
          // Map technical validation messages to user-friendly ones
          message = json.detail
            .map((err: any) => {
              const msg = err.msg || '';
              
              // Map common technical messages to user-friendly ones
              if (msg.includes('An email address must have an @-sign')) {
                return 'Please enter a valid email address (missing @ symbol)';
              }
              if (msg.includes('String should have at least 8 characters')) {
                return 'Password must be at least 8 characters long';
              }
              if (msg.includes('value is not a valid email address')) {
                return 'Please enter a valid email address';
              }
              
              // Return original message if no mapping found
              return msg;
            })
            .join('\n');
        } else {
          message = typeof json.detail === "string" ? json.detail : JSON.stringify(json.detail);
        }
      }
    } catch {
      // keep message as text
    }
    throw new Error(message);
  }

  // 204 No Content has no body; calling .json() would throw
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}