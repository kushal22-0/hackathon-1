import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Database,
  FileSearch,
  GitBranch,
  Network,
  RefreshCw,
  ScanSearch,
  ShieldCheck,
  Waypoints,
} from "lucide-react"

import { FraudNetMark } from "@/components/FraudNetMark"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { useBackendHealth } from "@/hooks/useBackendHealth"
import { API_BASE_URL } from "@/lib/api"
import { cn } from "@/lib/utils"

const capabilities = [
  {
    step: "01",
    signal: "Ingest",
    title: "Transaction fabric",
    description:
      "Validated CSV ingestion, typed rules for every field, and paginated search across accounts, devices, channels, and time windows.",
    icon: Database,
  },
  {
    step: "02",
    signal: "Detect",
    title: "Layered risk engine",
    description:
      "Configurable transfer, velocity, and succession rules combined with IsolationForest anomaly scoring into one documented 0–100 risk score.",
    icon: ScanSearch,
  },
  {
    step: "03",
    signal: "Investigate",
    title: "Fund-flow tracing",
    description:
      "NetworkX traversal for N-hop flows, circular transfers, fan-in, and fan-out—paired with a live account risk profile.",
    icon: Waypoints,
  },
  {
    step: "04",
    signal: "Explain",
    title: "Evidence-backed alerts",
    description:
      "Every alert carries the rule hits, ML score, contextual evidence, and a plain-language explanation an investigator can act on.",
    icon: FileSearch,
  },
] as const

const stack = [
  "FastAPI",
  "Supabase + pgvector",
  "scikit-learn",
  "NetworkX",
  "React + Vite",
  "PostgreSQL RLS",
] as const

function StatusDot({ online }: { online: boolean }) {
  return (
    <span className="relative flex h-2 w-2">
      {online ? (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
      ) : null}
      <span
        className={cn(
          "relative inline-flex h-2 w-2 rounded-full",
          online ? "bg-emerald-400" : "bg-muted-foreground/50",
        )}
      />
    </span>
  )
}

