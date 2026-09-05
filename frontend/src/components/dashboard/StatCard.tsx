import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    direction: "up" | "down" | "neutral";
    label?: string;
  };
  sparklineData?: number[];
  sparklineColor?: string;
  className?: string;
}

export function StatCard({
  label,
  value,
  icon,
  trend,
  sparklineData,
  sparklineColor = "#D47A22",
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "bg-white border border-gray-300 shadow-sm p-4 flex flex-col gap-1.5 border-t-4 transition-colors",
        className
      )}
      style={{ borderTopColor: sparklineColor }}
    >
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-bold uppercase tracking-wider text-gray-600 truncate">
          {label}
        </p>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>

      <p className="text-2xl font-bold text-gray-900 font-mono tracking-tight">{value}</p>

      {/* Trend indicator */}
      {trend && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-bold uppercase border",
              trend.direction === "up" && "bg-emerald-50 text-emerald-800 border-emerald-300",
              trend.direction === "down" && "bg-red-50 text-red-800 border-red-300",
              trend.direction === "neutral" && "bg-gray-100 text-gray-700 border-gray-300"
            )}
          >
            {trend.direction === "up" && <TrendingUp className="w-3 h-3 text-emerald-600" />}
            {trend.direction === "down" && <TrendingDown className="w-3 h-3 text-red-600" />}
            {trend.direction === "neutral" && <Minus className="w-3 h-3 text-gray-500" />}
            {trend.value}
          </span>
          {trend.label && (
            <span className="text-[10px] font-medium text-gray-500">{trend.label}</span>
          )}
        </div>
      )}

      {/* Government MIS Column Indicator */}
      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <GovernmentMiniBars data={sparklineData} color={sparklineColor} />
        </div>
      )}
    </div>
  );
}

// Government MIS Mini Column Chart (Sharp rectangular bars, no wavy curves)
function GovernmentMiniBars({
  data,
  color,
  height = 24,
}: {
  data: number[];
  color: string;
  height?: number;
}) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const count = data.length;
  const barWidth = 14;
  const gap = 6;
  const totalWidth = count * barWidth + (count - 1) * gap;

  return (
    <div className="flex items-center justify-between">
      <svg
        width={totalWidth}
        height={height}
        viewBox={`0 0 ${totalWidth} ${height}`}
        className="overflow-visible"
      >
        {/* Baseline */}
        <line
          x1={0}
          y1={height - 1}
          x2={totalWidth}
          y2={height - 1}
          stroke="#CBD5E1"
          strokeWidth="1"
        />
        {data.map((val, i) => {
          const barHeight = Math.max(3, Math.round(((val - min) / range) * (height - 4)));
          const x = i * (barWidth + gap);
          const y = height - 1 - barHeight;
          const isLatest = i === count - 1;

          return (
            <rect
              key={i}
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill={color}
              fillOpacity={isLatest ? 1.0 : 0.45 + (i / count) * 0.45}
              stroke={color}
              strokeWidth="0.5"
            />
          );
        })}
      </svg>
      <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider font-semibold">
        MIS Trend
      </span>
    </div>
  );
}
