"use client";

import Link from "next/link";
import { Incident } from "@/lib/types";
import { formatSeverityColor, formatStatusColor, formatRelativeTime } from "@/lib/utils";
import { ArrowRight, Bot, ShieldAlert } from "lucide-react";

interface RecentIncidentsTableProps {
  incidents: Incident[];
  onInvestigate?: (incidentId: string) => void;
}

export function RecentIncidentsTable({ incidents, onInvestigate }: RecentIncidentsTableProps) {
  if (incidents.length === 0) {
    return (
      <div className="p-8 text-center text-xs text-muted-foreground border border-dashed border-border rounded-lg">
        No incidents detected. System is running cleanly.
      </div>
    );
  }

  return (
    <div
      tabIndex={0}
      role="region"
      aria-labelledby="recent-incidents-caption"
      className="table-wrapper border border-border/80 rounded-lg overflow-x-auto"
    >
      <table className="w-full text-left text-xs text-foreground">
        <caption id="recent-incidents-caption" className="sr-only">
          Production Incidents Overview
        </caption>
        <thead className="text-[11px] uppercase tracking-wider text-muted-foreground border-b border-border">
          <tr>
            <th scope="col" className="px-4 py-3 font-semibold">Incident ID & Title</th>
            <th scope="col" className="px-4 py-3 font-semibold">Severity</th>
            <th scope="col" className="px-4 py-3 font-semibold">Status</th>
            <th scope="col" className="px-4 py-3 font-semibold">Affected Services</th>
            <th scope="col" className="px-4 py-3 font-semibold">Error Rate</th>
            <th scope="col" className="px-4 py-3 font-semibold">Detected</th>
            <th scope="col" className="px-4 py-3 text-right font-semibold">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {incidents.slice(0, 8).map((inc) => (
            <tr
              key={inc.id}
              className="hover:bg-muted/40 transition-colors group cursor-pointer"
            >
              <th scope="row" className="px-4 py-3 font-medium">
                <Link href={`/incidents/${inc.id}`} className="block">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-zinc-400 font-semibold">{inc.id}</span>
                  </div>
                  <div className="font-medium text-foreground group-hover:text-primary transition-colors truncate max-w-xs mt-0.5">
                    {inc.title}
                  </div>
                </Link>
              </th>

              <td className="px-4 py-3">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${formatSeverityColor(
                    inc.severity
                  )}`}
                >
                  {inc.severity}
                </span>
              </td>

              <td className="px-4 py-3">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border ${formatStatusColor(
                    inc.status
                  )}`}
                >
                  {inc.status}
                </span>
              </td>

              <td className="px-4 py-3">
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

              <td className="px-4 py-3 font-mono text-xs font-semibold text-zinc-300">
                {inc.error_rate}
              </td>

              <td className="px-4 py-3 text-muted-foreground font-mono text-[11px]">
                {formatRelativeTime(inc.start_time)}
              </td>

              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-2">
                  {onInvestigate && inc.status === "Detected" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onInvestigate(inc.id);
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/40 text-[11px] font-medium transition-colors"
                    >
                      <Bot className="h-3 w-3" />
                      Investigate
                    </button>
                  )}
                  <Link
                    href={`/incidents/${inc.id}`}
                    className="p-1 rounded text-zinc-400 hover:text-foreground hover:bg-secondary transition-colors"
                    title="View Incident Details"
                  >
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
