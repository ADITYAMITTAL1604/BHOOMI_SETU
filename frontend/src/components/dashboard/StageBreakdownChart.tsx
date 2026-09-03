import { cn } from "@/lib/utils";

interface StageBreakdownChartProps {
  data: Array<{
    stage: string;
    percentage: number;
    count: number;
  }>;
  className?: string;
}

const STAGE_COLORS = [
  "bg-brand-teal-blue",
  "bg-brand-copper",
  "bg-brand-sea-green",
  "bg-brand-sage-green",
  "bg-blue-400",
];

export function StageBreakdownChart({ data, className }: StageBreakdownChartProps) {
  return (
    <div className={cn("space-y-3.5", className)}>
      {data.map((item, index) => (
        <div key={item.stage} className="group">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors">
              {item.stage}
            </span>
            <span className="text-sm font-bold text-gray-900">
              {item.percentage}%
            </span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-700 ease-out",
                STAGE_COLORS[index % STAGE_COLORS.length]
              )}
              style={{ width: `${item.percentage}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
