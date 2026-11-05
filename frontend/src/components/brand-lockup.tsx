import { cn } from "@/lib/utils"
import { NexGuardMark } from "./NexGuardMark"

interface BrandLockupProps {
  collapsed?: boolean
  className?: string
}

export function BrandLockup({ collapsed = false, className }: BrandLockupProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <NexGuardMark className="h-9 w-9" />
      {!collapsed && (
        <div className="flex flex-col">
          <span className="text-sm font-semibold tracking-tight">
            NexGuard AI
          </span>
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
            Detect · Investigate · Explain
          </span>
        </div>
      )}
    </div>
  )
}