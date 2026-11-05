import { useCallback, useEffect, useRef, useState } from "react"

import { API_BASE_URL, type HealthResponse } from "@/lib/api"

export type BackendStatus = "checking" | "online" | "offline"

interface BackendHealthState {
  status: BackendStatus
  data: HealthResponse | null
  latencyMs: number | null
  error: string | null
  refresh: () => Promise<void>
}

export function useBackendHealth(): BackendHealthState {
  const [status, setStatus] = useState<BackendStatus>("checking")
  const [data, setData] = useState<HealthResponse | null>(null)
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const mounted = useRef(true)

  const refresh = useCallback(async () => {
    setStatus("checking")
    setError(null)
    const startedAt = performance.now()

    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        headers: { Accept: "application/json" },
      })
      if (!response.ok) {
        throw new Error(`Health check returned ${response.status}`)
      }
      const body = (await response.json()) as HealthResponse
      if (!mounted.current) return
      setData(body)
      setLatencyMs(Math.round(performance.now() - startedAt))
      setStatus(body.status === "ok" ? "online" : "offline")
    } catch (err) {
      if (!mounted.current) return
      setData(null)
      setLatencyMs(null)
      setStatus("offline")
      setError(
        err instanceof Error ? err.message : "Unable to reach the FraudNet API",
      )
    }
  }, [])

  useEffect(() => {
    mounted.current = true
    void refresh()

    const timer = window.setInterval(() => {
      void refresh()
    }, 30_000)

    return () => {
      mounted.current = false
      window.clearInterval(timer)
    }
  }, [refresh])

  return { status, data, latencyMs, error, refresh }
}
