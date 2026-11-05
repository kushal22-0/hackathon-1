import { useNavigate } from "react-router-dom"
import { Bell, ChevronRight, LogOut, Search } from "lucide-react"
import { useAuth } from "@/lib/auth"
import { BrandLockup } from "@/components/brand-lockup"
export function TopBar({user}:{user:{displayName:string;role:string}|null}) {
 const {logout}=useAuth(),navigate=useNavigate()
 return <header className="topbar"><div className="mobile-brand"><BrandLockup collapsed/></div><div className="breadcrumbs"><span>Workspace</span><ChevronRight size={13}/><strong>NexGuard</strong></div><div className="top-actions"><label className="global-search"><Search size={14}/><input placeholder="Search transactions and alerts..." onKeyDown={e=>{if(e.key==="Enter")navigate("/transactions")}}/><kbd>Enter</kbd></label><button className="icon-button" onClick={()=>navigate("/alerts")} aria-label="Open fraud alerts"><Bell size={17}/></button><div className="top-divider"/><div className="top-profile"><div className="avatar small">{user?.displayName?.slice(0,2).toUpperCase()||"NG"}</div><div><strong>{user?.displayName||"Analyst"}</strong><span>{user?.role||"analyst"}</span></div></div><button className="icon-button" onClick={()=>void logout()} aria-label="Sign out"><LogOut size={15}/></button></div></header>
}