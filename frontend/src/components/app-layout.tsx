import { Suspense } from "react"
import { Outlet } from "react-router-dom"
import { useAuth } from "@/lib/auth"
import { NavSidebar } from "@/components/nav-sidebar"
import { TopBar } from "@/components/top-bar"
import { CopilotFAB } from "@/components/copilot-fab"

function AppSkeleton() {
  return (
    <div className="flex min-h-screen">
      <div className="w-64 shrink-0 border-r border-border bg-card/50" />
      <div className="flex-1 p-6">
        <div className="h-12 w-48 animate-pulse rounded bg-muted" />
      </div>
    </div>
  )
}

export function AppLayout() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      <NavSidebar />
      <div className="flex flex-1 flex-col">
        <TopBar user={user} />
        <main className="flex-1">
          <Suspense fallback={<AppSkeleton />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
      <CopilotFAB />
    </div>
  )
}