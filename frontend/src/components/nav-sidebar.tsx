import {
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Users,
  BriefcaseBusiness,
  Table2,
  AlertTriangle,
  Network,
  GitBranch,
  Sparkles,
  ShieldCheck,
  FileSearch,
  Database,
  BarChart3,
  Activity,
  SlidersHorizontal,
  Bot,
  Zap,
  LifeBuoy,
  type LucideIcon,
} from "lucide-react"
import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "@/lib/auth"
import { BrandLockup } from "@/components/brand-lockup"
import { cn } from "@/lib/utils"

interface NavItem {
  label: string
  icon: LucideIcon
  path: string
  section: string
  roles?: ("administrator" | "analyst" | "investigator")[]
}

const navItems: NavItem[] = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/dashboard", section: "OVERVIEW" },
  { label: "Customers", icon: Users, path: "/customers", section: "FINANCIAL DATA" },
  { label: "Accounts", icon: BriefcaseBusiness, path: "/accounts", section: "FINANCIAL DATA" },
  { label: "Transactions", icon: Table2, path: "/transactions", section: "FINANCIAL DATA" },
  { label: "Fraud alerts", icon: AlertTriangle, path: "/alerts", section: "FRAUD INTELLIGENCE" },
  { label: "Transaction network", icon: Network, path: "/network", section: "FRAUD INTELLIGENCE" },
  { label: "Money flow tracker", icon: GitBranch, path: "/money-flow", section: "FRAUD INTELLIGENCE" },
  { label: "AI detection", icon: Sparkles, path: "/ai-detection", section: "FRAUD INTELLIGENCE" },
  { label: "Account risk profiles", icon: ShieldCheck, path: "/account-risk", section: "FRAUD INTELLIGENCE" },
  { label: "Investigation center", icon: FileSearch, path: "/investigation", section: "INVESTIGATION" },
  { label: "Evidence vault", icon: Database, path: "/evidence", section: "INVESTIGATION" },
  { label: "Fraud analytics", icon: BarChart3, path: "/fraud-analytics", section: "ANALYTICS" },
  { label: "Model performance", icon: Activity, path: "/model-performance", section: "ANALYTICS" },
  { label: "Detection rules", icon: SlidersHorizontal, path: "/detection-rules", section: "ANALYTICS" },
  { label: "AI Copilot", icon: Bot, path: "/ai-copilot", section: "AI & INTEGRATIONS" },
  { label: "MCP integrations", icon: Zap, path: "/mcp", section: "AI & INTEGRATIONS" },
  { label: "Help center", icon: LifeBuoy, path: "/help", section: "SUPPORT" },
]

const groupedItems = navItems.reduce<Record<string, NavItem[]>>((groups, item) => {
  groups[item.section] = [...(groups[item.section] ?? []), item]
  return groups
}, {})

export function NavSidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, hasRole } = useAuth()
  const [collapsed, setCollapsed] = useState(false)

  const visibleNavItems = navItems.filter((item) => {
    if (!item.roles) return true
    return item.roles.some((r) => hasRole(r))
  })

  return (
    <aside className={cn(
      "flex h-screen flex-col border-r border-border bg-card/50 transition-all duration-250",
      collapsed ? "w-20" : "w-64",
    )}>
      <div className="flex items-center justify-between p-4">
        <BrandLockup collapsed={collapsed} />
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden rounded-md p-1 hover:bg-muted sm:block"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto px-3">
{Object.entries(groupedItems).map(([section, items]) => {
            const visible = items.filter((i) =>
              visibleNavItems.find((n) => n.label === i.label && n.path === i.path)
            )
          if (visible.length === 0) return null
          return (
            <div key={section} className="mb-4">
              {!collapsed && (
                <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {section}
                </div>
              )}
              {visible.map((item) => {
                const Icon = item.icon
                const active = location.pathname === item.path
                return (
                  <button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                      active
                        ? "bg-primary/10 text-primary font-medium"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <Icon size={18} />
                    {!collapsed && <span>{item.label}</span>}
                  </button>
                )
              })}
            </div>
          )
        })}
      </nav>
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold">
            {user?.displayName?.charAt(0) ?? "?"}
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{user?.displayName}</p>
              <p className="truncate text-xs capitalize text-muted-foreground">{user?.role}</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}