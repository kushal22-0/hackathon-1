import { useState } from "react"
import { Bell, ChevronRight, LogOut, Search, X } from "lucide-react"
import { useAuth } from "@/lib/auth"
import { BrandLockup } from "@/components/brand-lockup"
export function TopBar({user}:{user:{displayName:string;role:string}|null}) {
 const {logout}=useAuth(),[notice,setNotice]=useState(false)
 return <header className="topbar">
  <div className="mobile-brand"><BrandLockup collapsed/></div>
  <div className="breadcrumbs"><span>Workspace</span><ChevronRight size={13}/><strong>Command center</strong></div>
  <div className="top-actions">
   <label className="global-search"><Search size={14}/><input placeholder="Search anything..."/><kbd>⌘ K</kbd></label>
   <button className="icon-button notification-trigger" onClick={()=>setNotice(v=>!v)} aria-label="Notifications"><Bell size={17}/><i/></button>
   <div className="top-divider"/>
   <div className="top-profile"><div className="avatar small">{user?.displayName?.slice(0,2).toUpperCase()||"NG"}</div><div><strong>{user?.displayName||"Demo Analyst"}</strong><span>{user?.role||"analyst"}</span></div></div>
   <button className="icon-button" onClick={()=>void logout()} aria-label="Sign out"><LogOut size={15}/></button>
   {notice&&<div className="notification-popover"><div className="popover-heading"><strong>Notifications</strong><button onClick={()=>setNotice(false)}><X size={13}/></button></div><div className="notification-item"><span className="priority critical">!</span><div><strong>Critical alert detected</strong><small>ALT-2048 · 2 minutes ago</small></div></div><div className="notification-item"><span className="priority high">!</span><div><strong>Case assigned to your queue</strong><small>CASE-0086 · 18 minutes ago</small></div></div><button onClick={()=>setNotice(false)}>Dismiss notifications</button></div>}
  </div>
 </header>
}
