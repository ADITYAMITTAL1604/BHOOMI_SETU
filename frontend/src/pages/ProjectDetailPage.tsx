import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  MapPin,
  Train,
  Users,
  ChevronRight,
  IndianRupee,
  Home,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Lock,
} from "lucide-react";
import { getProject, getProjectSummary, getRecentActivities } from "@/api/projects";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { cn, formatCurrency } from "@/lib/utils";
import type { AcquisitionStage } from "@/types/api";

// Lifecycle stages for the stepper
const LIFECYCLE_STAGES: { key: AcquisitionStage; label: string; short?: string }[] = [
  { key: "PROPOSAL", label: "Proposal" },
  { key: "IDENTIFICATION", label: "Sec 3A", short: "3A" },
  { key: "SURVEY", label: "Survey" },
  { key: "VERIFICATION", label: "Sec 3D", short: "3D" },
  { key: "NOTIFICATION", label: "Notification" },
  { key: "OBJECTION", label: "Objection" },
  { key: "AWARD", label: "Sec 3G (Award)", short: "Award" },
  { key: "COMPENSATION", label: "Compensation" },
  { key: "REHABILITATION_RESETTLEMENT", label: "R&R" },
  { key: "POSSESSION", label: "Possession" },
];

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["project-summary", projectId],
    queryFn: () => getProjectSummary(projectId!),
    enabled: !!projectId,
  });

  const { data: activities } = useQuery({
    queryKey: ["project-activities", projectId],
    queryFn: () => getRecentActivities(projectId!),
    enabled: !!projectId,
  });

  if (projectLoading) {
    return (
      <div className="animate-fade-in space-y-6">
        <div className="h-8 w-64 animate-shimmer rounded" />
        <div className="grid grid-cols-3 gap-4">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500">Project not found</p>
        <Link to="/projects" className="text-brand-teal-blue text-sm mt-2 inline-block">
          ← Back to Projects
        </Link>
      </div>
    );
  }

  // Safely derive metrics with fallbacks
  const totalParcels = project.total_parcels ?? (project as any).parcels_count ?? 0;
  const acquiredParcels = project.acquired_parcels ?? (project as any).parcels_completed ?? 0;
  const progressPct = typeof project.progress_pct === "number"
    ? project.progress_pct
    : (totalParcels > 0 ? Math.round((acquiredParcels / totalParcels) * 100) : 0);

  // Determine current lifecycle stage index
  const currentStageIndex = Math.min(
    Math.floor((progressPct || 0) / (100 / LIFECYCLE_STAGES.length)),
    LIFECYCLE_STAGES.length - 1
  );

  const statesStr = Array.isArray(project.states) ? project.states.join(", ") : String(project.states || "Uttar Pradesh");
  const districtsStr = Array.isArray(project.districts) ? project.districts.join(", ") : String(project.districts || "");
  const landRequired = project.land_required_ha ?? 0;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-xs text-gray-400">
        <Link to="/dashboard" className="hover:text-brand-teal-blue transition-colors">
          BhoomiSetu
        </Link>
        <ChevronRight className="w-3 h-3" />
        <Link to="/projects" className="hover:text-brand-teal-blue transition-colors">
          Projects
        </Link>
        <ChevronRight className="w-3 h-3" />
        <span className="text-gray-600 font-medium">Project Details</span>
      </div>

      {/* ── Project Header ────────────────────── */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="status" level={project.status}>
                {project.status}
              </Badge>
              <span className="text-[11px] font-mono text-gray-400">
                ID: {project.project_id}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-3">
              {project.name}
            </h1>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4" />
                {statesStr} {districtsStr ? `/ ${districtsStr}` : ""}
              </span>
              <span className="flex items-center gap-1.5">
                <Train className="w-4 h-4" />
                {landRequired.toLocaleString()} ha Corridor
              </span>
              <span className="flex items-center gap-1.5">
                <Users className="w-4 h-4" />
                {totalParcels.toLocaleString()} PAPs
              </span>
            </div>
          </div>

          {/* Donut Progress */}
          <div className="flex-shrink-0 ml-6">
            <ProgressDonut pct={progressPct} size={100} />
          </div>
        </div>
      </Card>

      {/* ── Stat Cards ────────────────────────── */}
      {summaryLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
      ) : summary ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-5">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                Compensation Paid
              </p>
              <IndianRupee className="w-4 h-4 text-gray-300" />
            </div>
            <p className="text-2xl font-bold text-foreground">
              {formatCurrency(summary.compensation?.paid ?? 0)}
            </p>
            <p className="text-xs text-emerald-600 font-medium mt-1">
              ↗ +12% this month
            </p>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                R&R Progress
              </p>
              <Home className="w-4 h-4 text-gray-300" />
            </div>
            <p className="text-2xl font-bold text-foreground">
              {summary.rr?.total_families ? Math.round(((summary.rr.rehabilitated ?? 0) / summary.rr.total_families) * 100) : 0}%
            </p>
            <div className="h-2 bg-gray-100 rounded-full mt-2">
              <div
                className="h-full bg-brand-teal-blue rounded-full"
                style={{
                  width: `${summary.rr?.total_families ? Math.min(100, Math.round(((summary.rr.rehabilitated ?? 0) / summary.rr.total_families) * 100)) : 0}%`,
                }}
              />
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                SLA Compliance
              </p>
              <BarChart3 className="w-4 h-4 text-gray-300" />
            </div>
            <p className="text-2xl font-bold text-foreground">
              {totalParcels > 0 ? Math.max(0, 100 - Math.round(((summary.sla_breaches ?? 0) / totalParcels) * 100)) : 100}%
            </p>
            {(summary.sla_breaches ?? 0) > 0 && (
              <p className="text-xs text-brand-copper font-medium mt-1 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                {summary.sla_breaches} cases delayed
              </p>
            )}
          </Card>
        </div>
      ) : null}

      {/* ── Acquisition Lifecycle ─────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Acquisition Lifecycle</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between overflow-x-auto pb-2">
            {LIFECYCLE_STAGES.map((stage, index) => {
              const isCompleted = index < currentStageIndex;
              const isCurrent = index === currentStageIndex;
              const isPending = index > currentStageIndex;

              return (
                <div key={stage.key} className="flex items-center">
                  {/* Step */}
                  <div className="flex flex-col items-center min-w-[80px]">
                    <div
                      className={cn(
                        "w-9 h-9 rounded-full flex items-center justify-center transition-all",
                        isCompleted && "bg-brand-teal-blue text-white",
                        isCurrent && "bg-brand-teal-blue/15 text-brand-teal-blue border-2 border-brand-teal-blue",
                        isPending && "bg-gray-100 text-gray-400"
                      )}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5" />
                      ) : isCurrent ? (
                        <Circle className="w-5 h-5" />
                      ) : (
                        <Lock className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <p
                      className={cn(
                        "text-[10px] font-medium mt-1.5 text-center leading-tight",
                        isCompleted && "text-brand-teal-blue",
                        isCurrent && "text-brand-teal-blue font-semibold",
                        isPending && "text-gray-400"
                      )}
                    >
                      {stage.short || stage.label}
                    </p>
                  </div>

                  {/* Connector line */}
                  {index < LIFECYCLE_STAGES.length - 1 && (
                    <div
                      className={cn(
                        "h-0.5 w-8 mx-0.5 flex-shrink-0",
                        index < currentStageIndex
                          ? "bg-brand-teal-blue"
                          : "bg-gray-200"
                      )}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* ── Bottom Row: Parcel Distribution + Activities ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Parcel Distribution */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Parcel Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {summary ? (
              <div className="space-y-3">
                {(() => {
                  const sTotal = summary.total_parcels || totalParcels || 1;
                  return [
                    { label: "Identified", count: summary.total_parcels || totalParcels, color: "bg-brand-teal-blue" },
                    { label: "Notified (3A)", count: Math.round(sTotal * 0.85), color: "bg-red-400" },
                    { label: "Declaration (3D)", count: Math.round(sTotal * 0.6), color: "bg-brand-sage-green" },
                    { label: "Awarded (3G)", count: summary.acquired_parcels ?? acquiredParcels, color: "bg-brand-copper" },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-3">
                      <p className="text-xs text-gray-500 w-28 flex-shrink-0">
                        {item.label}
                      </p>
                      <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={cn("h-full rounded-full", item.color)}
                          style={{
                            width: `${Math.min(100, Math.round((item.count / sTotal) * 100))}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-gray-700 w-12 text-right">
                        {item.count.toLocaleString()}
                      </span>
                    </div>
                  ));
                })()}
              </div>
            ) : (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-4 animate-shimmer rounded" />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activities */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Recent Activities</CardTitle>
          </CardHeader>
          <CardContent>
            {Array.isArray(activities) && activities.length > 0 ? (
              <div className="space-y-4">
                {activities.map((activity: any) => (
                  <div key={activity.id} className="flex gap-3">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                        activity.icon_color
                      )}
                    >
                      <span className="text-white text-[10px] font-bold">
                        {activity.user.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-700">
                        <strong className="font-semibold">{activity.user}</strong>{" "}
                        {activity.action}{" "}
                        {activity.entity && (
                          <strong className="font-semibold text-brand-teal-blue">
                            {activity.entity}
                          </strong>
                        )}
                      </p>
                      <p className="text-[11px] text-gray-400 mt-0.5">
                        {activity.time_ago}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-12 animate-shimmer rounded" />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ── Donut Progress Component ───────────────────────────
function ProgressDonut({ pct, size = 100 }: { pct: number; size?: number }) {
  const safePct = typeof pct === "number" && !isNaN(pct) ? Math.max(0, Math.min(100, Math.round(pct))) : 0;
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (safePct / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E5E7EB"
          strokeWidth="8"
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#D47A22"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-[#D47A22]">{safePct}%</span>
        <span className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider">
          Acquired
        </span>
      </div>
    </div>
  );
}

export default ProjectDetailPage;