function SystemPulse() {
  const { status, data, latencyMs, error, refresh } = useBackendHealth()
  const online = status === "online"
  const checking = status === "checking"

  const healthRows = [
    { label: "Service", value: data?.service ?? "FraudNet AI API" },
    { label: "Version", value: data?.version ?? "—" },
    { label: "Environment", value: data?.environment ?? "—" },
    {
      label: "Round trip",
      value: latencyMs === null ? "—" : `${latencyMs} ms`,
    },
  ]

  return (
    <Card className="surface-ring relative overflow-hidden border-border/80 bg-card/80 backdrop-blur">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/70 to-transparent" />
      <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-border/60 px-5 py-4">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" />
          <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Control plane
          </span>
        </div>
        <Badge variant={online ? "default" : checking ? "secondary" : "outline"}>
          <StatusDot online={online} />
          <span className="ml-1.5">
            {online ? "API online" : checking ? "Checking" : "API offline"}
          </span>
        </Badge>
      </CardHeader>

      <CardContent className="p-5">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              System pulse
            </p>
            <p className="mt-2 text-2xl font-semibold tracking-tight">
              {online ? "Core API is responsive" : checking ? "Reaching the API…" : "API not reachable"}
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0 text-muted-foreground"
            onClick={() => void refresh()}
            disabled={checking}
            aria-label="Re-check API health"
          >
            <RefreshCw className={cn("h-4 w-4", checking && "animate-spin")} />
          </Button>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border/70 bg-border/70">
          {healthRows.map((row) => (
            <div key={row.label} className="bg-[#091018] px-4 py-3.5">
              <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                {row.label}
              </p>
              <p className="mt-1 truncate text-sm font-medium text-foreground/90">
                {row.value}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-5 flex items-start gap-3 rounded-lg border border-border/60 bg-background/50 p-4">
          <GitBranch className="mt-0.5 h-4 w-4 shrink-0 text-primary/80" />
          <div className="min-w-0">
            <p className="text-sm font-medium">Endpoint</p>
            <p className="mt-1 break-all font-mono text-xs text-muted-foreground">
              {API_BASE_URL}/health
            </p>
            {error && status === "offline" ? (
              <p className="mt-2 text-xs text-amber-300/90">
                {error}. Start it with{" "}
                <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px]">
                  npm run dev:backend
                </code>
                .
              </p>
            ) : (
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Public liveness only. Business endpoints are JWT-guarded when auth
                is enabled.
              </p>
            )}
          </div>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          {["Rules", "IsolationForest", "NetworkX"].map((item) => (
            <div
              key={item}
              className="rounded-md border border-border/60 bg-card px-3 py-2 text-center font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground"
            >
              {item}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function CapabilityCard({
  step,
  signal,
  title,
  description,
  icon: Icon,
}: (typeof capabilities)[number]) {
  return (
    <div className="group relative flex flex-col rounded-xl border border-border/60 bg-card/45 p-6 transition-colors hover:border-primary/30 hover:bg-card/80">
      <div className="flex items-start justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-primary/20 bg-primary/10 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <span className="font-mono text-xs text-muted-foreground/60">{step}</span>
      </div>
      <p className="mt-6 font-mono text-[10px] uppercase tracking-[0.22em] text-primary/80">
        {signal}
      </p>
      <h3 className="mt-2 text-lg font-semibold tracking-tight">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  )
}

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0 hero-grid opacity-70" />
      <div className="pointer-events-none absolute left-1/2 top-[-26rem] h-[46rem] w-[70rem] -translate-x-1/2 rounded-full bg-emerald-500/[0.07] blur-[120px]" />
      <div className="pointer-events-none absolute right-[-16rem] top-24 h-[30rem] w-[30rem] rounded-full bg-sky-500/[0.05] blur-[100px]" />

      <header className="relative z-20 border-b border-border/50 bg-background/55 backdrop-blur-xl">
        <div className="container flex h-16 items-center justify-between">
          <a href="/" className="flex items-center gap-3">
            <FraudNetMark />
            <span className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight">
                FraudNet AI
              </span>
              <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                Detect · Investigate · Explain
              </span>
            </span>
          </a>

          <nav className="hidden items-center gap-7 text-sm text-muted-foreground md:flex">
            <a className="transition-colors hover:text-foreground" href="#architecture">
              Architecture
            </a>
            <a className="transition-colors hover:text-foreground" href="#scope">
              Scope
            </a>
            <a
              className="transition-colors hover:text-foreground"
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noreferrer"
            >
              API reference
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Badge variant="outline" className="hidden border-primary/25 text-primary sm:inline-flex">
              Phase 1
            </Badge>
            <Button asChild size="sm" variant="outline" className="border-primary/30 bg-primary/5">
              <a
                href={`${API_BASE_URL}/docs`}
                target="_blank"
                rel="noreferrer"
              >
                Open API
                <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            </Button>
          </div>
        </div>
      </header>

      <main className="relative z-10">
        <section className="container pb-20 pt-16 sm:pt-20 lg:pb-28 lg:pt-24">
          <div className="grid items-center gap-14 lg:grid-cols-[1.06fr_0.94fr] lg:gap-16">
            <div className="animate-fade-up">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/[0.06] px-3 py-1.5 text-xs text-primary">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute h-full w-full animate-ping rounded-full bg-primary opacity-50" />
                  <span className="relative h-1.5 w-1.5 rounded-full bg-primary" />
                </span>
                Phase 1 foundation · core detection engine
              </div>

              <h1 className="max-w-2xl text-balance text-4xl font-semibold leading-[1.05] tracking-[-0.04em] sm:text-5xl lg:text-6xl">
                Follow the money.
                <br />
                <span className="text-gradient">Explain the risk.</span>
              </h1>

              <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground sm:text-[17px]">
                FraudNet AI turns raw transaction data into explainable risk
                signals, then traces the network behind them. Built for analysts
                who need evidence—not another black box.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Button asChild size="lg" className="gap-2">
                  <a
                    href={`${API_BASE_URL}/docs`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Explore the API
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </Button>
                <Button asChild size="lg" variant="outline" className="bg-background/30">
                  <a href="#architecture">
                    See the system
                    <Network className="h-4 w-4" />
                  </a>
                </Button>
              </div>

              <div className="mt-9 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-primary/80" />
                  JWT roles: admin & investigator
                </span>
                <span className="hidden h-3 w-px bg-border sm:block" />
                <span className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-primary/80" />
                  Supabase PostgreSQL + pgvector
                </span>
              </div>
            </div>

            <div className="animate-fade-up lg:pl-2" style={{ animationDelay: "120ms" }}>
              <SystemPulse />
            </div>
          </div>

          <div className="mt-16 border-y border-border/50 py-5 lg:mt-24">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground/70">
                Phase 1 stack
              </p>
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                {stack.map((item) => (
                  <span
                    key={item}
                    className="text-xs font-medium text-muted-foreground/80"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="architecture" className="container scroll-mt-24 pb-20 lg:pb-28">
          <div className="mb-10 max-w-2xl">
            <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-primary/80">
              The pipeline
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">
              One pipeline. Four questions.
            </h2>
            <p className="mt-4 text-sm leading-7 text-muted-foreground sm:text-base">
              What happened? Is it suspicious? Where did the money go? Can we
              prove why? Every layer has one job, and every answer is traceable.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {capabilities.map((capability) => (
              <CapabilityCard key={capability.step} {...capability} />
            ))}
          </div>
        </section>

        <section id="scope" className="container scroll-mt-24 pb-20 lg:pb-28">
          <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
            <Card className="overflow-hidden border-border/60 bg-card/50">
              <CardContent className="p-7 sm:p-9">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-primary/80">
                    Scope discipline
                  </p>
                </div>
                <h2 className="mt-5 max-w-lg text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">
                  Phase 1 ends at a trustworthy engine.
                </h2>
                <p className="mt-4 max-w-xl text-sm leading-7 text-muted-foreground">
                  No half-built graph explorer, no decorative dashboards. This
                  phase ships the data model, ingestion, detection, tracing,
                  risk profiles, auth, and tests that every later surface depends
                  on.
                </p>
                <div className="mt-6 flex flex-wrap gap-2">
                  {[
                    "5k demo transactions",
                    "pgvector schema",
                    "RLS policies",
                    "pytest coverage",
                    "typed API contracts",
                  ].map((item) => (
                    <Badge
                      key={item}
                      variant="secondary"
                      className="rounded-md border border-border/70 bg-background/50 font-normal text-muted-foreground"
                    >
                      {item}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/60 bg-card/50">
              <CardContent className="flex h-full flex-col justify-between p-7 sm:p-9">
                <div>
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-4 w-4 text-primary" />
                    <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                      Deliberately deferred
                    </p>
                  </div>
                  <p className="mt-5 text-lg font-medium leading-7">
                    Graph workspace, cases UI, analytics, Copilot, and MCP tools
                    arrive only after Phase 1 is accepted.
                  </p>
                </div>
                <div className="mt-8 space-y-2.5">
                  {[
                    "Detection services stay callable from future tool adapters",
                    "Knowledge tables exist now; embeddings land later",
                    "No business logic in routes or adapters",
                  ].map((line) => (
                    <div key={line} className="flex items-start gap-2.5">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" />
                      <p className="text-xs leading-5 text-muted-foreground">
                        {line}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-border/50 bg-background/60">
        <div className="container flex flex-col gap-5 py-8 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <FraudNetMark className="h-8 w-8 rounded-lg" />
            <div>
              <p className="text-sm font-medium">FraudNet AI</p>
              <p className="text-xs text-muted-foreground">
                Detect. Investigate. Explain.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
            <span>Phase 1 · Core engine</span>
            <a
              className="transition-colors hover:text-foreground"
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noreferrer"
            >
              OpenAPI
            </a>
            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground/50">
              Built for evidence
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
