import { cn } from "@/lib/utils";

interface StageBreakdownChartProps {
  data: Array<{
    stage: string;
    percentage: number;
    count: number;
  }>;
  className?: string;
}

const STAGE_BAR_COLORS = [
  "from-[#D47A22] to-[#ea9039]",
  "from-[#439288] to-[#59b8ab]",
  "from-[#73A557] to-[#8ec76f]",
  "from-[#b45309] to-[#d97706]",
  "from-[#52525b] to-[#71717a]",
  "from-[#d97706] to-[#f59e0b]",
  "from-[#0f766e] to-[#14b8a6]",
];

export function StageBreakdownChart({ data, className }: StageBreakdownChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="py-8 text-center text-gray-400 text-xs font-medium">
        No active parcels in pipeline stages.
      </div>
    );
  }

  return (
    <div className={cn("space-y-3.5", className)}>
      {data.map((item, index) => {
        const colorGradient = STAGE_BAR_COLORS[index % STAGE_BAR_COLORS.length];
        return (
          <div
            key={item.stage}
            className="group rounded-lg p-1.5 -mx-1.5 transition-colors hover:bg-gray-50/80"
          >
            <div className="flex items-center justify-between mb-1.5 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-semibold text-gray-800 truncate group-hover:text-[#D47A22] transition-colors">
                  {item.stage}
                </span>
                <span className="px-1.5 py-0.5 rounded-md bg-gray-100 text-[10px] font-semibold text-gray-600 flex-shrink-0">
                  {item.count.toLocaleString("en-IN")} parcels
                </span>
              </div>
              <span className="font-bold text-gray-900 ml-2 flex-shrink-0">
                {item.percentage}%
              </span>
            </div>
            <div className="h-2 bg-gray-100/90 rounded-full overflow-hidden p-[1px]">
              <div
                className={cn(
                  "h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out group-hover:brightness-110",
                  colorGradient
                )}
                style={{ width: `${Math.max(2, item.percentage)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
