"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import {
  IncidentDetail,
  InvestigationReport,
  Patch,
  IncidentEvent,
  IncidentLog,
  IncidentTrace,
} from "@/lib/types";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { formatSeverityColor, formatStatusColor, formatRelativeTime } from "@/lib/utils";
import {
  AlertTriangle,
  ArrowLeft,
  Bot,
  CheckCircle2,
  Clock,
  Code,
  FileCode,
  GitCommit,
  GitPullRequest,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Terminal,
  Activity,
  Layers,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";

type TabType = "overview" | "logs" | "traces" | "evidence" | "patch" | "timeline";

export default function IncidentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const incidentId = resolvedParams.id;

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [patch, setPatch] = useState<Patch | null>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  // Approval form state
  const [approvalAction, setApprovalAction] = useState<"approved" | "rejected">("approved");
  const [approvalFeedback, setApprovalFeedback] = useState<string>("");
  const [createPR, setCreatePR] = useState<boolean>(true);
  const [isSubmittingApproval, setIsSubmittingApproval] = useState<boolean>(false);

  // Resolution modal state
  const [showResolveModal, setShowResolveModal] = useState<boolean>(false);
  const [resolutionText, setResolutionText] = useState<string>("");

  const loadIncidentData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [incData, reportData, patchData, evidenceData] = await Promise.all([
        api.getIncidentById(incidentId),
        api.getIncidentReport(incidentId).catch(() => null),
        api.getIncidentPatch(incidentId).catch(() => null),
        api.getIncidentEvidence(incidentId).catch(() => []),
      ]);
      setIncident(incData);
      setReport(reportData);
      setPatch(patchData);
      setEvidence(evidenceData);
    } catch (err) {
      console.error("Failed to load incident detail:", err);
    } finally {
      setIsLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    loadIncidentData();
  }, [loadIncidentData]);

  // Real-time synchronization for this incident
  useWebSocket({
    channel: incidentId,
    onMessage: (msg) => {
      if (
        msg.type === "incident_updated" ||
        msg.type === "agent_event" ||
        msg.type === "log_ingested" ||
        msg.type === "trace_ingested" ||
        msg.type === "patch_decision" ||
        msg.type === "incident_resolved" ||
        msg.type === "incident_reopened"
      ) {
        loadIncidentData();
      }
    },
  });

  const handleStartInvestigation = async () => {
    try {
      setIsInvestigating(true);
      await api.startInvestigation(incidentId);
      loadIncidentData();
    } catch (err) {
      console.error("Failed to start investigation:", err);
    } finally {
      setIsInvestigating(false);
    }
  };

  const handleApprovePatch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmittingApproval(true);
      await api.approvePatch(incidentId, {
        action: approvalAction,
        feedback: approvalFeedback,
        create_github_pr: createPR,
      });
      loadIncidentData();
    } catch (err) {
      console.error("Approval failed:", err);
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  const handleResolve = async () => {
    if (!resolutionText.trim()) return;
    try {
      await api.resolveIncident(incidentId, resolutionText);
      setShowResolveModal(false);
      loadIncidentData();
    } catch (err) {
      console.error("Resolution failed:", err);
    }
  };

  const handleReopen = async () => {
    try {
      await api.reopenIncident(incidentId);
      loadIncidentData();
    } catch (err) {
      console.error("Reopen failed:", err);
    }
  };

  if (isLoading && !incident) {
    return (
      <div className="h-96 flex items-center justify-center text-xs text-muted-foreground gap-2">
        <RefreshCw className="h-4 w-4 animate-spin text-primary" />
        <span>Loading incident {incidentId} workspace...</span>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="p-8 text-center text-xs text-muted-foreground">
        Incident not found. <Link href="/incidents" className="text-primary underline">Back to incidents</Link>
      </div>
    );
  }

  const isResolved = incident.status === "Resolved";

  return (
    <div className="space-y-6">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Link href="/incidents" className="hover:text-foreground flex items-center gap-1 transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Incident Command</span>
        </Link>
        <span>/</span>
        <span className="font-mono text-zinc-300 font-medium">{incident.id}</span>
      </div>

      {/* Incident Header Card */}
      <div className="p-6 rounded-xl border border-border bg-card/50 backdrop-blur-md space-y-4 shadow-lg">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-sm font-bold text-zinc-300">{incident.id}</span>
              <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${formatSeverityColor(incident.severity)}`}>
                {incident.severity}
              </span>
              <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${formatStatusColor(incident.status)}`}>
                {incident.status}
              </span>
              <span className="text-[11px] text-muted-foreground font-mono">
                Detected via {incident.detection_source}
              </span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-foreground">{incident.title}</h1>
            <p className="text-xs text-muted-foreground max-w-3xl leading-relaxed">{incident.description}</p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 shrink-0">
            {isResolved ? (
              <button
                onClick={handleReopen}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-secondary/80 hover:bg-secondary text-xs font-semibold text-zinc-200 transition-colors"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reopen Case</span>
              </button>
            ) : (
              <button
                onClick={() => setShowResolveModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-800/80 bg-emerald-950/40 hover:bg-emerald-950/70 text-xs font-semibold text-emerald-400 transition-colors"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Mark Resolved</span>
              </button>
            )}

            <button
              onClick={handleStartInvestigation}
              disabled={isInvestigating}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all disabled:opacity-50"
            >
              <Bot className={`h-4 w-4 ${isInvestigating ? "animate-spin" : ""}`} />
              <span>{isInvestigating ? "Agents Investigating..." : "Launch AI Agents"}</span>
            </button>
          </div>
        </div>

        {/* Metadata Summary Banner */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-border/60 text-xs">
          <div>
            <span className="text-muted-foreground block text-[11px]">Affected Services</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {incident.affected_services.map((svc) => (
                <span key={svc} className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-secondary text-zinc-300 border border-border">
                  {svc}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="text-muted-foreground block text-[11px]">Observed Error Rate</span>
            <span className="font-mono font-semibold text-sm text-red-400 mt-1 block">{incident.error_rate}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[11px]">Start Time</span>
            <span className="font-mono text-zinc-300 mt-1 block">{new Date(incident.start_time).toLocaleString()}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[11px]">Resolution Status</span>
            <span className="font-medium text-zinc-300 mt-1 block">
              {incident.resolved_at ? `Resolved ${formatRelativeTime(incident.resolved_at)}` : "Active Investigation"}
            </span>
          </div>
        </div>
      </div>

      {/* Accessible Tab Navigation */}
      <div className="border-b border-border">
        <div role="tablist" aria-label="Incident details navigation" className="flex items-center gap-1 overflow-x-auto">
          {[
            { id: "overview", label: "Root Cause & Overview", icon: Sparkles },
            { id: "logs", label: `Error Logs (${incident.logs.length})`, icon: Terminal },
            { id: "traces", label: `Distributed Traces (${incident.traces.length})`, icon: Activity },
            { id: "evidence", label: `Technical Evidence (${evidence.length})`, icon: Layers },
            { id: "patch", label: "Patch & Sandbox", icon: Code },
            { id: "timeline", label: `Timeline (${incident.events.length})`, icon: Clock },
          ].map((tab) => {
            const isSelected = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                role="tab"
                id={`tab-${tab.id}`}
                aria-selected={isSelected}
                aria-controls={`panel-${tab.id}`}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
                  isSelected
                    ? "border-primary text-primary font-semibold bg-primary/5"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-zinc-700"
                }`}
              >
                <Icon className={`h-4 w-4 ${isSelected ? "text-primary" : "text-muted-foreground"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panels */}

      {/* TAB 1: OVERVIEW & ROOT CAUSE */}
      {activeTab === "overview" && (
        <div role="tabpanel" id="panel-overview" aria-labelledby="tab-overview" className="space-y-6">
          {report ? (
            <div className="p-6 rounded-xl border border-indigo-900/50 bg-indigo-950/10 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                  <Sparkles className="h-4 w-4" />
                  <span>Autonomous Root Cause Analysis</span>
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-950/80 border border-indigo-800 text-indigo-300 text-xs font-mono font-semibold">
                  <span>Confidence: {(report.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div>
                <h3 className="text-base font-semibold text-foreground mb-1">Primary Identified Culprit</h3>
                <p className="text-xs text-zinc-300 leading-relaxed font-mono bg-card/80 p-3 rounded-lg border border-border">
                  {report.primary_root_cause}
                </p>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                  Executive Summary
                </h3>
                <p className="text-xs text-zinc-300 leading-relaxed">{report.executive_summary}</p>
              </div>

              {report.regression_risks?.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span>Regression Risks & Side Effects</span>
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-xs text-zinc-400">
                    {report.regression_risks.map((risk, i) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}

              {report.recommended_next_steps?.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Recommended Engineering Remediations</span>
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-xs text-zinc-400">
                    {report.recommended_next_steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 rounded-xl border border-dashed border-border text-center space-y-3">
              <Bot className="h-8 w-8 text-muted-foreground mx-auto" />
              <div>
                <h3 className="text-sm font-semibold text-foreground">No Root Cause Report Yet</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Launch the multi-agent orchestration workflow to inspect logs, analyze AST repository code, and synthesize verified root causes.
                </p>
              </div>
              <button
                onClick={handleStartInvestigation}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold shadow-sm"
              >
                <Bot className="h-3.5 w-3.5" />
                <span>Begin Autonomous Investigation</span>
              </button>
            </div>
          )}

          {/* Quick Technical Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-border bg-card/40 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                <Terminal className="h-4 w-4 text-amber-400" />
                <span>Log Anomalies</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {incident.logs.length} structured log events captured around failure window.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-card/40 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                <Activity className="h-4 w-4 text-cyan-400" />
                <span>Distributed Spans</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {incident.traces.length} OpenTelemetry trace spans correlated to this failure pattern.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-card/40 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <span>Sandbox Patch Isolation</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {patch ? `Patch ${patch.status} with ${patch.validations.length} validations.` : "Awaiting patch generation step."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ERROR LOGS */}
      {activeTab === "logs" && (
        <div role="tabpanel" id="panel-logs" aria-labelledby="tab-logs" className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Displaying {incident.logs.length} correlated log events</span>
          </div>

          <div className="space-y-2">
            {incident.logs.map((log) => {
              const isExpanded = expandedLogId === log.id;
              const isError = log.level === "ERROR" || log.level === "FATAL";
              return (
                <div
                  key={log.id}
                  className={`border rounded-lg p-3 text-xs transition-colors bg-card/40 ${
                    isError ? "border-red-900/40 hover:border-red-800/80" : "border-border hover:border-zinc-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold uppercase ${
                          isError ? "bg-red-950/80 text-red-400 border border-red-800" : "bg-amber-950/80 text-amber-400 border border-amber-800"
                        }`}
                      >
                        {log.level}
                      </span>
                      <span className="font-mono text-zinc-400 font-semibold">{log.service_name}</span>
                      <span className="text-muted-foreground font-mono text-[11px]">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    {log.stack_trace && (
                      <button
                        onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                        className="text-[11px] text-zinc-400 hover:text-foreground flex items-center gap-1 font-mono"
                      >
                        <span>{isExpanded ? "Hide Trace" : "View Stack Trace"}</span>
                        {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      </button>
                    )}
                  </div>

                  <p className="mt-1.5 font-mono text-zinc-200 leading-relaxed break-words">{log.message}</p>

                  {isExpanded && log.stack_trace && (
                    <div className="mt-3 p-3 rounded-md bg-black/60 border border-border text-[11px] font-mono text-red-300 overflow-x-auto whitespace-pre">
                      {log.stack_trace}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 3: DISTRIBUTED TRACES */}
      {activeTab === "traces" && (
        <div role="tabpanel" id="panel-traces" aria-labelledby="tab-traces" className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>OpenTelemetry Distributed Trace Spans Waterfall</span>
          </div>

          <div className="border border-border rounded-xl bg-card/40 p-4 space-y-3">
            {incident.traces.map((trace, idx) => {
              const maxDuration = Math.max(...incident.traces.map((t) => t.duration_ms), 100);
              const barWidth = Math.max(10, Math.min(100, (trace.duration_ms / maxDuration) * 100));

              return (
                <div key={trace.id} className="space-y-1.5 border-b border-border/50 pb-3 last:border-0 last:pb-0">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-zinc-500">Span #{idx + 1}</span>
                      <span className="font-semibold text-zinc-200">{trace.operation_name}</span>
                      <span className="font-mono text-[11px] px-1.5 py-0.2 rounded bg-secondary text-zinc-400">
                        {trace.service_name}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 font-mono text-xs">
                      <span className={trace.status_code === "500" || trace.status_code === "ERROR" ? "text-red-400 font-bold" : "text-emerald-400"}>
                        {trace.status_code}
                      </span>
                      <span className="text-zinc-300 font-semibold">{trace.duration_ms.toFixed(1)}ms</span>
                    </div>
                  </div>

                  {/* Waterfall Latency Bar */}
                  <div className="w-full bg-secondary/50 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        trace.status_code === "500" || trace.status_code === "ERROR"
                          ? "bg-red-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>

                  {trace.error_message && (
                    <p className="text-[11px] font-mono text-red-400 mt-1">Error: {trace.error_message}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: TECHNICAL EVIDENCE */}
      {activeTab === "evidence" && (
        <div role="tabpanel" id="panel-evidence" aria-labelledby="tab-evidence" className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Verified Technical Evidence vs AI Hypotheses</span>
          </div>

          {evidence.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground border border-dashed border-border rounded-xl">
              No evidence indexed yet. Run the code investigation agent to extract attributed code snippets.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {evidence.map((ev) => (
                <div key={ev.id} className="p-4 rounded-xl border border-border bg-card/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-mono bg-primary/10 text-primary border border-primary/20">
                      {ev.source_type}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                      {ev.is_verified}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-foreground">{ev.title}</h3>
                  <p className="text-xs text-muted-foreground">{ev.description}</p>

                  {ev.file_path && (
                    <div className="font-mono text-[11px] text-zinc-400 bg-secondary/60 p-2 rounded border border-border">
                      {ev.file_path} {ev.line_range && `:${ev.line_range}`}
                    </div>
                  )}

                  {ev.raw_content && (
                    <pre className="text-[11px] font-mono p-2.5 rounded bg-black/60 border border-border text-zinc-300 overflow-x-auto">
                      {ev.raw_content}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 5: PATCH & SANDBOX VALIDATION */}
      {activeTab === "patch" && (
        <div role="tabpanel" id="panel-patch" aria-labelledby="tab-patch" className="space-y-6">
          {patch ? (
            <div className="space-y-6">
              {/* Patch Summary Card */}
              <div className="p-5 rounded-xl border border-border bg-card/40 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-foreground">{patch.title}</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">{patch.explanation}</p>
                  </div>
                  <span className="px-2.5 py-1 rounded text-xs font-semibold uppercase bg-indigo-950/80 text-indigo-400 border border-indigo-800">
                    {patch.status}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                  <span>Affected files:</span>
                  {patch.affected_files.map((f) => (
                    <span key={f} className="px-1.5 py-0.2 rounded bg-secondary text-zinc-200 border border-border">
                      {f}
                    </span>
                  ))}
                </div>
              </div>

              {/* Code Diff Viewer */}
              <div className="rounded-xl border border-border bg-black/80 overflow-hidden shadow-lg">
                <div className="px-4 py-2 border-b border-border bg-card/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-zinc-300 font-mono">
                    <FileCode className="h-4 w-4 text-primary" />
                    <span>Unified Git Diff</span>
                  </div>
                  <span className="text-[11px] text-muted-foreground font-mono">Monaco Diff Formatter</span>
                </div>
                <pre className="p-4 text-xs font-mono text-zinc-200 overflow-x-auto leading-relaxed">
                  {patch.diff_content.split("\n").map((line, idx) => {
                    const isAdd = line.startsWith("+") && !line.startsWith("+++");
                    const isDel = line.startsWith("-") && !line.startsWith("---");
                    const isHeader = line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++");

                    return (
                      <div
                        key={idx}
                        className={`${
                          isAdd ? "bg-emerald-950/40 text-emerald-300" : isDel ? "bg-red-950/40 text-red-300" : isHeader ? "text-cyan-400 font-bold" : "text-zinc-300"
                        } px-2 py-0.5`}
                      >
                        {line}
                      </div>
                    );
                  })}
                </pre>
              </div>

              {/* Sandbox Execution Validation Card */}
              {patch.validations.length > 0 && (
                <div className="p-5 rounded-xl border border-emerald-900/50 bg-emerald-950/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                      <ShieldCheck className="h-4 w-4" />
                      <span>Isolated Docker Sandbox Test Verification</span>
                    </div>
                    <span className="text-xs font-mono text-emerald-400 font-semibold uppercase">
                      Status: {patch.validations[0].status}
                    </span>
                  </div>

                  <p className="text-xs text-zinc-300">{patch.validations[0].validation_summary}</p>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono bg-card/60 p-3 rounded-lg border border-border">
                    <div>
                      <span className="text-muted-foreground block text-[10px]">Total Tests</span>
                      <span className="font-semibold text-zinc-200">{patch.validations[0].total_tests}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[10px]">Passed</span>
                      <span className="font-semibold text-emerald-400">{patch.validations[0].passed_tests}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[10px]">Execution Time</span>
                      <span className="font-semibold text-zinc-200">{patch.validations[0].execution_time_seconds}s</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[10px]">Peak Memory</span>
                      <span className="font-semibold text-zinc-200">{patch.validations[0].memory_peak_mb} MB</span>
                    </div>
                  </div>

                  {patch.validations[0].stdout_output && (
                    <div className="mt-2">
                      <span className="text-[11px] font-mono text-muted-foreground block mb-1">Sandbox stdout:</span>
                      <pre className="p-3 rounded-md bg-black/70 border border-border text-[11px] font-mono text-zinc-300 overflow-x-auto whitespace-pre">
                        {patch.validations[0].stdout_output}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Human Approval Gate */}
              <div className="p-5 rounded-xl border border-border bg-card/60 space-y-4">
                <div className="flex items-center justify-between border-b border-border/60 pb-3">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-amber-400" />
                    <h3 className="text-sm font-semibold text-foreground">Human-in-the-Loop Approval Gate</h3>
                  </div>
                  <span className="text-[11px] text-muted-foreground">Production Code Guard</span>
                </div>

                <p className="text-xs text-muted-foreground">
                  The system enforces that AI never automatically deploys code to production. An engineer must review the unified diff, review sandbox validation results, and sign off.
                </p>

                {patch.github_pr_url ? (
                  <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-xs text-emerald-300 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <GitPullRequest className="h-4 w-4" />
                      <span>Pull Request Created: {patch.github_pr_url}</span>
                    </div>
                    <a
                      href={patch.github_pr_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-semibold underline"
                    >
                      <span>Open on GitHub</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                ) : (
                  <form onSubmit={handleApprovePatch} className="space-y-3 text-xs">
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="approval"
                          value="approved"
                          checked={approvalAction === "approved"}
                          onChange={() => setApprovalAction("approved")}
                          className="text-primary"
                        />
                        <span className="font-semibold text-emerald-400">Approve Resolution</span>
                      </label>

                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="approval"
                          value="rejected"
                          checked={approvalAction === "rejected"}
                          onChange={() => setApprovalAction("rejected")}
                          className="text-primary"
                        />
                        <span className="font-semibold text-red-400">Reject Resolution</span>
                      </label>
                    </div>

                    <div>
                      <label className="block text-zinc-300 mb-1">Reviewer Feedback & Audit Comments</label>
                      <textarea
                        rows={2}
                        value={approvalFeedback}
                        onChange={(e) => setApprovalFeedback(e.target.value)}
                        placeholder="Add engineering review sign-off notes..."
                        className="w-full px-3 py-2 rounded-md bg-secondary/50 border border-border text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                      />
                    </div>

                    {approvalAction === "approved" && (
                      <label className="flex items-center gap-2 text-zinc-300 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={createPR}
                          onChange={(e) => setCreatePR(e.target.checked)}
                          className="rounded text-primary"
                        />
                        <span>Create GitHub Pull Request upon approval</span>
                      </label>
                    )}

                    <div className="flex items-center justify-end pt-2">
                      <button
                        type="submit"
                        disabled={isSubmittingApproval}
                        className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-white font-semibold shadow-md transition-all disabled:opacity-50 ${
                          approvalAction === "approved"
                            ? "bg-emerald-600 hover:bg-emerald-500"
                            : "bg-red-600 hover:bg-red-500"
                        }`}
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        <span>{isSubmittingApproval ? "Submitting..." : `Submit Decision (${approvalAction.toUpperCase()})`}</span>
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl border border-dashed border-border text-center space-y-3">
              <Code className="h-8 w-8 text-muted-foreground mx-auto" />
              <div>
                <h3 className="text-sm font-semibold text-foreground">No Patch Generated Yet</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Launch the multi-agent orchestration workflow to let the Fix Generation Agent construct a minimal unified diff.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 6: TIMELINE & AUDIT TRAIL */}
      {activeTab === "timeline" && (
        <div role="tabpanel" id="panel-timeline" aria-labelledby="tab-timeline" className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Chronological Incident Audit History</span>
          </div>

          <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
            {incident.events.map((ev) => (
              <div key={ev.id} className="relative space-y-1">
                <span className="absolute -left-6 top-1 h-2.5 w-2.5 rounded-full bg-primary border-2 border-background" />
                <div className="flex items-center gap-2 text-xs">
                  <span className="font-semibold text-foreground">{ev.actor}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-secondary text-zinc-400">
                    {ev.event_type}
                  </span>
                  <span className="text-[11px] text-muted-foreground font-mono">
                    {formatRelativeTime(ev.created_at)}
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed">{ev.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal: Mark Resolved */}
      {showResolveModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-semibold text-foreground">Resolve Incident</h3>
            <p className="text-xs text-muted-foreground">
              Provide a brief summary of how this incident was mitigated or resolved.
            </p>
            <textarea
              rows={3}
              value={resolutionText}
              onChange={(e) => setResolutionText(e.target.value)}
              placeholder="e.g., Connection pool leak fixed in db.py and verified via sandbox test suite."
              className="w-full px-3 py-2 rounded-md bg-secondary/50 border border-border text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary resize-none"
            />
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowResolveModal(false)}
                className="px-3 py-1.5 rounded-md border border-border text-zinc-400 hover:text-foreground text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                className="px-4 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs"
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
