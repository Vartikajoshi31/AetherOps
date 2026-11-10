"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { Incident, IncidentSeverity, IncidentStatus } from "@/lib/types";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { formatSeverityColor, formatStatusColor, formatRelativeTime } from "@/lib/utils";
import {
  AlertTriangle,
  Search,
  Filter,
  PlusCircle,
  RefreshCw,
  RotateCcw,
  Sparkles,
  ArrowUpDown,
  ChevronRight,
  ChevronLeft,
  Bot,
  Zap,
  CheckCircle2,
  SlidersHorizontal
} from "lucide-react";

const ALL_STATUSES = [
  "all",
  "Detected",
  "Investigating",
  "Root Cause Identified",
  "Fix Generated",
  "Validating",
  "Awaiting Approval",
  "Resolved",
  "Failed",
];

const ALL_SEVERITIES = ["all", "Critical", "High", "Medium", "Low"];

const ALL_SERVICES = [
  "all",
  "checkout-service",
  "payment-service",
  "inventory-service",
  "order-service",
];

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [selectedService, setSelectedService] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"time_desc" | "time_asc" | "severity" | "error_rate">("time_desc");
  const [page, setPage] = useState<number>(1);
  const pageSize = 8;

  // Chaos simulation state
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [showSimulateModal, setShowSimulateModal] = useState<boolean>(false);
  const [selectedScenario, setSelectedScenario] = useState<string>("db_pool_exhaustion");
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);

  const loadIncidents = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await api.getIncidents({
        status: selectedStatus !== "all" ? selectedStatus : undefined,
        severity: selectedSeverity !== "all" ? selectedSeverity : undefined,
        service: selectedService !== "all" ? selectedService : undefined,
        search: search.trim() ? search.trim() : undefined,
      });
      setIncidents(data);
    } catch (err) {
      console.error("Failed to load incidents:", err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedStatus, selectedSeverity, selectedService, search]);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  useEffect(() => {
    api.getChaosScenarios().then(setScenarios).catch(console.error);
  }, []);

  // Real-time synchronization
  useWebSocket({
    channel: "global",
    onMessage: (msg) => {
      if (
        msg.type === "incident_created" ||
        msg.type === "incident_updated" ||
        msg.type === "incident_resolved" ||
        msg.type === "incident_reopened" ||
        msg.type === "incident_deleted" ||
        msg.type === "demo_reset"
      ) {
        loadIncidents();
      }
    },
  });

  const sortedIncidents = useMemo(() => {
    const list = [...incidents];
    switch (sortBy) {
      case "time_desc":
        return list.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());
      case "time_asc":
        return list.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
      case "severity":
        const weight: Record<string, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };
        return list.sort((a, b) => (weight[b.severity] || 0) - (weight[a.severity] || 0));
      case "error_rate":
        return list.sort((a, b) => parseFloat(b.error_rate || "0") - parseFloat(a.error_rate || "0"));
      default:
        return list;
    }
  }, [incidents, sortBy]);

  const totalPages = Math.max(1, Math.ceil(sortedIncidents.length / pageSize));
  const paginatedIncidents = sortedIncidents.slice((page - 1) * pageSize, page * pageSize);

  const handleSimulate = async () => {
    try {
      setIsSimulating(true);
      await api.simulateChaos(selectedScenario);
      setShowSimulateModal(false);
      loadIncidents();
    } catch (err) {
      console.error("Chaos simulation failed:", err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleResetDemo = async () => {
    if (!confirm("Reset all incidents, telemetry logs, and deployments to initial baseline demo state?")) return;
    try {
      setIsResetting(true);
      await api.resetDemo();
      loadIncidents();
    } catch (err) {
      console.error("Demo reset failed:", err);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Action Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>Incident Command Center</span>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-secondary text-zinc-300 border border-border">
              {incidents.length} Total
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Browse, triage, filter, and orchestrate autonomous AI investigations across all services.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleResetDemo}
            disabled={isResetting}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-card/60 hover:bg-secondary text-xs font-medium text-zinc-300 hover:text-foreground transition-all disabled:opacity-50"
            title="Reset telemetry & incidents to clean demo state"
          >
            <RotateCcw className={`h-3.5 w-3.5 ${isResetting ? "animate-spin text-primary" : ""}`} />
            <span>Reset Demo</span>
          </button>

          <button
            onClick={() => setShowSimulateModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-all"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Inject Chaos Incident</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-3">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search incidents by title, description, or ID..."
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-secondary/40 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Service Dropdown */}
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs text-muted-foreground whitespace-nowrap">Service:</label>
            <select
              value={selectedService}
              onChange={(e) => {
                setSelectedService(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-2 rounded-lg bg-secondary/40 border border-border text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {ALL_SERVICES.map((svc) => (
                <option key={svc} value={svc}>
                  {svc === "all" ? "All Services" : svc}
                </option>
              ))}
            </select>
          </div>

          {/* Severity Dropdown */}
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs text-muted-foreground whitespace-nowrap">Severity:</label>
            <select
              value={selectedSeverity}
              onChange={(e) => {
                setSelectedSeverity(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-2 rounded-lg bg-secondary/40 border border-border text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {ALL_SEVERITIES.map((sev) => (
                <option key={sev} value={sev}>
                  {sev === "all" ? "All Severities" : sev}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By Dropdown */}
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs text-muted-foreground whitespace-nowrap">Sort:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-2.5 py-2 rounded-lg bg-secondary/40 border border-border text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="time_desc">Newest First</option>
              <option value="time_asc">Oldest First</option>
              <option value="severity">Highest Severity</option>
              <option value="error_rate">Highest Error Rate</option>
            </select>
          </div>
        </div>

        {/* Status Filter Badges (Horizontal scrollable pill list) */}
        <div className="flex items-center gap-1.5 overflow-x-auto pt-2 border-t border-border/60">
          <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mr-1">
            Status:
          </span>
          {ALL_STATUSES.map((status) => {
            const isSelected = selectedStatus === status;
            return (
              <button
                key={status}
                onClick={() => {
                  setSelectedStatus(status);
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-colors ${
                  isSelected
                    ? "bg-primary text-primary-foreground font-semibold"
                    : "bg-secondary/40 text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
              >
                {status === "all" ? "All Statuses" : status}
              </button>
            );
          })}
        </div>
      </div>

      {/* Incidents Table */}
      <div
        tabIndex={0}
        role="region"
        aria-labelledby="incidents-table-caption"
        className="table-wrapper border border-border/80 rounded-xl bg-card/40 backdrop-blur-sm overflow-x-auto"
      >
        <table className="w-full text-left text-xs text-foreground">
          <caption id="incidents-table-caption" className="sr-only">
            Active and Resolved Production Incidents
          </caption>
          <thead className="text-[11px] uppercase tracking-wider text-muted-foreground border-b border-border bg-card">
            <tr>
              <th scope="col" className="px-4 py-3 font-semibold">Incident Details</th>
              <th scope="col" className="px-4 py-3 font-semibold">Severity</th>
              <th scope="col" className="px-4 py-3 font-semibold">Status</th>
              <th scope="col" className="px-4 py-3 font-semibold">Affected Services</th>
              <th scope="col" className="px-4 py-3 font-semibold">Error Rate</th>
              <th scope="col" className="px-4 py-3 font-semibold">Telemetry Counts</th>
              <th scope="col" className="px-4 py-3 font-semibold">Detected</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-xs text-muted-foreground">
                  <div className="flex items-center justify-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-primary" />
                    <span>Loading incidents from telemetry store...</span>
                  </div>
                </td>
              </tr>
            ) : paginatedIncidents.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-xs text-muted-foreground">
                  No incidents match the active filters.
                </td>
              </tr>
            ) : (
              paginatedIncidents.map((inc) => (
                <tr
                  key={inc.id}
                  className="hover:bg-muted/30 transition-colors group cursor-pointer"
                >
                  <th scope="row" className="px-4 py-3.5 font-medium">
                    <Link href={`/incidents/${inc.id}`} className="block">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-zinc-400 font-semibold">{inc.id}</span>
                        <span className="text-[10px] text-zinc-500 font-normal">
                          via {inc.detection_source}
                        </span>
                      </div>
                      <div className="font-semibold text-foreground group-hover:text-primary transition-colors mt-0.5 max-w-sm truncate">
                        {inc.title}
                      </div>
                    </Link>
                  </th>

                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${formatSeverityColor(
                        inc.severity
                      )}`}
                    >
                      {inc.severity}
                    </span>
                  </td>

                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border ${formatStatusColor(
                        inc.status
                      )}`}
                    >
                      {inc.status}
                    </span>
                  </td>

                  <td className="px-4 py-3.5">
                    <div className="flex flex-wrap gap-1">
                      {(inc.affected_services || []).map((svc) => (
                        <span
                          key={svc}
                          className="px-1.5 py-0.5 rounded bg-secondary/80 text-zinc-300 font-mono text-[10px] border border-border"
                        >
                          {svc}
                        </span>
                      ))}
                    </div>
                  </td>

                  <td className="px-4 py-3.5 font-mono text-xs font-semibold text-zinc-200">
                    {inc.error_rate}
                  </td>

                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
                      <span>{inc.logs_count} logs</span>
                      <span>•</span>
                      <span>{inc.traces_count} traces</span>
                      <span>•</span>
                      <span>{inc.events_count} events</span>
                    </div>
                  </td>

                  <td className="px-4 py-3.5 text-muted-foreground font-mono text-[11px]">
                    {formatRelativeTime(inc.start_time)}
                  </td>

                  <td className="px-4 py-3.5 text-right">
                    <Link
                      href={`/incidents/${inc.id}`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-secondary/80 hover:bg-secondary text-foreground text-xs font-medium border border-border transition-colors"
                    >
                      <span>Investigate</span>
                      <ChevronRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground px-2">
          <div>
            Showing {(page - 1) * pageSize + 1} to{" "}
            {Math.min(page * pageSize, sortedIncidents.length)} of {sortedIncidents.length} incidents
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded border border-border bg-card hover:bg-secondary disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="font-mono text-foreground font-semibold px-2">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded border border-border bg-card hover:bg-secondary disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Chaos Simulator Modal */}
      {showSimulateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
                <Zap className="h-4 w-4 text-indigo-400" />
                <span>Inject Synthetic Chaos Incident</span>
              </h3>
              <button
                onClick={() => setShowSimulateModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-mono"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-muted-foreground">
              Select a realistic production chaos failure mode. The system will synthesize distributed trace spans, error logs, and metrics in the database.
            </p>

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {scenarios.map((sc) => (
                <div
                  key={sc.key}
                  onClick={() => setSelectedScenario(sc.key)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                    selectedScenario === sc.key
                      ? "border-primary bg-primary/10 text-foreground"
                      : "border-border/80 hover:border-zinc-700 bg-secondary/30 text-zinc-300"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-foreground">{sc.title}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-semibold border ${formatSeverityColor(
                        sc.severity
                      )}`}
                    >
                      {sc.severity}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground line-clamp-2">{sc.description}</p>
                  <div className="mt-1 font-mono text-[10px] text-indigo-400">
                    Service: {sc.service}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setShowSimulateModal(false)}
                className="px-3 py-1.5 rounded-md border border-border text-zinc-400 hover:text-foreground text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleSimulate}
                disabled={isSimulating}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50"
              >
                <Zap className="h-3.5 w-3.5" />
                <span>{isSimulating ? "Injecting..." : "Inject Chaos Scenario"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
