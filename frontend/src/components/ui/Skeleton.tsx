import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-md animate-shimmer",
        className
      )}
    />
  );
}

/** Skeleton preset: full stat card */
export function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-card p-5 space-y-3">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-7 w-20" />
      <Skeleton className="h-8 w-full" />
    </div>
  );
}

/** Skeleton preset: chart area */
export function ChartSkeleton({ height = "h-64" }: { height?: string }) {
  return (
    <div className={cn("bg-white rounded-xl border border-gray-100 shadow-card p-5", height)}>
      <Skeleton className="h-4 w-40 mb-4" />
      <Skeleton className="h-full w-full rounded-lg" />
    </div>
  );
}

/** Skeleton preset: table row */
export function TableRowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}
