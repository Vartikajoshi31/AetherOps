"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Bot,
  Activity,
  CheckCircle2,
  Clock,
  Cpu,
  Layers,
  ChevronRight,
  Sparkles,
  RefreshCw,
  Coins,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Code2,
  FileText,
  Terminal,
  Zap,
  ArrowRight
} from "lucide-react";
import { api } from "@/lib/api";

interface AgentEvent {
  id: string;
  agent_name: string;
  stage: string;
  message: string;
  step_index: number;
  duration_ms: number;
  created_at: string;
}

interface InvestigationRun {
  id: string;
  incident_id: string;
  incident_title: string;
  workflow_name: string;
  status: string;
  current_agent: string;
  step_count: number;
  total_tokens_used: number;
  estimated_cost_usd: number;
  started_at: string;
  completed_at?: string | null;
  graph_state?: any;
  error_message?: string | null;
  events?: AgentEvent[];
}

const WORKFLOW_STAGES = [
  { id: "triage", name: "Triage Agent", role: "Severity & Service Classification", icon: AlertTriangle, color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  { id: "logs", name: "Log Intelligence", role: "Recurring Stack Trace Anomaly", icon: FileText, color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20" },
  { id: "code", name: "AST Code Investigator", role: "Hybrid Qdrant Semantic Retrieval", icon: Code2, color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
  { id: "rca", name: "Root Cause Synthesis", role: "Ranked Hypothesis Correlation", icon: Cpu, color: "text-purple-400 bg-purple-500/10 border-purple-500/20" },
  { id: "fix", name: "Fix Generation", role: "Surgical Unified Diff & Tests", icon: Zap, color: "text-pink-400 bg-pink-500/10 border-pink-500/20" },
  { id: "validation", name: "Sandboxed Runner", role: "Isolated Pytest Execution", icon: Terminal, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  { id: "review", name: "Release Gatekeeper", role: "Human Sign-off Staging", icon: ShieldCheck, color: "text-blue-400 bg-blue-500/10 border-blue-500/20" }
];

export default function InvestigationsPage() {
  const [runs, setRuns] = useState<InvestigationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<InvestigationRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    loadInvestigations();
  }, []);

  const loadInvestigations = async () => {
    try {
      setIsRefreshing(true);
      const res = await fetch("/api/investigations");
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
        if (data.length > 0 && !selectedRun) {
          loadRunDetail(data[0].id);
        }
      }
    } catch (e) {
      console.error("Failed to load investigations", e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const loadRunDetail = async (runId: string) => {
    try {
      const res = await fetch(`/api/investigations/${runId}`);
      if (res.ok) {
        const detail = await res.json();
        setSelectedRun(detail);
      }
    } catch (e) {
      console.error("Failed to load run detail", e);
    }
  };

  const totalTokens = runs.reduce((acc, r) => acc + (r.total_tokens_used || 0), 0);
  const totalCost = runs.reduce((acc, r) => acc + (r.estimated_cost_usd || 0), 0);
  const completedRuns = runs.filter((r) => r.status === "paused_awaiting_approval" || r.status === "completed").length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              LangGraph Multi-Agent Orchestration
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
              Stateful Workflow
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time execution trace, checkpoint states, token accounting, and sandboxed test logs for autonomous incident investigations.
          </p>
        </div>

        <button
          onClick={loadInvestigations}
          disabled={isRefreshing}
          className="py-2 px-3.5 rounded-lg border border-border bg-card/60 hover:bg-card text-foreground font-medium text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
          Refresh Swarm Activity
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-card border border-border shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Total Swarm Runs</span>
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground mt-2">{runs.length}</div>
          <span className="text-[11px] text-muted-foreground">Autonomous workflows</span>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Completed / Staged</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-2">{completedRuns}</div>
          <span className="text-[11px] text-muted-foreground">Ready for human review</span>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">LLM Tokens Billed</span>
            <Zap className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-2">{totalTokens.toLocaleString()}</div>
          <span className="text-[11px] text-muted-foreground">Prompt + completion tokens</span>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Total AI Inference Cost</span>
            <Coins className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-purple-400 mt-2">${totalCost.toFixed(4)}</div>
          <span className="text-[11px] text-muted-foreground">Computed from model pricing</span>
        </div>
      </div>

      {/* Interactive LangGraph Architecture Flow Visualizer */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-border/60 pb-3">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-foreground">
              LangGraph Multi-Agent Orchestration Topology
            </h2>
          </div>
          <span className="text-xs font-mono text-muted-foreground">
            Linear / Conditional Retry Loop
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {WORKFLOW_STAGES.map((stage, idx) => {
            const Icon = stage.icon;
            const isCurrentlySelectedAgent = selectedRun?.current_agent?.toLowerCase().includes(stage.id);
            return (
              <div
                key={stage.id}
                className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                  isCurrentlySelectedAgent
                    ? "bg-secondary/70 border-primary shadow-sm ring-1 ring-primary/40"
                    : "bg-secondary/20 border-border/60"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono text-muted-foreground font-semibold">
                      0{idx + 1}
                    </span>
                    <span className={`p-1.5 rounded-lg border ${stage.color}`}>
                      <Icon className="h-3.5 w-3.5" />
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-foreground">{stage.name}</h3>
                  <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                    {stage.role}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-border/40 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-emerald-400 font-medium">Ready</span>
                  {idx < 6 && <ArrowRight className="h-3 w-3 text-muted-foreground/40 hidden lg:block" />}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Content: Runs List & Detailed Execution Trace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Runs List */}
        <div className="lg:col-span-1 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              Investigation Runs ({runs.length})
            </h2>
            <span className="text-xs text-muted-foreground font-mono">Real-time</span>
          </div>

          {runs.length === 0 && !isLoading && (
            <div className="p-8 text-center border border-dashed border-border rounded-xl bg-card/30">
              <Bot className="h-8 w-8 text-muted-foreground/50 mx-auto mb-2" />
              <p className="text-xs font-medium text-foreground">No investigation runs recorded</p>
              <p className="text-[11px] text-muted-foreground mt-1">
                Trigger an investigation from the Incidents dashboard or simulate a chaos scenario.
              </p>
            </div>
          )}

          <div className="space-y-2 max-h-[680px] overflow-y-auto pr-1">
            {runs.map((run) => {
              const isSelected = selectedRun?.id === run.id;
              return (
                <button
                  key={run.id}
                  onClick={() => loadRunDetail(run.id)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-secondary/70 border-primary text-foreground shadow-sm"
                      : "bg-card/60 border-border text-muted-foreground hover:bg-card hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-xs text-foreground truncate">
                      {run.incident_title}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                      {run.status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-muted-foreground">
                    <span>{run.step_count} steps</span>
                    <span>{run.total_tokens_used} tok</span>
                    <span className="text-purple-400 font-semibold">${run.estimated_cost_usd?.toFixed(4)}</span>
                  </div>

                  <div className="mt-1.5 text-[10px] text-muted-foreground/60 flex items-center justify-between font-mono">
                    <span>ID: {run.id.substring(0, 8)}...</span>
                    <span>{new Date(run.started_at).toLocaleTimeString()}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Columns: Selected Run Trace & Events */}
        <div className="lg:col-span-2 space-y-4">
          {selectedRun ? (
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
              {/* Header Bar */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-foreground">
                      {selectedRun.incident_title}
                    </h2>
                    <Link
                      href={`/incidents/${selectedRun.incident_id}`}
                      className="text-xs text-primary hover:underline flex items-center gap-1 font-mono"
                    >
                      <span>Incident View</span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono mt-1">
                    <span>Run ID: {selectedRun.id}</span>
                    <span>•</span>
                    <span>Workflow: {selectedRun.workflow_name}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right font-mono text-xs">
                    <span className="text-muted-foreground block text-[10px] uppercase">Cost Billed</span>
                    <span className="text-purple-400 font-bold">${selectedRun.estimated_cost_usd?.toFixed(4)}</span>
                  </div>
                  <div className="h-6 w-px bg-border" />
                  <div className="text-right font-mono text-xs">
                    <span className="text-muted-foreground block text-[10px] uppercase">Tokens</span>
                    <span className="text-cyan-400 font-bold">{selectedRun.total_tokens_used}</span>
                  </div>
                </div>
              </div>

              {/* Chronological Agent Event Log */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                  <Clock className="h-3.5 w-3.5 text-primary" />
                  Step-by-Step Agent Telemetry Stream ({selectedRun.events?.length || 0})
                </h3>

                <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-2">
                  {selectedRun.events?.map((ev, idx) => (
                    <div
                      key={ev.id || idx}
                      className="p-3 rounded-lg bg-secondary/30 border border-border/60 flex items-start gap-3 hover:border-border transition-colors text-xs"
                    >
                      <div className="h-6 w-6 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-mono text-[10px] shrink-0 mt-0.5">
                        {ev.step_index || idx + 1}
                      </div>

                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-foreground font-mono text-[11px]">
                            {ev.agent_name}
                          </span>
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {ev.duration_ms ? `${ev.duration_ms}ms` : "0.5s"}
                          </span>
                        </div>
                        <p className="text-zinc-300 font-mono text-[11px] leading-relaxed">
                          {ev.message}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sandboxed Validation Results Snapshot */}
              {selectedRun.graph_state?.validation && (
                <div className="p-4 rounded-xl bg-black/40 border border-border space-y-2 font-mono text-xs">
                  <div className="flex items-center justify-between text-muted-foreground pb-2 border-b border-border/40">
                    <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                      <Terminal className="h-3.5 w-3.5" />
                      Sandboxed Pytest Execution Output
                    </span>
                    <span>
                      {selectedRun.graph_state.validation.duration_seconds}s execution
                    </span>
                  </div>
                  <pre className="text-zinc-300 text-[11px] overflow-x-auto whitespace-pre-wrap max-h-32">
                    {selectedRun.graph_state.validation.stdout || selectedRun.graph_state.validation.summary}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="p-16 text-center border border-dashed border-border rounded-xl bg-card/30">
              <Bot className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm font-medium text-foreground">Select an investigation run</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                Click any investigation on the left to inspect its stateful LangGraph node execution, agent reasoning, and validation telemetry.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
