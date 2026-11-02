import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { IncidentSeverity, IncidentStatus } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSeverityColor(severity: IncidentSeverity | string) {
  switch (severity?.toLowerCase()) {
    case "critical":
      return "text-red-400 bg-red-950/60 border-red-800/80";
    case "high":
      return "text-amber-400 bg-amber-950/60 border-amber-800/80";
    case "medium":
      return "text-yellow-300 bg-yellow-950/50 border-yellow-800/60";
    case "low":
      return "text-emerald-400 bg-emerald-950/50 border-emerald-800/60";
    default:
      return "text-zinc-400 bg-zinc-900 border-zinc-800";
  }
}

export function formatStatusColor(status: IncidentStatus | string) {
  switch (status) {
    case "Detected":
      return "text-red-400 bg-red-950/40 border-red-800/60";
    case "Investigating":
      return "text-cyan-400 bg-cyan-950/40 border-cyan-800/60";
    case "Root Cause Identified":
      return "text-indigo-400 bg-indigo-950/40 border-indigo-800/60";
    case "Fix Generated":
      return "text-purple-400 bg-purple-950/40 border-purple-800/60";
    case "Validating":
      return "text-amber-400 bg-amber-950/40 border-amber-800/60";
    case "Awaiting Approval":
      return "text-orange-400 bg-orange-950/40 border-orange-800/60";
    case "Resolved":
      return "text-emerald-400 bg-emerald-950/40 border-emerald-800/60";
    case "Failed":
      return "text-rose-400 bg-rose-950/40 border-rose-800/60";
    default:
      return "text-zinc-400 bg-zinc-900 border-zinc-800";
  }
}

export function formatRelativeTime(isoString?: string | null): string {
  if (!isoString) return "-";
  const date = new Date(isoString);
  const now = new Date();
  const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSec < 60) return `${Math.max(1, diffSec)}s ago`;
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return `${Math.floor(diffSec / 86400)}d ago`;
}
