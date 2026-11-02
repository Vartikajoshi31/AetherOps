"use client";

import { ServiceHealth } from "@/lib/types";
import { Server, Activity, ShieldAlert, CheckCircle2 } from "lucide-react";

interface ServiceHealthGridProps {
  services?: ServiceHealth[];
}

export function ServiceHealthGrid({ services = [] }: ServiceHealthGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
      {services.map((svc) => {
        const isHealthy = svc.health_status === "healthy";
        const isDegraded = svc.health_status === "degraded";
        const isCritical = svc.health_status === "critical";

        return (
          <div
            key={svc.id}
            className={`p-3.5 rounded-lg border bg-card/40 backdrop-blur-sm transition-all ${
              isCritical
                ? "border-red-900/50 bg-red-950/20"
                : isDegraded
                ? "border-amber-900/50 bg-amber-950/20"
                : "border-zinc-800/80 hover:border-zinc-700"
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 text-zinc-400" />
                <span className="font-semibold text-xs tracking-tight text-foreground truncate">
                  {svc.name}
                </span>
              </div>
              <span
                className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium uppercase ${
                  isCritical
                    ? "bg-red-950/60 text-red-400 border border-red-800/60"
                    : isDegraded
                    ? "bg-amber-950/60 text-amber-400 border border-amber-800/60"
                    : "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60"
                }`}
              >
                {isCritical ? (
                  <ShieldAlert className="h-3 w-3" />
                ) : isDegraded ? (
                  <Activity className="h-3 w-3 animate-pulse" />
                ) : (
                  <CheckCircle2 className="h-3 w-3" />
                )}
                {svc.health_status}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-muted-foreground mt-2 pt-2 border-t border-border/50">
              <span className="text-[11px] font-mono text-zinc-400">{svc.language}</span>
              <span
                className={`font-mono text-xs font-semibold ${
                  isCritical
                    ? "text-red-400"
                    : isDegraded
                    ? "text-amber-400"
                    : "text-emerald-400"
                }`}
              >
                {svc.error_rate} error rate
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
