"use client";

import { Activity, Bell, Shield, Sparkles, Terminal } from "lucide-react";

interface HeaderProps {
  activeIncidentsCount?: number;
}

export function Header({ activeIncidentsCount = 0 }: HeaderProps) {
  return (
    <header className="h-16 border-b border-border bg-card/40 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 text-xs font-medium">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
          <span>Real-Time Engine Online</span>
        </div>

        <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground border-l border-border pl-4">
          <Terminal className="h-3.5 w-3.5 text-zinc-400" />
          <span className="font-mono text-zinc-300">Cluster: prod-us-east-1</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Active Incident Warning Badge */}
        {activeIncidentsCount > 0 ? (
          <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-red-950/60 border border-red-800/70 text-red-400 text-xs font-semibold">
            <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
            <span>{activeIncidentsCount} Active Incident{activeIncidentsCount > 1 ? "s" : ""}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 text-xs">
            <Shield className="h-3.5 w-3.5" />
            <span>All Services Operational</span>
          </div>
        )}

        <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-secondary/60 border border-border text-xs text-zinc-300">
          <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
          <span>Sandboxed Patch Defense Active</span>
        </div>
      </div>
    </header>
  );
}
