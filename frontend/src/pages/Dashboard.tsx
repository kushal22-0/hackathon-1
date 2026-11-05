import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { Activity, AlertTriangle, ArrowUpRight, BriefcaseBusiness, Download, Filter, Plus, ShieldCheck, Wallet, ArrowRight, MoreHorizontal, Search, CheckCircle2 } from "lucide-react"
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

const activity = [
  { time: "00:00", normal: 190, suspicious: 12 }, { time: "04:00", normal: 240, suspicious: 18 },
  { time: "08:00", normal: 360, suspicious: 25 }, { time: "12:00", normal: 315, suspicious: 19 },
  { time: "16:00", normal: 470, suspicious: 36 }, { time: "20:00", normal: 390, suspicious: 28 },
  { time: "Now", normal: 520, suspicious: 42 },
]
const risk = [{ name: "High risk", value: 18, color: "#d66d72" }, { name: "Medium risk", value: 32, color: "#dfb85e" }, { name: "Low risk", value: 50, color: "#72b6a2" }]
const alerts = [
  { id: "ALT-2048", name: "Unusual high-value transfer", account: "AC-009184", amount: "$48,500.00", score: 96, risk: "Critical", time: "2 min ago" },
  { id: "ALT-2047", name: "Rapid succession transfers", account: "AC-002761", amount: "$12,800.00", score: 88, risk: "High", time: "8 min ago" },
  { id: "ALT-2046", name: "Multiple accounts / shared device", account: "AC-008231", amount: "$8,240.00", score: 79, risk: "High", time: "14 min ago" },
]
const networkNodes = [
  { x: "15%", y: "50%", label: "AC-1024", kind: "safe" }, { x: "39%", y: "27%", label: "AC-2091", kind: "high" },
  { x: "40%", y: "74%", label: "AC-3108", kind: "medium" }, { x: "67%", y: "27%", label: "AC-4402", kind: "high" },
  { x: "68%", y: "74%", label: "AC-5510", kind: "safe" }, { x: "88%", y: "50%", label: "AC-6012", kind: "high" },
]
function Metric({ icon: Icon, label, value, trend, detail, tone }: { icon: typeof Activity; label: string; value: string; trend: string; detail: string; tone: string }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={17}/></div><div className="metric-label">{label}<span className="trend up"><ArrowUpRight size={12}/>{trend}</span></div><div className="metric-value">{value}</div><div className="metric-detail"><span>{detail}</span><Activity size={14}/></div></div>
}
export default function Dashboard() {
  const [query, setQuery] = useState("")
  const filteredAlerts = useMemo(() => alerts.filter(a => (a.name + a.id + a.account).toLowerCase().includes(query.toLowerCase())), [query])
  return <div className="workspace">
    <div className="page-heading">
      <div><div className="eyebrow"><span className="live-dot"/> LIVE MONITORING · DEMO DATA</div><h1>Command center</h1><p>Your financial security overview, updated just now.</p></div>
      <div className="heading-actions"><button className="secondary-button" onClick={() => window.print()}><Download size={14}/> Export report</button><Link className="primary-button" to="/investigation"><Plus size={15}/> New investigation</Link></div>
    </div>
    <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12,fontSize:10,color:"#66808e"}}><span style={{background:"#d9eee8",padding:"4px 8px",borderRadius:5,color:"#35685d"}}>SYNTHETIC DATA</span> Figures are illustrative and not connected to a live financial institution.</div>
    <div className="metric-grid">
      <Metric icon={Wallet} label="Total transactions" value="2.84M" trend="+12.8%" detail="31,008 processed today" tone="blue"/>
      <Metric icon={AlertTriangle} label="Suspicious alerts" value="1,284" trend="+8.4%" detail="0.045% of total volume" tone="red"/>
      <Metric icon={ShieldCheck} label="High-risk accounts" value="318" trend="+4.2%" detail="42 require attention" tone="amber"/>
      <Metric icon={BriefcaseBusiness} label="Open investigations" value="86" trend="+2.1%" detail="18 due this week" tone="green"/>
    </div>
    <div className="main-grid">
      <section className="panel activity-panel">
        <div className="panel-header"><div><h2>Transaction activity</h2><p>Volume across monitored payment rails</p></div><span className="select-control">Last 24 hours</span></div>
        <div className="chart-legend"><span><i className="legend-blue"/> Normal transactions <strong>2.83M</strong></span><span><i className="legend-red"/> Suspicious <strong>1,284</strong></span></div>
        <div className="activity-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={activity} margin={{top:8,right:8,left:-22,bottom:0}}><defs><linearGradient id="normalFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7fa6b8" stopOpacity={0.28}/><stop offset="95%" stopColor="#7fa6b8" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#dce8ed" strokeDasharray="3 4" vertical={false}/><XAxis dataKey="time" tick={{fontSize:9,fill:"#66808e"}} axisLine={false} tickLine={false}/><YAxis tick={{fontSize:9,fill:"#66808e"}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{borderRadius:8,border:"1px solid #c7d9e1",fontSize:11}}/><Area type="monotone" dataKey="normal" stroke="#6f9eaf" strokeWidth={2} fill="url(#normalFill)"/><Area type="monotone" dataKey="suspicious" stroke="#d66d72" strokeWidth={2} fill="none"/></AreaChart></ResponsiveContainer></div>
      </section>
      <section className="panel">
        <div className="panel-header"><div><h2>Risk distribution</h2><p>Across all scored transactions</p></div><button className="more-button" aria-label="More options"><MoreHorizontal size={18}/></button></div>
        <div className="donut-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={risk} dataKey="value" nameKey="name" innerRadius={57} outerRadius={78} paddingAngle={3} stroke="none">{risk.map((r)=><Cell key={r.name} fill={r.color}/>)}</Pie><Tooltip formatter={(v)=>[`${v}%`,"Share"]}/></PieChart></ResponsiveContainer><div className="donut-center"><strong>12.4K</strong><span>total alerts</span></div></div>
        <div className="risk-legend">{risk.map(r=><div key={r.name}><span><i style={{background:r.color}}/>{r.name}</span><strong>{r.value}%</strong></div>)}</div>
      </section>
    </div>
    <div className="lower-grid">
      <section className="panel alerts-panel">
        <div className="panel-header"><div><h2>Recent fraud alerts</h2><p>Prioritized signals requiring analyst attention</p></div><Link to="/alerts" className="text-button">View all <ArrowRight size={13}/></Link></div>
        <div className="table-toolbar"><label className="table-search"><Search size={13}/><input placeholder="Search alerts..." value={query} onChange={e=>setQuery(e.target.value)}/></label><button className="filter-button"><Filter size={12}/> Filter</button></div>
        <div className="data-table-wrap"><table><thead><tr><th>Alert / account</th><th>Amount</th><th>Risk score</th><th>Priority</th><th>Detected</th></tr></thead><tbody>{filteredAlerts.map(a=><tr key={a.id} onClick={()=>window.location.assign("/alerts")}><td><strong>{a.name}</strong><small>{a.id} · {a.account}</small></td><td className="amount-cell">{a.amount}</td><td><span className={`score ${a.risk==="Critical"?"critical":"high"}`}>{a.score}/100</span></td><td><span className={`priority ${a.risk==="Critical"?"critical":"high"}`}>{a.risk}</span></td><td>{a.time}</td></tr>)}</tbody></table></div>
      </section>
      <section className="panel">
        <div className="panel-header"><div><h2>Investigation pulse</h2><p>Current workload overview</p></div><Link to="/investigation" className="text-button">Open center <ArrowRight size={13}/></Link></div>
        <div className="case-list">
          <div className="case-item"><div className="case-symbol"><BriefcaseBusiness size={16}/></div><div className="case-copy"><strong>Open cases</strong><span>Awaiting initial review</span></div><b>42</b></div>
          <div className="case-item"><div className="case-symbol"><Activity size={16}/></div><div className="case-copy"><strong>In progress</strong><span>Assigned to investigators</span></div><b>28</b></div>
          <div className="case-item"><div className="case-symbol"><CheckCircle2 size={16}/></div><div className="case-copy"><strong>Resolved this week</strong><span>Human-reviewed outcomes</span></div><b>16</b></div>
        </div>
        <Link to="/investigation" className="outline-wide">Review investigation queue <ArrowRight size={13}/></Link>
      </section>
    </div>
    <div className="bottom-grid">
      <section className="panel network-panel">
        <div className="panel-header"><div><h2>Transaction network snapshot</h2><p>Connected accounts around a flagged transfer</p></div><Link to="/network" className="text-button">Explore network <ArrowRight size={13}/></Link></div>
        <div className="network-stage"><div className="network-grid"/><div className="connection c1"/><div className="connection c2"/><div className="connection c3"/><div className="connection c4"/>{networkNodes.map(n=><div key={n.label} className={`network-node ${n.kind}`} style={{left:n.x,top:n.y}}><span><Wallet size={11}/></span><small>{n.label}</small></div>)}</div>
        <div className="network-summary"><span>6 linked accounts</span><span>·</span><span>12 transfers in cluster</span><span>·</span><strong>3 high-risk nodes</strong></div>
      </section>
      <section className="panel">
        <div className="panel-header"><div><h2>Platform health</h2><p>Local demonstration environment</p></div><span className="health-check"><CheckCircle2 size={13}/> Ready</span></div>
        <div className="health-list"><div className="health-item"><span>API service</span><strong>Demo mode</strong></div><div className="health-item"><span>Detection engine</span><strong>Rules + Isolation Forest</strong></div><div className="health-item"><span>Database</span><strong>In-memory / optional Supabase</strong></div><div className="health-item"><span>AI Copilot / MCP</span><strong>Demo / not connected</strong></div></div>
        <div className="health-footer">Alerts indicate potential risk, not confirmed fraud.</div>
      </section>
    </div>
  </div>
}
