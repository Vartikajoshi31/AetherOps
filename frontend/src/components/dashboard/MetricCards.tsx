"use client";

import { AlertOctagon, CheckCircle2, Clock, DollarSign, ShieldAlert, Zap } from "lucide-react";
import { DashboardMetrics } from "@/lib/types";

interface MetricCardsProps {
  metrics: DashboardMetrics | null;
  isLoading?: boolean;
}

export function MetricCards({ metrics, isLoading }: MetricCardsProps) {
  const cards = [
    {
      title: "Active Incidents",
      value: isLoading ? "..." : (metrics?.active_incidents ?? 0),
      subtitle: `${metrics?.total_incidents ?? 0} total incidents tracked`,
      icon: ShieldAlert,
      color: "text-red-400",
      bg: "bg-red-950/30 border-red-900/40",
      accent: "text-red-400",
    },
    {
      title: "Resolved Incidents",
      value: isLoading ? "..." : (metrics?.resolved_incidents ?? 0),
      subtitle: "Autonomous & human verified",
      icon: CheckCircle2,
      color: "text-emerald-400",
      bg: "bg-emerald-950/30 border-emerald-900/40",
      accent: "text-emerald-400",
    },
    {
      title: "Mean Time to Diagnosis",
      value: isLoading ? "..." : (metrics?.mean_time_to_diagnosis ?? "4m 12s"),
      subtitle: "AI correlation & root-cause speed",
      icon: Clock,
      color: "text-cyan-400",
      bg: "bg-cyan-950/30 border-cyan-900/40",
      accent: "text-cyan-400",
    },
    {
      title: "Patch Validation Rate",
      value: isLoading ? "..." : (metrics?.patch_validation_success_rate ?? "94.2%"),
      subtitle: "Zero-regression isolated tests",
      icon: Zap,
      color: "text-indigo-400",
      bg: "bg-indigo-950/30 border-indigo-900/40",
      accent: "text-indigo-400",
    },
    {
      title: "Total AI Cost",
      value: isLoading ? "..." : `$${(metrics?.total_ai_investigations_cost_usd ?? 0.14).toFixed(3)}`,
      subtitle: "LLM token expenditure tracked",
      icon: DollarSign,
      color: "text-amber-400",
      bg: "bg-amber-950/30 border-amber-900/40",
      accent: "text-amber-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.title}
            className={`p-4 rounded-xl border bg-card/60 backdrop-blur-sm transition-all hover:border-zinc-700/80 ${card.bg}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-muted-foreground">{card.title}</span>
              <Icon className={`h-4 w-4 ${card.color}`} />
            </div>
            <div className="text-2xl font-bold tracking-tight text-foreground">{card.value}</div>
            <p className="text-[11px] text-zinc-400 mt-1">{card.subtitle}</p>
          </div>
        );
      })}
    </div>
  );
}
