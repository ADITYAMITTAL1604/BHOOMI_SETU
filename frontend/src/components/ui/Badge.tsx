import { cn } from "@/lib/utils";
import type { RiskLevel, ProjectStatus, AlertSeverity } from "@/types/api";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "risk" | "status" | "severity";
  level?: RiskLevel | ProjectStatus | AlertSeverity | string;
  className?: string;
}

const RISK_COLORS: Record<string, string> = {
  LOW: "bg-emerald-100 text-emerald-800",
  MEDIUM: "bg-amber-100 text-amber-800",
  Med: "bg-amber-100 text-amber-800",
  HIGH: "bg-orange-100 text-orange-800",
  CRITICAL: "bg-red-100 text-red-800",
};

const STATUS_COLORS: Record<string, string> = {
  PLANNING: "bg-blue-100 text-blue-800",
  ACTIVE: "bg-emerald-100 text-emerald-800",
  ON_HOLD: "bg-gray-100 text-gray-600",
  COMPLETED: "bg-teal-100 text-teal-800",
  CANCELLED: "bg-gray-100 text-gray-500",
};

const SEVERITY_COLORS: Record<string, string> = {
  INFO: "bg-blue-100 text-blue-800",
  WARNING: "bg-amber-100 text-amber-800",
  MEDIUM: "bg-amber-100 text-amber-800",
  CRITICAL: "bg-red-100 text-red-800",
  HIGH: "bg-orange-100 text-orange-800",
};

export function Badge({ children, variant = "default", level, className }: BadgeProps) {
  let colorClass = "bg-gray-100 text-gray-700";

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
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider",
        colorClass,
        className
      )}
    >
      {children}
    </span>
  );
}
