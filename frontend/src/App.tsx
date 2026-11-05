import { useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  Bot,
  BriefcaseBusiness,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  Download,
  FileSearch,
  Filter,
  GitBranch,
  Globe2,
  LayoutDashboard,
  LifeBuoy,
  LogOut,
  Menu,
  MessageSquareText,
  MoreHorizontal,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Table2,
  Users,
  X,
  Zap,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import './App.css';

type NavItem = { label: string; icon: typeof LayoutDashboard; section: string };
type AlertItem = { id: string; transaction: string; account: string; amount: string; score: number; reason: string; time: string; risk: 'Critical' | 'High' | 'Medium' };

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, section: 'OVERVIEW' },
  { label: 'Customers', icon: Users, section: 'FINANCIAL DATA' },
  { label: 'Accounts', icon: BriefcaseBusiness, section: 'FINANCIAL DATA' },
  { label: 'Transactions', icon: Table2, section: 'FINANCIAL DATA' },
  { label: 'Fraud alerts', icon: AlertTriangle, section: 'FRAUD INTELLIGENCE' },
  { label: 'Transaction network', icon: Network, section: 'FRAUD INTELLIGENCE' },
  { label: 'Money flow tracker', icon: GitBranch, section: 'FRAUD INTELLIGENCE' },
  { label: 'AI detection', icon: Sparkles, section: 'FRAUD INTELLIGENCE' },
  { label: 'Account risk profiles', icon: ShieldCheck, section: 'FRAUD INTELLIGENCE' },
  { label: 'Investigation center', icon: FileSearch, section: 'INVESTIGATION' },
  { label: 'Evidence vault', icon: Database, section: 'INVESTIGATION' },
  { label: 'Fraud analytics', icon: BarChart3, section: 'ANALYTICS' },
  { label: 'Model performance', icon: Activity, section: 'ANALYTICS' },
  { label: 'Detection rules', icon: SlidersHorizontal, section: 'ANALYTICS' },
  { label: 'AI Copilot', icon: Bot, section: 'AI & INTEGRATIONS' },
  { label: 'MCP integrations', icon: Zap, section: 'AI & INTEGRATIONS' },
];

const activityData = [
  { name: '00:00', normal: 240, suspicious: 24 }, { name: '04:00', normal: 310, suspicious: 31 },
  { name: '08:00', normal: 450, suspicious: 46 }, { name: '12:00', normal: 390, suspicious: 42 },
  { name: '16:00', normal: 520, suspicious: 67 }, { name: '20:00', normal: 430, suspicious: 52 },
  { name: 'Now', normal: 590, suspicious: 71 },
];

const alerts: AlertItem[] = [
  { id: 'ALT-28491', transaction: 'TXN-8F21A', account: 'AC-009184', amount: '$48,920.00', score: 94, reason: 'Rapid cross-border movement', time: '8 min ago', risk: 'Critical' },
  { id: 'ALT-28490', transaction: 'TXN-4C72B', account: 'AC-004671', amount: '$12,480.50', score: 87, reason: 'Unusual transaction frequency', time: '23 min ago', risk: 'High' },
  { id: 'ALT-28489', transaction: 'TXN-9D13C', account: 'AC-011203', amount: '$9,780.00', score: 78, reason: 'New device and location', time: '41 min ago', risk: 'High' },
  { id: 'ALT-28488', transaction: 'TXN-2A98E', account: 'AC-002814', amount: '$4,250.75', score: 65, reason: 'Velocity threshold exceeded', time: '1 hr ago', risk: 'Medium' },
];

const distribution = [
  { name: 'High risk', value: 18, color: '#f05454' },
  { name: 'Medium risk', value: 32, color: '#f1b84b' },
  { name: 'Low risk', value: 50, color: '#30c29a' },
];

