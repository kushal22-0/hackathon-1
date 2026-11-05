import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { supabase, isSupabaseConfigured } from "@/lib/supabase"

export type UserRole = "administrator" | "analyst" | "investigator"

export interface AuthUser {
  id: string
  email: string
  role: UserRole
  displayName: string
}

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  hasRole: (...roles: UserRole[]) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

const ROLE_COOKIE = "nexguard_role"
const USER_COOKIE = "nexguard_user"

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(";").shift() ?? null
  return null
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split(".")[1]
    if (!payload) return null
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/")
    const decoded = atob(normalized)
    return JSON.parse(decoded) as Record<string, unknown>
  } catch {
    return null
  }
}

function mapRole(role: unknown): UserRole {
  if (role === "investigator") return "investigator"
  if (role === "analyst") return "analyst"
  return "administrator"
}

function buildAuthUser(payload: Record<string, unknown>, fallbackEmail: string): AuthUser {
  const role = mapRole(payload.role ?? payload.user_role)
  const email =
    (typeof payload.email === "string" && payload.email) || fallbackEmail
  const displayName =
    (typeof payload.name === "string" && payload.name) ||
    (typeof payload.full_name === "string" && payload.full_name) ||
    email.split("@")[0] ||
    "User"
  return {
    id: typeof payload.sub === "string" ? payload.sub : typeof payload.user_id === "string" ? payload.user_id : "",
    email,
    role,
    displayName,
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const restoreSession = useCallback(async () => {
    if (!isSupabaseConfigured || !supabase) {
      // Fall back to cookie-based session for local/demo deployments.
      const cookieRole = readCookie(ROLE_COOKIE)
      const cookieUser = readCookie(USER_COOKIE)
      if (cookieRole && cookieUser) {
        try {
          const payload = JSON.parse(cookieUser) as Record<string, unknown>
          setUser(buildAuthUser(payload, ""))
          return
        } catch {
          // ignore
        }
      }
      // Default: treat as administrator for local development.
      const devUser: AuthUser = {
        id: "dev-admin",
        email: "admin@nexguard.ai",
        role: "administrator",
        displayName: "Administrator",
      }
      setUser(devUser)
      return
    }

    try {
      const { data, error: sessionError } = await supabase.auth.getUser()
      if (sessionError) {
        setError(sessionError.message)
        setUser(null)
        return
      }
      if (data.user) {
        const payload = decodeJwtPayload(data.session?.access_token ?? "")
        const authUser = buildAuthUser(
          payload ?? {},
          data.user.email ?? "",
        )
        authUser.id = data.user.id
        setUser(authUser)
      } else {
        setUser(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth error")
      setUser(null)
    }
  }, [])

  useEffect(() => {
    let mounted = true
    setLoading(true)
    restoreSession().finally(() => {
      if (mounted) setLoading(false)
    })
    return () => {
      mounted = false
    }
  }, [restoreSession])

  const login = useCallback(
    async (email: string, password: string) => {
      setError(null)
      if (!isSupabaseConfigured || !supabase) {
        // Cookie-based local auth.
        const role: UserRole = email.toLowerCase().includes("inv") ? "investigator" : "administrator"
        const payload = { sub: `local-${email}`, email, role, name: email.split("@")[0] }
        document.cookie = `${ROLE_COOKIE}=${role}; path=/; max-age=86400`
        document.cookie = `${USER_COOKIE}=${encodeURIComponent(JSON.stringify(payload))}; path=/; max-age=86400`
        setUser(buildAuthUser(payload, email))
        return
      }
      const { data, error: authError } = await supabase.auth.signUp({ email, password })
      if (authError) {
        setError(authError.message)
        return
      }
      if (data.session?.access_token) {
        const payload = decodeJwtPayload(data.session.access_token)
        const authUser = buildAuthUser(payload ?? {}, email)
        authUser.id = data.user?.id ?? authUser.id
        setUser(authUser)
      }
    },
    [],
  )

  const logout = useCallback(async () => {
    setError(null)
    if (isSupabaseConfigured && supabase) {
      await supabase.auth.signOut()
    }
    document.cookie = `${ROLE_COOKIE}=; path=/; max-age=0`
    document.cookie = `${USER_COOKIE}=; path=/; max-age=0`
    setUser(null)
  }, [])

  const hasRole = useCallback(
    (...roles: UserRole[]) => {
      if (!user) return false
      return roles.includes(user.role)
    },
    [user],
  )

  const value = useMemo(
    () => ({ user, loading, error, login, logout, hasRole }),
    [user, loading, error, login, logout, hasRole],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}