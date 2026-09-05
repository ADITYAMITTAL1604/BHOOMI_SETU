import { useMemo } from "react";
import {
  BarChart,
  Bar,
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

  const target = payload.find((p) => p.dataKey === "target")?.value || 0;
  const acquired = payload.find((p) => p.dataKey === "acquired")?.value || 0;
  const pct = target > 0 ? Math.round((acquired / target) * 100) : 0;

  return (
    <div className="bg-white border-2 border-gray-700 shadow-md p-3 min-w-[200px] text-xs">
      <div className="flex items-center justify-between border-b border-gray-300 pb-1.5 mb-2">
        <span className="font-bold text-gray-900 uppercase tracking-wider">{label}</span>
        <span className="bg-gray-100 border border-gray-300 text-gray-800 font-bold px-1.5 py-0.5 text-[10px]">
          {pct}% MET
        </span>
      </div>
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-gray-700 font-semibold">
            <span className="w-2.5 h-2.5 bg-[#2B6D97] inline-block" />
            Target Area:
          </span>
          <span className="font-bold font-mono text-gray-900">{Number(target).toLocaleString("en-IN")} ha</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-gray-700 font-semibold">
            <span className="w-2.5 h-2.5 bg-[#D47A22] inline-block" />
            Acquired Area:
          </span>
          <span className="font-bold font-mono text-[#D47A22]">{Number(acquired).toLocaleString("en-IN")} ha</span>
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
      <ResponsiveContainer width="100%" height={215} minWidth={280}>
        <BarChart data={chartData} margin={{ top: 12, right: 10, left: 0, bottom: 0 }} barGap={4} barCategoryGap="25%">
          <CartesianGrid stroke="#E2E8F0" vertical={false} strokeDasharray="0" />
          <XAxis
            dataKey="quarter"
            tick={{ fontSize: 11, fill: "#334155", fontWeight: 600 }}
            axisLine={{ stroke: "#94A3B8" }}
            tickLine={true}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#475569", fontWeight: 500 }}
            axisLine={{ stroke: "#94A3B8" }}
            tickLine={true}
            tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : `${v}`)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="square"
            iconSize={10}
            wrapperStyle={{ fontSize: "11px", paddingTop: "8px", fontWeight: 600, color: "#1E293B" }}
            formatter={(value: string) =>
              value === "target" ? "Planned Target (ha)" : "Statutory Acquired (ha)"
            }
          />
          <Bar
            dataKey="target"
            fill="#2B6D97"
            radius={[0, 0, 0, 0]}
            name="target"
          />
          <Bar
            dataKey="acquired"
            fill="#D47A22"
            radius={[0, 0, 0, 0]}
            name="acquired"
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Government tabular mini-strip */}
      <div className="mt-3 border border-gray-200 grid grid-cols-4 bg-gray-50/70 text-center divide-x divide-gray-200 text-[11px]">
        {chartData.map((d) => {
          const pct = d.target > 0 ? Math.round((d.acquired / d.target) * 100) : 0;
          return (
            <div key={d.quarter} className="p-1.5">
              <span className="block font-bold text-gray-700">{d.quarter}</span>
              <span className="block font-mono text-[10px] text-gray-500">{d.acquired}/{d.target} ha</span>
              <span className="font-bold text-[10px] text-[#D47A22]">{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
