import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { LayoutDashboard, Users, BriefcaseBusiness, Table2, AlertTriangle, Network, GitBranch, Sparkles, ShieldCheck, FileSearch, Database, BarChart3, Activity, SlidersHorizontal, Bot, Zap, LifeBuoy, ChevronLeft, ChevronRight } from "lucide-react"
import { useAuth } from "@/lib/auth"
import { BrandLockup } from "@/components/brand-lockup"

const groups = [
 ["OVERVIEW", [["Dashboard",LayoutDashboard,"/dashboard"]]],
 ["FINANCIAL DATA", [["Customers",Users,"/customers"],["Accounts",BriefcaseBusiness,"/accounts"],["Transactions",Table2,"/transactions"]]],
 ["FRAUD INTELLIGENCE", [["Fraud alerts",AlertTriangle,"/alerts"],["Transaction network",Network,"/network"],["Money flow tracker",GitBranch,"/money-flow"],["AI detection",Sparkles,"/ai-detection"],["Account risk profiles",ShieldCheck,"/account-risk"]]],
 ["INVESTIGATION", [["Investigation center",FileSearch,"/investigation"],["Evidence vault",Database,"/evidence"]]],
 ["ANALYTICS", [["Fraud analytics",BarChart3,"/fraud-analytics"],["Model performance",Activity,"/model-performance"],["Detection rules",SlidersHorizontal,"/detection-rules"]]],
 ["AI & INTEGRATIONS", [["AI Copilot",Bot,"/ai-copilot"],["MCP integrations",Zap,"/mcp"]]],
 ["SUPPORT", [["Help center",LifeBuoy,"/help"]]],
] as const
export function NavSidebar() {
 const [collapsed,setCollapsed]=useState(false), navigate=useNavigate(), location=useLocation()
 const {user}=useAuth()
 return <aside className={`sidebar ${collapsed?"collapsed":""}`}>
  <button className="collapse-button" onClick={()=>setCollapsed(v=>!v)} aria-label="Toggle sidebar">{collapsed?<ChevronRight size={13}/>:<ChevronLeft size={13}/>}</button>
  <div className="brand-lockup"><BrandLockup collapsed={collapsed}/></div>
  <nav className="side-nav">{groups.map(([section,items])=><div className="nav-group" key={section}>{!collapsed&&<div className="nav-label">{section}</div>}{items.map(([label,Icon,path])=><button key={path} title={collapsed?label:undefined} onClick={()=>navigate(path)} className={`nav-item ${location.pathname===path?"active":""}`}><Icon size={16}/>{!collapsed&&<span>{label}</span>}</button>)}</div>)}</nav>
  <div className="sidebar-footer"><div className="profile-card"><div className="avatar">{user?.displayName?.slice(0,2).toUpperCase()||"NG"}</div>{!collapsed&&<div className="profile-copy"><strong>{user?.displayName||"Demo Analyst"}</strong><span>{user?.role||"analyst"}</span></div>}</div></div>
 </aside>
}
