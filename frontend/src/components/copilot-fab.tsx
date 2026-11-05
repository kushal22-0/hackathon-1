import { Bot, Sparkles } from "lucide-react"
import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"

export function CopilotFAB() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  if (open) return null

  return (
    <button
      onClick={() => navigate("/ai-copilot")}
      className="fixed right-6 bottom-6 z-40 flex items-center gap-2 rounded-full bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-lg hover:shadow-xl transition-shadow"
    >
      <Bot size={18} />
      <span>Ask Copilot</span>
      <Sparkles size={14} className="text-primary-foreground/70" />
    </button>
  )
}