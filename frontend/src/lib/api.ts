export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "")

export interface HealthResponse {
  status: "ok"
  service: string
  version: string
  environment: string
}

export interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown

  constructor(
    message: string,
    status: number,
    code = "request_failed",
    details: unknown = null,
  ) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.code = code
    this.details = details
  }
}

interface RequestOptions extends RequestInit {
  accessToken?: string | null
}

export async function apiRequest<T>(
  path: string,
  { accessToken, headers, ...init }: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
  })

  if (!response.ok) {
    let body: ApiErrorBody | null = null
    try {
      body = (await response.json()) as ApiErrorBody
    } catch {
      // Non-JSON error responses still surface as a typed ApiError.
    }
    throw new ApiError(
      body?.error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      body?.error?.code ?? "request_failed",
      body?.error?.details ?? null,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export async function apiStream(
  path: string,
  body: unknown,
  accessToken: string | null,
  onChunk: (chunk: string) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    let bodyText: ApiErrorBody | null = null
    try {
      bodyText = (await response.json()) as ApiErrorBody
    } catch {
      // ignore
    }
    throw new ApiError(
      bodyText?.error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      bodyText?.error?.code ?? "request_failed",
      bodyText?.error?.details ?? null,
    )
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new ApiError("No response body", 500, "no_body")
  }
  const decoder = new TextDecoder()
  let buffer = ""
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue
      const payload = line.slice(6).trim()
      if (!payload) continue
      onChunk(payload)
    }
  }
}