function App() {
  const [activeNav, setActiveNav] = useState('Dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [range, setRange] = useState('Last 24 hours');
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);
  const [toast, setToast] = useState('');

  const groupedItems = useMemo(() => navItems.reduce<Record<string, NavItem[]>>((groups, item) => {
    groups[item.section] = [...(groups[item.section] ?? []), item];
    return groups;
  }, {}), []);

  const notify = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 2600);
  };

  const pageTitle = activeNav === 'Dashboard' ? 'Command center' : activeNav;
  const pageSubtitle = activeNav === 'Dashboard' ? 'Your financial security overview, updated just now.' : `Explore ${activeNav.toLowerCase()} across your intelligence workspace.`;

  return (
    <div className="app-shell">
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="brand-lockup">
          <WaveLogo />
          {!collapsed && <div><strong>FRAUDNET AI</strong><span>AI SECURITY NETWORK</span></div>}
        </div>
        <button className="collapse-button" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">
          {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
        </button>
        <nav className="side-nav">
          {Object.entries(groupedItems).map(([section, items]) => (
            <div className="nav-group" key={section}>
              {!collapsed && <div className="nav-label">{section}</div>}
              {items.map(({ label, icon: Icon }) => (
                <button key={label} className={`nav-item ${activeNav === label ? 'active' : ''}`} onClick={() => setActiveNav(label)} title={collapsed ? label : undefined}>
                  <Icon size={18} /> {!collapsed && <span>{label}</span>}
                  {!collapsed && label === 'Fraud alerts' && <span className="nav-count">12</span>}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="nav-item" onClick={() => notify('Help center is opening soon')}><LifeBuoy size={18} />{!collapsed && <span>Help center</span>}</button>
          <div className="profile-card">
            <div className="avatar">KS</div>
            {!collapsed && <div className="profile-copy"><strong>FraudNet Analyst</strong><span>Risk administrator</span></div>}
            {!collapsed && <ChevronDown size={16} className="profile-chevron" />}
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="mobile-brand"><WaveLogo /><strong>FRAUDNET AI</strong></div>
          <div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14} /><strong>{pageTitle}</strong></div>
          <div className="top-actions">
            <div className="global-search"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search anything..." /><kbd>⌘ K</kbd></div>
            <button className="icon-button notification-trigger" onClick={() => setShowNotifications(!showNotifications)} aria-label="Notifications"><Bell size={18} /><i /></button>
            {showNotifications && <div className="notification-popover"><div className="popover-heading"><strong>Notifications</strong><span>3 new</span></div><div className="notification-item"><span className="notification-dot red" /><div><strong>Critical alert detected</strong><small>ALT-28491 requires review</small></div><span>8m</span></div><div className="notification-item"><span className="notification-dot blue" /><div><strong>Case assigned to you</strong><small>INV-1024 · Wire activity</small></div><span>32m</span></div><button onClick={() => notify('All notifications marked as read')}>Mark all as read</button></div>}
            <div className="top-divider" />
            <div className="top-profile"><div className="avatar small">KS</div><div><strong>Analyst</strong><span>Administrator</span></div><ChevronDown size={15} /></div>
          </div>
        </header>

        <div className="workspace">
          <section className="page-heading">
            <div><div className="eyebrow"><span className="live-dot" /> LIVE MONITORING</div><h1>{pageTitle}</h1><p>{pageSubtitle}</p></div>
            <div className="heading-actions"><button className="secondary-button" onClick={() => notify('Report export prepared')}><Download size={16} /> Export report</button><button className="primary-button" onClick={() => notify('New investigation workspace created')}><Plus size={17} /> New investigation</button></div>
          </section>

          {activeNav !== 'Dashboard' ? <PlaceholderPage title={activeNav} onAction={() => notify(`${activeNav} action is ready for review`)} /> : <>
            <section className="metric-grid">
              <MetricCard label="Total transactions" value="2.84M" change="12.8%" trend="up" icon={Activity} tone="blue" detail="$1.26B processed today" />
              <MetricCard label="Suspicious transactions" value="1,284" change="4.2%" trend="down" icon={AlertTriangle} tone="red" detail="0.045% of total volume" />
              <MetricCard label="High-risk accounts" value="318" change="8.1%" trend="up" icon={ShieldCheck} tone="amber" detail="42 require attention" />
              <MetricCard label="Active investigations" value="86" change="2.4%" trend="up" icon={FileSearch} tone="green" detail="18 due this week" />
            </section>

            <section className="main-grid">
              <div className="panel activity-panel">
                <PanelHeader title="Transaction activity" subtitle="Volume across monitored payment rails" action={<select value={range} onChange={(event) => setRange(event.target.value)} className="select-control"><option>Last 24 hours</option><option>Last 7 days</option><option>Last 30 days</option></select>} />
                <div className="chart-legend"><span><i className="legend-blue" /> Normal transactions <strong>2.83M</strong></span><span><i className="legend-red" /> Suspicious <strong>1,284</strong></span></div>
                <div className="activity-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={activityData} margin={{ top: 16, right: 12, left: -18, bottom: 0 }}><defs><linearGradient id="normalFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7fa6b8" stopOpacity={0.24} /><stop offset="100%" stopColor="#7fa6b8" stopOpacity={0} /></linearGradient><linearGradient id="suspiciousFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#c9828c" stopOpacity={0.18} /><stop offset="100%" stopColor="#c9828c" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#d6e6ef" vertical={false} strokeDasharray="3 3" /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#66808e', fontSize: 11 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#66808e', fontSize: 11 }} /><Tooltip contentStyle={{ background: '#f7fbfd', border: '1px solid #b7cbd6', borderRadius: 10, color: '#2a3e48' }} /><Area type="monotone" dataKey="normal" stroke="#7fa6b8" strokeWidth={2.5} fill="url(#normalFill)" /><Area type="monotone" dataKey="suspicious" stroke="#c9828c" strokeWidth={2} fill="url(#suspiciousFill)" /></AreaChart></ResponsiveContainer></div>
              </div>
              <div className="panel risk-panel">
                <PanelHeader title="Risk distribution" subtitle="Across all active accounts" action={<button className="more-button"><MoreHorizontal size={18} /></button>} />
                <div className="donut-wrap"><ResponsiveContainer width="100%" height={190}><PieChart><Pie data={distribution} innerRadius={60} outerRadius={82} paddingAngle={4} dataKey="value" stroke="none">{distribution.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie></PieChart></ResponsiveContainer><div className="donut-center"><strong>12.4K</strong><span>total alerts</span></div></div>
                <div className="risk-legend">{distribution.map((item) => <div key={item.name}><span><i style={{ background: item.color }} />{item.name}</span><strong>{item.value}%</strong></div>)}</div>
              </div>
            </section>

            <section className="lower-grid">
              <div className="panel alerts-panel"><PanelHeader title="Recent fraud alerts" subtitle="Prioritized by detection confidence" action={<button className="text-button" onClick={() => setActiveNav('Fraud alerts')}>View all <ArrowUpRight size={15} /></button>} /><div className="table-toolbar"><div className="table-search"><Search size={15} /><input placeholder="Filter alerts..." /></div><button className="filter-button"><Filter size={15} /> Filters</button></div><div className="data-table-wrap"><table><thead><tr><th>Alert</th><th>Account</th><th>Amount</th><th>Risk score</th><th>Detection reason</th><th>Generated</th><th /></tr></thead><tbody>{alerts.map((alert) => <tr key={alert.id} onClick={() => setSelectedAlert(alert)}><td><strong>{alert.id}</strong><small>{alert.transaction}</small></td><td><span className="account-cell"><span className="account-icon"><Globe2 size={14} /></span>{alert.account}</span></td><td className="amount-cell">{alert.amount}</td><td><span className={`score ${alert.risk.toLowerCase()}`}>{alert.score}</span></td><td><span className="reason-cell"><i className={`risk-dot ${alert.risk.toLowerCase()}`} />{alert.reason}</span></td><td className="muted-cell">{alert.time}</td><td><button className="row-more"><MoreHorizontal size={16} /></button></td></tr>)}</tbody></table></div></div>
              <div className="panel investigations-panel"><PanelHeader title="Investigation pulse" subtitle="Cases requiring your attention" action={<button className="more-button"><MoreHorizontal size={18} /></button>} /><div className="case-list"><CaseItem id="INV-1024" title="Cross-border wire activity" status="In review" priority="Critical" time="Updated 12m ago" /><CaseItem id="INV-1021" title="Synthetic identity cluster" status="Open" priority="High" time="Updated 1h ago" /><CaseItem id="INV-1018" title="Velocity anomaly · AC-8821" status="Assigned" priority="Medium" time="Updated 3h ago" /></div><button className="outline-wide" onClick={() => setActiveNav('Investigation center')}>Open investigation center <ChevronRight size={16} /></button></div>
            </section>

            <section className="bottom-grid"><div className="panel network-panel"><PanelHeader title="Transaction network" subtitle="Live view of connected account clusters" action={<button className="text-button" onClick={() => setActiveNav('Transaction network')}>Explore network <ArrowUpRight size={15} /></button>} /><div className="network-stage"><div className="network-grid" /><div className="connection c1" /><div className="connection c2" /><div className="connection c3" /><div className="connection c4" /><NetworkNode x="17%" y="48%" label="AC-0018" risk="safe" /><NetworkNode x="39%" y="28%" label="AC-0046" risk="medium" /><NetworkNode x="39%" y="68%" label="AC-0091" risk="high" /><NetworkNode x="63%" y="48%" label="AC-1024" risk="high" main /><NetworkNode x="84%" y="28%" label="AC-8812" risk="safe" /><NetworkNode x="84%" y="70%" label="AC-4110" risk="medium" /></div><div className="network-summary"><span><i className="risk-dot high" /> 4 suspicious clusters</span><span><i className="risk-dot medium" /> 28 connected accounts</span><span><i className="risk-dot safe" /> $184K flow monitored</span></div></div><div className="panel health-panel"><PanelHeader title="System health" subtitle="All systems operational" action={<button className="more-button"><MoreHorizontal size={18} /></button>} /><div className="health-list"><HealthItem label="Detection engine" value="99.98%" status="Operational" /><HealthItem label="Database connection" value="28ms" status="Operational" /><HealthItem label="AI Copilot" value="Demo" status="Demo mode" /><HealthItem label="MCP server" value="Demo" status="Not configured" /></div><div className="health-footer"><span><span className="pulse-dot" /> Last checked just now</span><button onClick={() => notify('System health refreshed')}><RefreshCw size={14} /> Refresh</button></div></div></section>
          </>}
        </div>
      </main>

      <button className={`copilot-fab ${copilotOpen ? 'hidden' : ''}`} onClick={() => setCopilotOpen(true)}><Bot size={22} /><span>Ask Copilot</span></button>
      {copilotOpen && <Copilot onClose={() => setCopilotOpen(false)} />}
      {selectedAlert && <AlertDrawer alert={selectedAlert} onClose={() => setSelectedAlert(null)} onAction={(message) => { setSelectedAlert(null); notify(message); }} />}
      {toast && <div className="toast"><ShieldCheck size={16} />{toast}</div>}
    </div>
  );
}

function WaveLogo() { return <div className="wave-logo" aria-label="FraudNet logo"><span className="wave-n">N</span><span className="wave-chevron">›</span><span className="wave-x">X</span><span className="wave-mark"><i /><i /><i /></span></div>; }
function MetricCard({ label, value, change, trend, icon: Icon, tone, detail }: { label: string; value: string; change: string; trend: 'up' | 'down'; icon: typeof Activity; tone: string; detail: string }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={19} /></div><div className="metric-label">{label}<span className={`trend ${trend}`}>{trend === 'up' ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}{change}</span></div><div className="metric-value">{value}</div><div className="metric-detail">{detail}<ChevronRight size={14} /></div></div>;
}
function PanelHeader({ title, subtitle, action }: { title: string; subtitle: string; action: React.ReactNode }) { return <div className="panel-header"><div><h2>{title}</h2><p>{subtitle}</p></div>{action}</div>; }
function CaseItem({ id, title, status, priority, time }: { id: string; title: string; status: string; priority: string; time: string }) { return <div className="case-item"><div className="case-symbol"><FileSearch size={16} /></div><div className="case-copy"><strong>{title}</strong><span>{id} · {time}</span></div><div className={`priority ${priority.toLowerCase()}`}>{priority}</div><span className="case-status">{status}</span><ChevronRight size={15} /></div>; }
function NetworkNode({ x, y, label, risk, main = false }: { x: string; y: string; label: string; risk: string; main?: boolean }) { return <div className={`network-node ${risk} ${main ? 'main' : ''}`} style={{ left: x, top: y }}><span>{main && <ShieldCheck size={13} />}</span><small>{label}</small></div>; }
function HealthItem({ label, value, status }: { label: string; value: string; status: string }) { return <div className="health-item"><span className="health-check"><ShieldCheck size={14} /></span><div><strong>{label}</strong><small>{status}</small></div><b>{value}</b></div>; }
function PlaceholderPage({ title, onAction }: { title: string; onAction: () => void }) { return <div className="placeholder-page"><div className="placeholder-icon"><Sparkles size={28} /></div><h2>{title} workspace</h2><p>This intelligence module is ready to connect to your operational data. Use the dashboard to open alerts, investigations, and account relationships.</p><button className="primary-button" onClick={onAction}><Plus size={16} /> Create a workspace view</button></div>; }
function AlertDrawer({ alert, onClose, onAction }: { alert: AlertItem; onClose: () => void; onAction: (message: string) => void }) { return <div className="drawer-backdrop" onClick={onClose}><aside className="alert-drawer" onClick={(event) => event.stopPropagation()}><div className="drawer-head"><div><span className="eyebrow">ALERT DETAILS</span><h2>{alert.id}</h2></div><button className="icon-button" onClick={onClose}><X size={18} /></button></div><div className="drawer-risk"><span className={`score ${alert.risk.toLowerCase()}`}>{alert.score}</span><div><strong>{alert.risk} risk detected</strong><span>Model confidence score</span></div><AlertTriangle size={20} /></div><div className="drawer-section"><span className="drawer-label">Detection reason</span><h3>{alert.reason}</h3><p>Activity differs from the account's established behavior across location, velocity, and relationship signals.</p></div><div className="detail-list"><div><span>Transaction</span><strong>{alert.transaction}</strong></div><div><span>Account</span><strong>{alert.account}</strong></div><div><span>Transaction amount</span><strong>{alert.amount}</strong></div><div><span>Generated</span><strong>{alert.time}</strong></div></div><div className="drawer-actions"><button className="primary-button" onClick={() => onAction('Investigation created from alert')}><Plus size={16} /> Create investigation</button><button className="secondary-button" onClick={() => onAction('Alert marked as reviewed')}>Mark as reviewed</button><button className="text-button" onClick={() => onAction('Copilot opened with alert context')}><MessageSquareText size={16} /> Ask Copilot</button></div></aside></div>; }
function Copilot({ onClose }: { onClose: () => void }) { const [message, setMessage] = useState(''); const [sent, setSent] = useState(false); return <aside className="copilot-panel"><div className="copilot-head"><div className="copilot-title"><div className="copilot-icon"><Bot size={19} /></div><div><strong>FraudNet AI Copilot</strong><span><i /> Connected to investigation context</span></div></div><div><button className="icon-button" onClick={() => setSent(false)}><RefreshCw size={16} /></button><button className="icon-button" onClick={onClose}><X size={18} /></button></div></div><div className="copilot-body">{!sent ? <><div className="copilot-welcome"><Sparkles size={18} /><strong>What would you like to investigate?</strong><p>I can explain alerts, trace account relationships, and summarize evidence from your workspace.</p></div><div className="suggestion-list"><button onClick={() => setMessage('Explain the highest-risk alert')}>Explain the highest-risk alert <ArrowUpRight size={14} /></button><button onClick={() => setMessage('Show suspicious account connections')}>Show suspicious account connections <ArrowUpRight size={14} /></button><button onClick={() => setMessage('Summarize open investigations')}>Summarize open investigations <ArrowUpRight size={14} /></button></div></> : <div className="copilot-response"><div className="user-bubble">{message}</div><div className="ai-bubble"><div className="mini-ai"><Bot size={14} /></div><p>Based on the current workspace, This is a demonstration interface. Live RAG retrieval is not connected yet, so I will not claim to have queried transaction or case records. Connect the secured FastAPI knowledge and evidence endpoints to enable grounded answers.</p><span>Generated from workspace data · 2s ago</span></div></div>}</div><div className="copilot-input"><input placeholder="Ask about your workspace..." value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && message.trim()) setSent(true); }} /><button onClick={() => message.trim() && setSent(true)}><ArrowUpRight size={17} /></button><small>Copilot provides analysis, not a fraud determination.</small></div></aside>; }

export default App;
