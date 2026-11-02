"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  AlertTriangle,
  Bot,
  Database,
  FileCode,
  ShieldCheck,
  BarChart3,
  Settings,
  Sparkles,
  GitBranch
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Incidents", href: "/incidents", icon: AlertTriangle },
  { name: "Agent Investigations", href: "/investigations", icon: Bot },
  { name: "RAG & Telemetry", href: "/rag", icon: Database },
  { name: "Code & Repositories", href: "/repositories", icon: GitBranch },
  { name: "Sandbox Validation", href: "/sandbox", icon: ShieldCheck },
  { name: "AI Evaluations", href: "/evaluations", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-border bg-card/60 backdrop-blur-md flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-border">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-600 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
          <Sparkles className="h-5 w-5 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 font-bold text-base tracking-tight text-foreground">
            <span>AgentOps</span>
            <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-primary/20 text-primary border border-primary/30">
              AI
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground font-medium">Incident Investigator</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
          Autonomous Ops
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                isActive
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              )}
            >
              <item.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-muted-foreground")} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-border bg-card/40">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            LangGraph Agent
          </span>
          <span className="text-[11px] font-mono text-zinc-400">v1.0.0</span>
        </div>
        <p className="text-[11px] text-zinc-500 truncate">
          Active: Autonomous SRE Loop
        </p>
      </div>
    </aside>
  );
}
