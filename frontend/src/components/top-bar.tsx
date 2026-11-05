import { Bell, ChevronRight, LogOut, Search } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/lib/auth"
import { BrandLockup } from "@/components/brand-lockup"
import { cn } from "@/lib/utils"

interface TopBarProps {
  user: { displayName: string; role: string } | null
}

export function TopBar({ user }: TopBarProps) {
  const navigate = useNavigate()
  const { logout } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between border-b border-border px-6">
      <div className="flex items-center gap-3 sm:hidden">
        <BrandLockup collapsed={true} />
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Workspace</span>
        <ChevronRight size={14} />
        <span className="text-foreground font-medium">Dashboard</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative hidden sm:block">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search anything..."
            className="h-9 w-64 rounded-md border border-input bg-background pl-9 pr-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
        <button className="relative rounded-md p-2 hover:bg-muted">
          <Bell size={18} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-red-500" />
        </button>
        <div className="flex items-center gap-2 rounded-md border border-border px-2 py-1">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold">
            {user?.displayName?.charAt(0) ?? "?"}
          </div>
          <div className="hidden flex-col sm:flex">
            <span className="text-xs font-medium">{user?.displayName}</span>
            <span className="text-[10px] capitalize text-muted-foreground">{user?.role}</span>
          </div>
        </div>
        <button
          onClick={() => void logout()}
          className="rounded-md p-2 text-muted-foreground hover:bg-muted"
          aria-label="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}