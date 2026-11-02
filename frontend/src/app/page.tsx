"use client";

import { useEffect, useState, useCallback } from "react";
import { DashboardMetrics, Incident } from "@/lib/types";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { MetricCards } from "@/components/dashboard/MetricCards";
import { IncidentTrendsChart } from "@/components/dashboard/IncidentTrendsChart";
import { SeverityPieChart } from "@/components/dashboard/SeverityPieChart";
import { ServiceHealthGrid } from "@/components/dashboard/ServiceHealthGrid";
import { AgentActivityStream } from "@/components/dashboard/AgentActivityStream";
import { RecentIncidentsTable } from "@/components/dashboard/RecentIncidentsTable";
import { PlusCircle, RefreshCw, Sparkles, AlertTriangle, ShieldCheck } from "lucide-react";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newSeverity, setNewSeverity] = useState("High");
  const [newService, setNewService] = useState("checkout-service");

  const loadData = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const [metricsData, incidentsData] = await Promise.all([
        api.getMetrics(),
        api.getIncidents({ limit: 15 }),
      ]);
      setMetrics(metricsData);
      setIncidents(incidentsData);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // WebSocket for real-time reactivity
  useWebSocket({
    channel: "global",
    onMessage: (msg) => {
      if (
        msg.type === "incident_created" ||
        msg.type === "incident_updated" ||
        msg.type === "agent_event" ||
        msg.type === "patch_decision"
      ) {
        loadData();
      }
    },
  });

  const handleCreateSynthetic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      await api.createIncident({
        title: newTitle,
        description: newDescription || "Triggered by production simulation monitor",
        severity: newSeverity,
        affected_services: [newService],
        error_rate: "14.2%",
        detection_source: "Synthetic Chaos Injector",
        initial_log_message: `Synthetic incident generated for ${newService}`,
      });
      setShowCreateModal(false);
      setNewTitle("");
      setNewDescription("");
      loadData();
    } catch (err) {
      console.error("Failed to create incident:", err);
    }
  };

  const handleQuickInvestigate = async (incidentId: string) => {
    try {
      await api.startInvestigation(incidentId);
      loadData();
    } catch (err) {
      console.error("Failed to start investigation:", err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Title & Action Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>Production Overview</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-400">
              Live Telemetry
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Real-time autonomous incident investigation, correlation engine, and sandboxed validation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData()}
            disabled={isRefreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-card/60 hover:bg-secondary text-xs font-medium text-muted-foreground hover:text-foreground transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin text-primary" : ""}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold shadow-sm transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Trigger Synthetic Incident</span>
          </button>
        </div>
      </div>

      {/* Top Metric Cards */}
      <MetricCards metrics={metrics} isLoading={isLoading} />

      {/* Service Health Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Microservice Health Status</span>
          </h2>
          <span className="text-[11px] text-muted-foreground font-mono">
            4 / 4 Services Monitored
          </span>
        </div>
        <ServiceHealthGrid services={metrics?.service_health} />
      </div>

      {/* Charts Section: Incident Trends & Severity Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-5 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Incident Velocity & Resolution Rate</h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">7-Day trend of detected vs resolved production events</p>
            </div>
            <span className="text-xs font-mono text-zinc-400">Past 7 Days</span>
          </div>
          <IncidentTrendsChart trends={metrics?.incident_trends} />
        </div>

        <div className="p-5 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Severity Distribution</h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">Categorization across active and historical cases</p>
            </div>
          </div>
          <SeverityPieChart distribution={metrics?.severity_distribution} />
        </div>
      </div>

      {/* Bottom Grid: Recent Incidents & Agent Execution Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              <span>Recent Production Incidents</span>
            </h2>
            <span className="text-xs text-muted-foreground font-mono">{incidents.length} Recorded</span>
          </div>
          <RecentIncidentsTable incidents={incidents} onInvestigate={handleQuickInvestigate} />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-400" />
              <span>AI Agent Activity Stream</span>
            </h2>
            <span className="text-[11px] font-mono text-emerald-400 animate-pulse">● Live</span>
          </div>
          <div className="p-3 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
            <AgentActivityStream activities={metrics?.recent_agent_activity} />
          </div>
        </div>
      </div>

      {/* Modal: Trigger Synthetic Incident */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span>Trigger Production Incident</span>
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-mono"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSynthetic} className="space-y-4 text-xs">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Incident Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Redis Connection Pool Starvation in checkout-service"
                  className="w-full px-3 py-2 rounded-md bg-secondary/60 border border-border text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Affected Service</label>
                <select
                  value={newService}
                  onChange={(e) => setNewService(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-secondary/60 border border-border text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="checkout-service">checkout-service (Tier 1 / Critical)</option>
                  <option value="payment-service">payment-service (Tier 1 / Critical)</option>
                  <option value="inventory-service">inventory-service (Tier 2 / Standard)</option>
                  <option value="order-service">order-service (Tier 1 / Critical)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Severity</label>
                <select
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-secondary/60 border border-border text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="Critical">Critical (P0)</option>
                  <option value="High">High (P1)</option>
                  <option value="Medium">Medium (P2)</option>
                  <option value="Low">Low (P3)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Description / Error Details</label>
                <textarea
                  rows={3}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Provide simulated error stack or symptoms..."
                  className="w-full px-3 py-2 rounded-md bg-secondary/60 border border-border text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 rounded-md border border-border text-zinc-400 hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-md bg-primary hover:bg-primary/90 text-primary-foreground font-semibold"
                >
                  Inject Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
