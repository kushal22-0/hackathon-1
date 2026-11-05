import { Suspense } from "react"
import { Outlet } from "react-router-dom"
import { useAuth } from "@/lib/auth"
import { NavSidebar } from "@/components/nav-sidebar"
import { TopBar } from "@/components/top-bar"
import { CopilotFAB } from "@/components/copilot-fab"

export function AppLayout() {
  const { user } = useAuth()
  return <div className="app-shell">
    <NavSidebar />
    <div className="main-content">
      <TopBar user={user} />
      <main><Suspense fallback={<div className="workspace">Loading workspace…</div>}><Outlet /></Suspense></main>
    </div>
    <CopilotFAB />
  </div>
}
