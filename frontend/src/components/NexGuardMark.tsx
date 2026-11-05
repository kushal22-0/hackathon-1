import { ShieldCheck } from "lucide-react"

export function NexGuardMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-primary/25 bg-primary/10",
        className,
      )}
      aria-hidden="true"
    >
      <svg viewBox="0 0 32 32" className="h-6 w-6">
        <path
          d="M16 3.5 27 7.7v7.1c0 6.1-4.3 11.4-11 14-6.7-2.6-11-7.9-11-14V7.7L16 3.5Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          className="text-primary"
        />
        <circle cx="12" cy="14" r="1.7" className="fill-primary" />
        <circle cx="20.5" cy="11.5" r="1.7" className="fill-sky-400" />
        <circle cx="18.5" cy="20" r="1.7" className="fill-emerald-300" />
        <path
          d="m13.3 13.1 5.7-1.1M13.1 15.2l4.2 3.8M19.6 13l-.9 5.4"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
          className="text-emerald-300/70"
        />
      </svg>
    </span>
  )
}