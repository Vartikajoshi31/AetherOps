"use client";

import { Bot, Terminal, GitCommit, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

interface AgentActivityStreamProps {
  activities?: {
    id: string;
    agent_name: string;
    event_type: string;
    message: string;
    step_index: number;
    duration_ms: number;
    created_at: string;
  }[];
}

const AGENT_BADGES: Record<string, { label: string; color: string; icon: any }> = {
  triage: { label: "Triage Agent", color: "text-blue-400 bg-blue-950/60 border-blue-800/80", icon: Bot },
  log_analysis: { label: "Log Agent", color: "text-amber-400 bg-amber-950/60 border-amber-800/80", icon: Terminal },
  code_investigation: { label: "Code Agent", color: "text-purple-400 bg-purple-950/60 border-purple-800/80", icon: GitCommit },
  root_cause: { label: "RCA Agent", color: "text-cyan-400 bg-cyan-950/60 border-cyan-800/80", icon: AlertTriangle },
  fix_generation: { label: "Fix Agent", color: "text-pink-400 bg-pink-950/60 border-pink-800/80", icon: Bot },
  validation: { label: "Validation Agent", color: "text-emerald-400 bg-emerald-950/60 border-emerald-800/80", icon: ShieldCheck },
  review: { label: "Review Agent", color: "text-indigo-400 bg-indigo-950/60 border-indigo-800/80", icon: CheckCircle2 },
};

export function AgentActivityStream({ activities = [] }: AgentActivityStreamProps) {
  if (activities.length === 0) {
    return (
      <div className="p-8 text-center text-xs text-muted-foreground border border-dashed border-border rounded-lg">
        No recent agent execution events recorded.
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {activities.map((act) => {
        const agentMeta = AGENT_BADGES[act.agent_name] || {
          label: act.agent_name,
          color: "text-zinc-400 bg-zinc-900 border-zinc-800",
          icon: Bot,
        };
        const Icon = agentMeta.icon;

        return (
          <div
            key={act.id}
            className="flex items-start gap-3 p-3 rounded-lg border border-border/80 bg-card/40 hover:bg-card/70 transition-colors"
          >
            <div className={`mt-0.5 p-1.5 rounded-md border ${agentMeta.color}`}>
              <Icon className="h-3.5 w-3.5" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-foreground">{agentMeta.label}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-secondary text-zinc-400">
                    Step {act.step_index}
                  </span>
                </div>
                <span className="text-[11px] text-muted-foreground">
                  {formatRelativeTime(act.created_at)}
                </span>
              </div>

              <p className="text-xs text-zinc-300 mt-1 leading-relaxed line-clamp-2">
                {act.message}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
