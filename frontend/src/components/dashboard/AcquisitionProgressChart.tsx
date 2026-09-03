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

export function AcquisitionProgressChart({ data }: AcquisitionProgressChartProps) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="gradAcquired" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#2B6D97" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#2B6D97" stopOpacity={0.02} />
          </linearGradient>
          <linearGradient id="gradPending" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#D47A22" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#D47A22" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
        <XAxis
          dataKey="quarter"
          tick={{ fontSize: 11, fill: "#9CA3AF" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#9CA3AF" }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) =>
            v >= 1000 ? `${(v / 1000).toFixed(0)}K` : String(v)
          }
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "white",
            borderRadius: "10px",
            border: "1px solid #E5E7EB",
            boxShadow: "0 4px 6px -1px rgba(0,0,0,0.08)",
            fontSize: "12px",
          }}
          formatter={(value: number, name: string) => [
            value.toLocaleString("en-IN"),
            name === "acquired" ? "Acquired" : name === "pending" ? "Pending" : "Target",
          ]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
          formatter={(value: string) =>
            value === "acquired" ? "Acquired" : value === "pending" ? "Pending" : "Target"
          }
        />
        <Area
          type="monotone"
          dataKey="acquired"
          stroke="#2B6D97"
          strokeWidth={2}
          fill="url(#gradAcquired)"
        />
        <Area
          type="monotone"
          dataKey="pending"
          stroke="#D47A22"
          strokeWidth={2}
          fill="url(#gradPending)"
          strokeDasharray="4 4"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
