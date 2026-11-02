"use client";

import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { IncidentSeverity } from "@/lib/types";

interface SeverityPieChartProps {
  distribution?: Record<IncidentSeverity, number>;
}

const COLORS: Record<IncidentSeverity, string> = {
  Critical: "#ef4444",
  High: "#f59e0b",
  Medium: "#eab308",
  Low: "#10b981",
};

export function SeverityPieChart({ distribution }: SeverityPieChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const data = [
    { name: "Critical", value: distribution?.Critical || 0 },
    { name: "High", value: distribution?.High || 0 },
    { name: "Medium", value: distribution?.Medium || 0 },
    { name: "Low", value: distribution?.Low || 0 },
  ].filter((item) => item.value > 0);

  if (!mounted) {
    return (
      <div className="h-[220px] flex items-center justify-center text-xs text-muted-foreground">
        Loading breakdown...
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="h-[220px] flex items-center justify-center text-xs text-muted-foreground">
        No incidents to display
      </div>
    );
  }

  return (
    <div className="h-[220px] w-full flex items-center justify-between">
      <div className="h-full w-1/2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              innerRadius={50}
              outerRadius={75}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell
                  key={`cell-${entry.name}`}
                  fill={COLORS[entry.name as IncidentSeverity] || "#71717a"}
                  stroke="#18181b"
                  strokeWidth={2}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "#09090b",
                borderColor: "#27272a",
                borderRadius: "8px",
                fontSize: "12px",
                color: "#fafafa",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="w-1/2 space-y-2 pr-2">
        {data.map((entry) => (
          <div key={entry.name} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-sm"
                style={{ backgroundColor: COLORS[entry.name as IncidentSeverity] }}
              />
              <span className="text-zinc-300">{entry.name}</span>
            </div>
            <span className="font-semibold text-foreground font-mono">{entry.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
