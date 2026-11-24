export class ApiError extends Error {
  status: number;
  body?: unknown;
  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = res.statusText || `HTTP ${res.status}`;
    let body: unknown;
    try {
      body = await res.json();
      const detail = (body as { detail?: unknown } | null)?.detail;
      if (typeof detail === "string") message = detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message, body);
  }
  return (await res.json()) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  return handle<T>(await fetch(path));
}

export async function apiPostForm<T>(path: string, body: FormData): Promise<T> {
  return handle<T>(await fetch(path, { method: "POST", body }));
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return handle<T>(
    await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
}
