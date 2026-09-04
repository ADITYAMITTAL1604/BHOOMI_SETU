import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { QuarterlyProgress } from "@/api/dashboard";

interface AcquisitionProgressChartProps {
  data: QuarterlyProgress[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;

  const acquired = payload.find((p) => p.dataKey === "acquired")?.value || 0;
  const target = payload.find((p) => p.dataKey === "target")?.value || 0;
  const pct = target > 0 ? Math.round((acquired / target) * 100) : 0;

  return (
    <div className="bg-white/95 backdrop-blur-md rounded-xl border border-gray-200/90 shadow-xl p-3.5 min-w-[190px] animate-fade-in text-xs">
      <div className="flex items-center justify-between border-b border-gray-100 pb-2 mb-2.5">
        <span className="font-bold text-gray-800 tracking-tight">{label}</span>
        <span
          className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${
            pct >= 70
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : pct >= 40
              ? "bg-amber-50 text-amber-700 border border-amber-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {pct}% Met
        </span>
      </div>
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-gray-500 font-medium">
            <span className="w-2 h-2 rounded-full bg-[#D47A22]" />
            Acquired
          </span>
          <span className="font-semibold text-gray-900">{Number(acquired).toLocaleString("en-IN")} ha</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-gray-500 font-medium">
            <span className="w-2 h-2 rounded-full bg-[#439288]" />
            Target
          </span>
          <span className="font-semibold text-gray-900">{Number(target).toLocaleString("en-IN")} ha</span>
        </div>
      </div>
    </div>
  );
}

export function AcquisitionProgressChart({ data }: AcquisitionProgressChartProps) {
  const chartData = useMemo(() => {
    return (data || []).map((item: any) => {
      const target = Number(item.target_ha ?? item.target ?? 0);
      const acquired = Number(item.acquired_ha ?? item.acquired ?? 0);
      return {
        quarter: item.quarter,
        target,
        acquired,
      };
    });
  }, [data]);

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData} margin={{ top: 12, right: 12, left: -14, bottom: 0 }}>
          <defs>
            <linearGradient id="gradAcquired" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#D47A22" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#D47A22" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="gradTarget" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#439288" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#439288" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="4 4" stroke="#F1F5F9" vertical={false} />
          <XAxis
            dataKey="quarter"
            tick={{ fontSize: 11, fill: "#64748B", fontWeight: 500 }}
            axisLine={{ stroke: "#E2E8F0" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#64748B" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : `${v}`)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: "11px", paddingTop: "12px", color: "#475569" }}
            formatter={(value: string) =>
              value === "acquired" ? "Acquired Land (ha)" : "Target Land (ha)"
            }
          />
          <Area
            type="monotone"
            dataKey="target"
            stroke="#439288"
            strokeWidth={2}
            strokeDasharray="4 4"
            fill="url(#gradTarget)"
            activeDot={{ r: 5, stroke: "#439288", strokeWidth: 2, fill: "#fff" }}
          />
          <Area
            type="monotone"
            dataKey="acquired"
            stroke="#D47A22"
            strokeWidth={2.5}
            fill="url(#gradAcquired)"
            activeDot={{ r: 6, stroke: "#D47A22", strokeWidth: 2.5, fill: "#fff" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
