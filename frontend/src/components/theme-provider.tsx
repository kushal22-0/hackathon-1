import * as React from "react"

type Theme = "dark" | "light" | "system"

interface ThemeContextValue {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: "dark" | "light"
}

const ThemeContext = React.createContext<ThemeContextValue | undefined>(undefined)

function getInitialTheme(): Theme {
  if (typeof localStorage !== "undefined") {
    const stored = localStorage.getItem("nexguard-theme") as Theme | null
    if (stored === "dark" || stored === "light" || stored === "system") return stored
  }
  return "dark"
}

function applyTheme(theme: Theme, resolved: "dark" | "light") {
  if (typeof document === "undefined") return
  const root = document.documentElement
  root.classList.toggle("dark", resolved === "dark")
  root.classList.toggle("light", resolved === "light")
}

function resolveTheme(theme: Theme): "dark" | "light" {
  if (theme === "system") {
    if (typeof window === "undefined") return "dark"
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  }
  return theme
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = React.useState<Theme>(getInitialTheme)
  const [resolvedTheme, setResolvedTheme] = React.useState<"dark" | "light">(() =>
    resolveTheme(getInitialTheme()),
  )

  React.useEffect(() => {
    const resolved = resolveTheme(theme)
    setResolvedTheme(resolved)
    applyTheme(theme, resolved)
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("nexguard-theme", theme)
    }
  }, [theme])

  React.useEffect(() => {
    if (theme !== "system" || typeof window === "undefined") return
    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const handler = (e: MediaQueryListEvent) => {
      const resolved = e.matches ? "dark" : "light"
      setResolvedTheme(resolved)
      applyTheme("system", resolved)
    }
    media.addEventListener("change", handler)
    return () => media.removeEventListener("change", handler)
  }, [theme])

  const setTheme = React.useCallback((next: Theme) => {
    setThemeState(next)
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = React.useContext(ThemeContext)
  if (!context) throw new Error("useTheme must be used within ThemeProvider")
  return context
}