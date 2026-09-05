import { cn } from "@/lib/utils";

interface StageBreakdownChartProps {
  data: Array<{
    stage: string;
    percentage: number;
    count: number;
  }>;
  className?: string;
}

const GOV_STAGE_COLORS: Record<string, string> = {
  "Survey & Mapping": "#2B6D97",
  "Verification & Claims": "#0F766E",
  "Sec 11 Notification": "#D47A22",
  "Sec 15 Objections": "#B45309",
  "Award & Compensation": "#15803D",
  "R&R Resettlement": "#4338CA",
  "Possession Transfer": "#7C2D12",
  "Project Closure": "#334155",
};

const STAGE_CODES: Record<string, string> = {
  "Survey & Mapping": "SURV",
  "Verification & Claims": "VERIF",
  "Sec 11 Notification": "SEC-11",
  "Sec 15 Objections": "SEC-15",
  "Award & Compensation": "AWARD",
  "R&R Resettlement": "R&R",
  "Possession Transfer": "POSS",
  "Project Closure": "CLOSE",
};

export function StageBreakdownChart({ data, className }: StageBreakdownChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="py-8 text-center text-gray-400 text-xs font-medium">
        No active parcels in pipeline stages.
      </div>
    );
  }

  const totalParcels = data.reduce((acc, item) => acc + item.count, 0);

  return (
    <div className={cn("space-y-3", className)}>
      <div className="divide-y divide-gray-100 border border-gray-200 bg-white">
        {data.map((item) => {
          const barColor = GOV_STAGE_COLORS[item.stage] || "#475569";
          const code = STAGE_CODES[item.stage] || "MIS";

          return (
            <div
              key={item.stage}
              className="p-2.5 hover:bg-amber-50/30 transition-colors"
            >
              <div className="flex items-center justify-between mb-1.5 text-xs">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold bg-gray-100 text-gray-700 border border-gray-300">
                    {code}
                  </span>
                  <span className="font-bold text-gray-800 truncate">
                    {item.stage}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-right flex-shrink-0">
                  <span className="font-mono text-[11px] text-gray-600">
                    {item.count.toLocaleString("en-IN")} parcels
                  </span>
                  <span className="font-mono font-bold text-gray-900 w-9 text-right">
                    {item.percentage}%
                  </span>
                </div>
              </div>

              {/* Sharp Government Progress Bar */}
              <div className="h-2 bg-gray-100 overflow-hidden border border-gray-300">
                <div
                  className="h-full transition-all duration-500 ease-out"
                  style={{
                    width: `${Math.max(2, item.percentage)}%`,
                    backgroundColor: barColor,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Footer */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border border-gray-200 text-xs">
        <span className="font-semibold text-gray-600 uppercase text-[10px] tracking-wider">
          Total Monitored Land Pipeline
        </span>
        <span className="font-mono font-bold text-gray-900">
          {totalParcels.toLocaleString("en-IN")} Parcels
        </span>
      </div>
    </div>
  );
}
