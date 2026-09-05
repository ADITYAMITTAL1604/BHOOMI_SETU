import { cn } from "@/lib/utils";
import type { RiskLevel, ProjectStatus, AlertSeverity } from "@/types/api";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "risk" | "status" | "severity";
  level?: RiskLevel | ProjectStatus | AlertSeverity | string;
  className?: string;
}

const RISK_COLORS: Record<string, string> = {
  LOW: "bg-emerald-50 text-emerald-800 border border-emerald-300",
  MEDIUM: "bg-amber-50 text-amber-800 border border-amber-300",
  Med: "bg-amber-50 text-amber-800 border border-amber-300",
  HIGH: "bg-red-50 text-red-800 border border-red-300",
  CRITICAL: "bg-red-100 text-red-900 border border-red-500 font-extrabold",
};

const STATUS_COLORS: Record<string, string> = {
  PLANNING: "bg-blue-50 text-blue-800 border border-blue-200",
  ACTIVE: "bg-emerald-50 text-emerald-800 border border-emerald-300",
  ON_HOLD: "bg-gray-100 text-gray-700 border border-gray-300",
  COMPLETED: "bg-teal-50 text-teal-800 border border-teal-300",
  CANCELLED: "bg-gray-100 text-gray-500 border border-gray-300",
};

const SEVERITY_COLORS: Record<string, string> = {
  INFO: "bg-blue-50 text-blue-800 border border-blue-200",
  WARNING: "bg-amber-50 text-amber-800 border border-amber-300",
  MEDIUM: "bg-amber-50 text-amber-800 border border-amber-300",
  CRITICAL: "bg-red-50 text-red-800 border border-red-400 font-extrabold",
  HIGH: "bg-red-50 text-red-800 border border-red-300 font-bold",
};

export function Badge({ children, variant = "default", level, className }: BadgeProps) {
  let colorClass = "bg-gray-50 text-gray-700 border border-gray-300";

  if (level) {
    const upperLevel = String(level).toUpperCase();
    if (variant === "risk") {
      colorClass = RISK_COLORS[upperLevel] || colorClass;
    } else if (variant === "status") {
      colorClass = STATUS_COLORS[upperLevel] || colorClass;
    } else if (variant === "severity") {
      colorClass = SEVERITY_COLORS[upperLevel] || colorClass;
    } else {
      // Auto-detect
      colorClass =
        RISK_COLORS[upperLevel] ||
        STATUS_COLORS[upperLevel] ||
        SEVERITY_COLORS[upperLevel] ||
        colorClass;
    }
  }

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-none text-[10px] font-bold uppercase tracking-wider",
        colorClass,
        className
      )}
    >
      {children}
    </span>
  );
}
