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
      <div className="min-h-[22px] flex items-center">
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
              <span className="text-[10px] font-medium text-gray-500 truncate">{trend.label}</span>
            )}
          </div>
        )}
      </div>

      {/* Clean Full-Width Mini Bar Trend (Zero text overlap, perfectly spaced across card) */}
      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <div className="flex items-end gap-2 h-6 w-full">
            {(() => {
              const min = Math.min(...sparklineData);
              const max = Math.max(...sparklineData);
              const range = max - min || 1;
              return sparklineData.map((val, i) => {
                const heightPct = Math.max(18, Math.round(((val - min) / range) * 82 + 18));
                const isLatest = i === sparklineData.length - 1;
                return (
                  <div
                    key={i}
                    className="flex-1 transition-all"
                    style={{
                      height: `${heightPct}%`,
                      backgroundColor: sparklineColor,
                      opacity: isLatest ? 1.0 : 0.35 + (i / sparklineData.length) * 0.45,
                    }}
                    title={`Period ${i + 1}: ${val}`}
                  />
                );
              });
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
