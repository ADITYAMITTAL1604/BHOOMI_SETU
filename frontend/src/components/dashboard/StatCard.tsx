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
  sparklineColor = "#2B6D97",
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-gray-100 shadow-card p-5 flex flex-col gap-1.5 hover:shadow-card-hover transition-shadow",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          {label}
        </p>
        {icon && <div className="text-gray-300">{icon}</div>}
      </div>

      <p className="text-2xl font-bold text-gray-900">{value}</p>

      {/* Trend indicator */}
      {trend && (
        <div className="flex items-center gap-1.5">
          {trend.direction === "up" && (
            <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
          )}
          {trend.direction === "down" && (
            <TrendingDown className="w-3.5 h-3.5 text-red-500" />
          )}
          {trend.direction === "neutral" && (
            <Minus className="w-3.5 h-3.5 text-gray-400" />
          )}
          <span
            className={cn(
              "text-xs font-medium",
              trend.direction === "up" && "text-emerald-600",
              trend.direction === "down" && "text-red-600",
              trend.direction === "neutral" && "text-gray-500"
            )}
          >
            {trend.value}
          </span>
          {trend.label && (
            <span className="text-[10px] text-gray-400">{trend.label}</span>
          )}
        </div>
      )}

      {/* Mini sparkline */}
      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-1">
          <MiniSparkline data={sparklineData} color={sparklineColor} />
        </div>
      )}
    </div>
  );
}

// Simple SVG sparkline
function MiniSparkline({
  data,
  color,
  height = 32,
}: {
  data: number[];
  color: string;
  height?: number;
}) {
  const width = 120;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const padding = 2;

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * (width - padding * 2) + padding;
    const y = height - ((val - min) / range) * (height - padding * 2) - padding;
    return `${x},${y}`;
  });

  const polyline = points.join(" ");

  // Area fill
  const areaPoints = [
    `${padding},${height}`,
    ...points,
    `${width - padding},${height}`,
  ].join(" ");

  return (
    <svg
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="opacity-80"
    >
      <defs>
        <linearGradient id={`grad-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon
        points={areaPoints}
        fill={`url(#grad-${color.replace("#", "")})`}
      />
      <polyline
        points={polyline}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
