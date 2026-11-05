import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "$0.00"
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatCompactCurrency(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "$0"
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`
  }
  return formatCurrency(value)
}

export function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return formatTimestamp(value)
}

export function riskLevel(score: number): "low" | "medium" | "high" | "critical" {
  if (score >= 85) return "critical"
  if (score >= 65) return "high"
  if (score >= 40) return "medium"
  return "low"
}

export function riskColor(level: string): string {
  switch (level) {
    case "critical":
      return "text-red-600 bg-red-50 dark:bg-red-950/30"
    case "high":
      return "text-amber-600 bg-amber-50 dark:bg-amber-950/30"
    case "medium":
      return "text-blue-600 bg-blue-50 dark:bg-blue-950/30"
    default:
      return "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30"
  }
}

export function statusColor(status: string): string {
  switch (status.toLowerCase()) {
    case "open":
      return "text-amber-600 bg-amber-50 dark:bg-amber-950/30"
    case "in_progress":
    case "investigating":
      return "text-blue-600 bg-blue-50 dark:bg-blue-950/30"
    case "under_review":
    case "pending_review":
    case "triaged":
      return "text-violet-600 bg-violet-50 dark:bg-violet-950/30"
    case "resolved":
    case "closed":
      return "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30"
    case "dismissed":
      return "text-slate-600 bg-slate-50 dark:bg-slate-950/30"
    default:
      return "text-slate-600 bg-slate-50 dark:bg-slate-950/30"
  }
}

export function truncate(value: string | null | undefined, length = 60): string {
  if (!value) return ""
  if (value.length <= length) return value
  return `${value.slice(0, length)}…`
}

export function uuidShort(value: string | null | undefined): string {
  if (!value) return "—"
  return value.slice(0, 8).toUpperCase()
}