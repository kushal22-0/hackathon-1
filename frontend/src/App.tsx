import { lazy } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"

import { AuthProvider, useAuth } from "@/lib/auth"
import { ThemeProvider } from "@/components/theme-provider"
import { AppLayout } from "@/components/app-layout"
import { Toaster } from "@/components/ui/toaster"

const Dashboard = lazy(() => import("@/pages/Dashboard"))
const Transactions = lazy(() => import("@/pages/Transactions"))
const TransactionDetail = lazy(() => import("@/pages/TransactionDetail"))
const Alerts = lazy(() => import("@/pages/Alerts"))
const AlertDetail = lazy(() => import("@/pages/AlertDetail"))
const Network = lazy(() => import("@/pages/Network"))
const MoneyFlow = lazy(() => import("@/pages/MoneyFlow"))
const AIDetection = lazy(() => import("@/pages/AIDetection"))
const AccountRisk = lazy(() => import("@/pages/AccountRisk"))
const Customers = lazy(() => import("@/pages/Customers"))
const Accounts = lazy(() => import("@/pages/Accounts"))
const Investigation = lazy(() => import("@/pages/Investigation"))
const EvidenceVault = lazy(() => import("@/pages/EvidenceVault"))
const FraudAnalytics = lazy(() => import("@/pages/FraudAnalytics"))
const ModelPerformance = lazy(() => import("@/pages/ModelPerformance"))
const DetectionRules = lazy(() => import("@/pages/DetectionRules"))
const AICopilot = lazy(() => import("@/pages/AICopilot"))
const MCPIntegrations = lazy(() => import("@/pages/MCPIntegrations"))
const HelpCenter = lazy(() => import("@/pages/HelpCenter"))
const Login = lazy(() => import("@/pages/Login"))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex h-screen items-center justify-center">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="customers" element={<Customers />} />
                <Route path="accounts" element={<Accounts />} />
                <Route path="accounts/:id" element={<AccountRisk />} />
                <Route path="transactions" element={<Transactions />} />
                <Route path="transactions/:id" element={<TransactionDetail />} />
                <Route path="alerts" element={<Alerts />} />
                <Route path="alerts/:id" element={<AlertDetail />} />
                <Route path="network" element={<Network />} />
                <Route path="money-flow" element={<MoneyFlow />} />
                <Route path="ai-detection" element={<AIDetection />} />
                <Route path="account-risk" element={<AccountRisk />} />
                <Route path="investigation" element={<Investigation />} />
                <Route path="evidence" element={<EvidenceVault />} />
                <Route path="fraud-analytics" element={<FraudAnalytics />} />
                <Route path="model-performance" element={<ModelPerformance />} />
                <Route path="detection-rules" element={<DetectionRules />} />
                <Route path="ai-copilot" element={<AICopilot />} />
                <Route path="mcp" element={<MCPIntegrations />} />
                <Route path="help" element={<HelpCenter />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
      <Toaster />
    </QueryClientProvider>
  )
}