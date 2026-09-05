import { useState } from "react";
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
  Layers,
  Clock,
  BookOpen,
  ChevronDown,
  ChevronUp,
  HelpCircle,
} from "lucide-react";
import { getProject, getProjectSummary, getRecentActivities } from "@/api/projects";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { cn, formatCurrency } from "@/lib/utils";
import type { AcquisitionStage } from "@/types/api";

// Statutory terms & abbreviations glossary
const STATUTORY_GLOSSARY = [
  {
    acronym: "SLA",
    term: "Service Level Agreement (Statutory Timeline)",
    desc: "Mandated legal completion limits for statutory stages under RFCTLARR 2013 (e.g. 60 days for hearings, 12 months for awards).",
  },
  {
    acronym: "R&R",
    term: "Rehabilitation & Resettlement",
    desc: "Mandatory social safeguard entitlements, alternate housing, and resettlement grants under Schedules II & III.",
  },
  {
    acronym: "PAF / PAP",
    term: "Project Affected Families / Persons",
    desc: "Families or individuals whose agricultural land, dwelling, or primary livelihood is acquired for the corridor.",
  },
  {
    acronym: "DBT",
    term: "Direct Benefit Transfer",
    desc: "Electronic compensation funds disbursed directly from state treasury escrow into verified land titleholder bank accounts.",
  },
  {
    acronym: "CALA",
    term: "Competent Authority for Land Acquisition",
    desc: "The designated Sub-Divisional Magistrate (SDM) or ADM authorized to conduct hearings, gazette notices, and awards.",
  },
  {
    acronym: "SLAO",
    term: "Special Land Acquisition Officer",
    desc: "Senior state revenue officer leading ground cadastral valuation, spot joint measurement surveys, and claims inquiries.",
  },
  {
    acronym: "3A & 3D",
    term: "Gazette Statutory Notifications",
    desc: "Section 3A publishes official state intent to acquire land; Section 3D is the final gazette declaration vesting land title.",
  },
  {
    acronym: "JMS / DGPS",
    term: "Joint Measurement Survey (DGPS)",
    desc: "Precision field demarcation using Differential GPS to fix physical Khasra parcel boundaries on revenue maps.",
  },
  {
    acronym: "RFCTLARR",
    term: "RFCTLARR Act, 2013",
    desc: "The Right to Fair Compensation and Transparency in Land Acquisition, Rehabilitation and Resettlement Act, 2013.",
  },
  {
    acronym: "HA",
    term: "Hectares (Area Unit)",
    desc: "Metric land area measurement. 1 Hectare = 10,000 square meters ≈ 2.471 Acres ≈ 3.95 Pucca Bigha (UP).",
  },
];

// Lifecycle stages for the statutory RFCTLARR stepper
const LIFECYCLE_STAGES: { key: AcquisitionStage; label: string; short?: string }[] = [
  { key: "PROPOSAL", label: "Proposal", short: "Proposal" },
  { key: "IDENTIFICATION", label: "Sec 3A", short: "3A" },
  { key: "SURVEY", label: "Joint Survey", short: "Survey" },
  { key: "VERIFICATION", label: "Sec 3D", short: "3D" },
  { key: "NOTIFICATION", label: "Notification", short: "Notice" },
  { key: "OBJECTION", label: "Sec 15 Hearing", short: "Hearing" },
  { key: "AWARD", label: "Sec 3G Award", short: "Award" },
  { key: "COMPENSATION", label: "Compensation", short: "Payment" },
  { key: "REHABILITATION_RESETTLEMENT", label: "R&R Package", short: "R&R" },
  { key: "POSSESSION", label: "Possession", short: "Possession" },
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

  const [showGlossary, setShowGlossary] = useState(true);

  if (projectLoading) {
    return (
      <div className="animate-fade-in space-y-6">
        <div className="h-8 w-64 bg-gray-200 animate-pulse rounded-none" />
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
      <div className="text-center py-20 bg-white border border-gray-300 rounded-none p-8">
        <p className="text-gray-600 font-semibold text-base">Project record not found</p>
        <Link to="/projects" className="text-[#D47A22] font-semibold text-sm mt-3 inline-block hover:underline">
          ← Back to Project Inventory
        </Link>
      </div>
    );
  }

  // Derive real live metrics with exact fallbacks
  const totalParcels = summary?.total_parcels ?? project.total_parcels ?? (project as any).parcels_count ?? 0;
  const acquiredParcels = summary?.acquired_parcels ?? project.acquired_parcels ?? (project as any).parcels_completed ?? 0;
  const progressPct =
    typeof project.progress_pct === "number" && project.progress_pct > 0
      ? project.progress_pct
      : summary?.acquisition_progress_pct ?? (totalParcels > 0 ? Number(((acquiredParcels / totalParcels) * 100).toFixed(1)) : 0);

  // Compute active lifecycle stage index based on progress and parcel stage distribution
  let currentStageIndex = 0;
  if (progressPct >= 80) {
    currentStageIndex = 9; // Possession
  } else if (progressPct >= 65) {
    currentStageIndex = 8; // R&R
  } else if (progressPct >= 45) {
    currentStageIndex = 7; // Compensation
  } else if (progressPct >= 35) {
    currentStageIndex = 6; // Award
  } else if (progressPct >= 25) {
    currentStageIndex = 5; // Hearing / Objection
  } else if (progressPct >= 15) {
    currentStageIndex = 4; // Notification
  } else if (progressPct >= 10) {
    currentStageIndex = 3; // 3D Verification
  } else if (progressPct >= 5) {
    currentStageIndex = 2; // Survey
  } else {
    currentStageIndex = 1; // 3A
  }

  const statesStr = Array.isArray(project.states) ? project.states.join(", ") : String(project.states || "Uttar Pradesh");
  const districtsStr = Array.isArray(project.districts) ? project.districts.join(", ") : String(project.districts || "");
  const landRequired = project.land_required_ha ?? 0;
  const landAcquired = project.land_acquired_ha ?? 0;

  // Parcel stage breakdown counts from real summary
  const sDist = summary?.stage_distribution || ({} as Record<string, number>);
  const surveyCount = (sDist.SURVEY || 0) + (sDist.VERIFICATION || 0);
  const noticeCount = (sDist.NOTIFICATION || 0) + (sDist.IDENTIFICATION || 0);
  const objectionCount = sDist.OBJECTION || 0;
  const awardCompCount = (sDist.AWARD || 0) + (sDist.COMPENSATION || 0);
  const possessionCount = (sDist.POSSESSION || 0) + (sDist.REHABILITATION_RESETTLEMENT || 0) + (sDist.CLOSURE || 0);

  const parcelDistributionItems = [
    { label: "Cadastral Survey & Demarcation", count: surveyCount, color: "bg-blue-600" },
    { label: "Gazette Notification (3A / 3D)", count: noticeCount, color: "bg-indigo-500" },
    { label: "Section 15 Hearings & Objections", count: objectionCount, color: "bg-amber-600" },
    { label: "Award Determination & Compensation", count: awardCompCount, color: "bg-[#D47A22]" },
    { label: "Possession & Handover (Acquired)", count: Math.max(acquiredParcels, possessionCount), color: "bg-emerald-600" },
  ];

  return (
    <div className="animate-fade-in space-y-6">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
        <Link to="/dashboard" className="hover:text-[#D47A22] transition-colors">
          BhoomiSetu
        </Link>
        <ChevronRight className="w-3 h-3 text-gray-400" />
        <Link to="/projects" className="hover:text-[#D47A22] transition-colors">
          Project Inventory
        </Link>
        <ChevronRight className="w-3 h-3 text-gray-400" />
        <span className="text-gray-900 font-bold">{project.name}</span>
      </div>

      {/* ── Project Master Header ────────────────────── */}
      <Card className="p-6 rounded-none border border-gray-300 bg-white shadow-none">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2.5 mb-2">
              <Badge variant="status" level={project.status} className="rounded-none border px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider">
                {project.status}
              </Badge>
              <span className="text-xs font-mono text-gray-500 bg-gray-100 border border-gray-300 px-2 py-0.5">
                ID: {project.project_id}
              </span>
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide bg-amber-50 text-[#D47A22] border border-amber-200 px-2 py-0.5">
                {project.type}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-3 tracking-tight">
              {project.name}
            </h1>
            <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-xs text-gray-700 font-medium">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-[#D47A22]" />
                <span className="font-bold text-gray-900">{statesStr}</span> {districtsStr ? `(${districtsStr})` : ""}
              </span>
              <span className="flex items-center gap-1.5">
                <Train className="w-4 h-4 text-[#D47A22]" />
                <span className="font-bold text-gray-900 font-mono">{landAcquired.toFixed(1)} / {landRequired.toFixed(1)} HA</span> Corridor
              </span>
              <span className="flex items-center gap-1.5">
                <Users className="w-4 h-4 text-[#D47A22]" />
                <span className="font-bold text-gray-900 font-mono">{totalParcels}</span> Recorded Parcels ({acquiredParcels} Acquired)
              </span>
            </div>
          </div>

          {/* Donut Progress Meter */}
          <div className="flex-shrink-0 flex items-center justify-center bg-amber-50/40 border border-amber-200/80 p-3">
            <ProgressDonut pct={progressPct} acquiredHa={landAcquired} requiredHa={landRequired} size={110} />
          </div>
        </div>
      </Card>

      {/* ── Key Statutory Metrics (3 Stat Cards) ────────────────────────── */}
      {summaryLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
      ) : summary ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Compensation Paid */}
          <Card className="p-5 rounded-none border border-gray-300 bg-white shadow-none">
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500">
                Compensation Disbursed
              </p>
              <IndianRupee className="w-4 h-4 text-[#D47A22]" />
            </div>
            <p className="text-2xl font-bold text-gray-900 font-mono">
              {formatCurrency(summary.compensation?.paid ?? 0)}
            </p>
            <div className="mt-2 text-xs font-medium text-gray-600">
              <span className="text-emerald-700 font-bold font-mono">
                {summary.compensation?.approved ? ((summary.compensation.paid / summary.compensation.approved) * 100).toFixed(1) : 0}%
              </span>{" "}
              disbursed of <span className="font-bold font-mono">{formatCurrency(summary.compensation?.approved ?? 0)}</span> approved award
            </div>
          </Card>

          {/* R&R Resettlement Progress */}
          <Card className="p-5 rounded-none border border-gray-300 bg-white shadow-none">
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500">
                R&R Resettlement Progress
              </p>
              <Home className="w-4 h-4 text-[#D47A22]" />
            </div>
            <p className="text-2xl font-bold text-gray-900 font-mono">
              {summary.rr?.total_families ? Math.round(((summary.rr.rehabilitated ?? 0) / summary.rr.total_families) * 100) : 0}%
            </p>
            <div className="h-2.5 bg-gray-100 border border-gray-300 rounded-none overflow-hidden mt-2">
              <div
                className="h-full bg-[#D47A22] rounded-none transition-all duration-500"
                style={{
                  width: `${summary.rr?.total_families ? Math.min(100, Math.round(((summary.rr.rehabilitated ?? 0) / summary.rr.total_families) * 100)) : 0}%`,
                }}
              />
            </div>
            <p className="text-xs text-gray-600 font-medium mt-2">
              <span className="font-bold text-gray-900 font-mono">{summary.rr?.rehabilitated ?? 0}</span> of{" "}
              <span className="font-bold text-gray-900 font-mono">{summary.rr?.total_families ?? 0}</span> PAFs package allocated
            </p>
          </Card>

          {/* SLA Statutory Compliance */}
          <Card className="p-5 rounded-none border border-gray-300 bg-white shadow-none">
            <div className="flex items-center justify-between mb-1.5">
              <p
                className="text-[11px] font-bold uppercase tracking-wider text-gray-500 cursor-help flex items-center gap-1"
                title="Service Level Agreement compliance: Percentage of parcels proceeding within legal statutory limits under RFCTLARR 2013"
              >
                SLA Statutory Compliance
                <HelpCircle className="w-3 h-3 text-gray-400" />
              </p>
              <BarChart3 className="w-4 h-4 text-[#D47A22]" />
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-bold text-gray-900 font-mono">
                {typeof summary.sla_compliance_pct === "number"
                  ? Math.round(summary.sla_compliance_pct)
                  : totalParcels > 0
                  ? Math.max(0, 100 - Math.round(((summary.sla_breaches ?? 0) / totalParcels) * 100))
                  : 100}%
              </p>
              <span className="text-xs font-semibold text-gray-500 font-mono">
                ({summary.sla_compliant_parcels ?? Math.max(0, totalParcels - (summary.sla_breaches ?? 0))} of {totalParcels} on track)
              </span>
            </div>
            <div className="h-2.5 bg-gray-100 border border-gray-300 rounded-none overflow-hidden mt-2">
              <div
                className={cn(
                  "h-full rounded-none transition-all duration-500",
                  (summary.sla_compliance_pct ?? 50) >= 70
                    ? "bg-emerald-600"
                    : (summary.sla_compliance_pct ?? 50) >= 50
                    ? "bg-[#D47A22]"
                    : "bg-amber-600"
                )}
                style={{
                  width: `${Math.min(
                    100,
                    typeof summary.sla_compliance_pct === "number"
                      ? summary.sla_compliance_pct
                      : totalParcels > 0
                      ? Math.max(0, 100 - Math.round(((summary.sla_breaches ?? 0) / totalParcels) * 100))
                      : 100
                  )}%`,
                }}
              />
            </div>
            <div className="mt-2">
              {(summary.sla_breaches ?? 0) > 0 ? (
                <p className="text-xs text-amber-800 font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span className="font-bold font-mono">{summary.sla_breaches}</span> parcels flagged for statutory delay review
                </p>
              ) : (
                <p className="text-xs text-emerald-800 font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  All statutory stages operating within legal SLA limits
                </p>
              )}
            </div>
          </Card>
        </div>
      ) : null}

      {/* ── Statutory Acronyms & Abbreviations Reference Guide ─────────────── */}
      <Card className="rounded-none border border-gray-300 bg-white shadow-none overflow-hidden">
        <div
          className="flex items-center justify-between px-4 py-2.5 bg-gray-50 border-b border-gray-200 cursor-pointer select-none hover:bg-gray-100/80 transition-colors"
          onClick={() => setShowGlossary(!showGlossary)}
        >
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-[#D47A22]" />
            <span className="text-xs font-bold text-gray-800 uppercase tracking-wide">
              Statutory Terms & Acronyms Reference Guide
            </span>
            <span className="hidden sm:inline text-[11px] text-gray-500">
              (SLA, R&R, PAF, DBT, CALA, SLAO, 3A/3D, JMS, DGPS, HA)
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs font-semibold text-[#D47A22]">
            <span>{showGlossary ? "Hide Guide" : "Show Guide"}</span>
            {showGlossary ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </div>
        </div>

        {showGlossary && (
          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 bg-white">
            {STATUTORY_GLOSSARY.map((item) => (
              <div
                key={item.acronym}
                className="p-2.5 rounded-none border border-gray-200 bg-gray-50/50 hover:border-[#D47A22]/50 hover:bg-amber-50/30 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="px-1.5 py-0.5 font-mono text-[11px] font-bold bg-amber-100/70 text-[#A3540C] border border-amber-300/80 rounded-none">
                      {item.acronym}
                    </span>
                  </div>
                  <p className="text-xs font-bold text-gray-900 leading-tight mb-1">
                    {item.term}
                  </p>
                  <p className="text-[11px] text-gray-600 leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* ── Statutory Acquisition Lifecycle Stepper ─────────────── */}
      <Card className="rounded-none border border-gray-300 bg-white shadow-none">
        <CardHeader className="py-3 px-5 border-b border-gray-200 bg-gray-50/60">
          <CardTitle className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#D47A22]" />
            Statutory RFCTLARR Acquisition Lifecycle
          </CardTitle>
        </CardHeader>
        <CardContent className="p-5 overflow-x-auto">
          <div className="flex items-center justify-between min-w-[750px] pb-2">
            {LIFECYCLE_STAGES.map((stage, index) => {
              const isCompleted = index < currentStageIndex;
              const isCurrent = index === currentStageIndex;
              const isPending = index > currentStageIndex;

              return (
                <div key={stage.key} className="flex items-center flex-1 last:flex-none">
                  {/* Step Icon & Label */}
                  <div className="flex flex-col items-center flex-shrink-0">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-none border flex items-center justify-center transition-all",
                        isCompleted && "bg-[#D47A22] border-[#D47A22] text-white",
                        isCurrent && "bg-amber-100/70 border-2 border-[#D47A22] text-[#D47A22] font-black",
                        isPending && "bg-gray-50 border-gray-300 text-gray-400"
                      )}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : isCurrent ? (
                        <Circle className="w-4 h-4 fill-[#D47A22]/20" />
                      ) : (
                        <Lock className="w-3 h-3 text-gray-400" />
                      )}
                    </div>
                    <p
                      className={cn(
                        "text-[11px] font-semibold mt-1.5 text-center leading-tight whitespace-nowrap",
                        isCompleted && "text-gray-800 font-bold",
                        isCurrent && "text-[#D47A22] font-extrabold underline decoration-[#D47A22] decoration-2 underline-offset-4",
                        isPending && "text-gray-400"
                      )}
                    >
                      {stage.short || stage.label}
                    </p>
                  </div>

                  {/* Connecting Line */}
                  {index < LIFECYCLE_STAGES.length - 1 && (
                    <div
                      className={cn(
                        "h-1 flex-1 mx-2",
                        index < currentStageIndex ? "bg-[#D47A22]" : "bg-gray-200"
                      )}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* ── Bottom Row: Real Parcel Distribution + Authentic Recent Activities ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Parcel Distribution Matrix */}
        <Card className="lg:col-span-2 rounded-none border border-gray-300 bg-white shadow-none">
          <CardHeader className="py-3 px-5 border-b border-gray-200 bg-gray-50/60">
            <CardTitle className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#D47A22]" />
              Live Parcel Pipeline Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5">
            {summary ? (
              <div className="space-y-4">
                {parcelDistributionItems.map((item) => {
                  const pct = totalParcels > 0 ? ((item.count / totalParcels) * 100).toFixed(1) : "0.0";
                  return (
                    <div key={item.label} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-gray-700">{item.label}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900 font-mono">{item.count}</span>
                          <span className="text-gray-400 font-mono text-[11px]">({pct}%)</span>
                        </div>
                      </div>
                      <div className="w-full h-2.5 bg-gray-100 border border-gray-300 rounded-none overflow-hidden">
                        <div
                          className={cn("h-full rounded-none transition-all duration-300", item.color)}
                          style={{ width: `${Math.min(100, Math.max(0, Number(pct)))}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-5 bg-gray-200 animate-pulse rounded-none" />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Real-time Incident & Milestone Activities */}
        <Card className="lg:col-span-3 rounded-none border border-gray-300 bg-white shadow-none">
          <CardHeader className="py-3 px-5 border-b border-gray-200 bg-gray-50/60 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#D47A22]" />
              Statutory Incident & Milestone Audit Trail
            </CardTitle>
            <span className="text-[11px] font-mono font-bold text-gray-500">
              {Array.isArray(activities) ? activities.length : 0} Events Logged
            </span>
          </CardHeader>
          <CardContent className="p-5">
            {Array.isArray(activities) && activities.length > 0 ? (
              <div className="space-y-4 max-h-[380px] overflow-y-auto pr-1">
                {activities.map((activity: any) => (
                  <div
                    key={activity.id}
                    className="p-3 border border-gray-200 bg-gray-50/50 hover:bg-amber-50/30 transition-colors rounded-none flex items-start gap-3"
                  >
                    {/* Role Avatar Badge */}
                    <div
                      className={cn(
                        "w-8 h-8 rounded-none border flex items-center justify-center flex-shrink-0 font-bold text-xs text-white",
                        activity.icon_color || "bg-[#D47A22] border-[#D47A22]"
                      )}
                    >
                      {activity.user?.charAt(0) || "G"}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <span className="text-xs font-bold text-gray-900 uppercase tracking-wide">
                          {activity.action}
                        </span>
                        <span className="text-[11px] font-mono text-gray-500 whitespace-nowrap">
                          {activity.time_ago}
                        </span>
                      </div>
                      <p className="text-xs text-gray-700 mt-1 leading-relaxed">
                        {activity.entity}
                      </p>
                      <p className="text-[10px] font-semibold text-[#D47A22] mt-1">
                        Recorded by: {activity.user}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10 text-gray-500 text-xs">
                No recent timeline activities recorded for this project corridor.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ── Donut Progress Component with Strict Government Styling ───────────────────────────
function ProgressDonut({
  pct,
  acquiredHa,
  requiredHa,
  size = 110,
}: {
  pct: number;
  acquiredHa?: number;
  requiredHa?: number;
  size?: number;
}) {
  const safePct = typeof pct === "number" && !isNaN(pct) ? Math.max(0, Math.min(100, pct)) : 0;
  const radius = (size - 14) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (safePct / 100) * circumference;

  return (
    <div
      className="relative flex flex-col items-center justify-center cursor-default"
      style={{ width: size, height: size }}
      title={acquiredHa && requiredHa ? `${acquiredHa.toFixed(1)} / ${requiredHa.toFixed(1)} HA Acquired` : undefined}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E5E7EB"
          strokeWidth="10"
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#D47A22"
          strokeWidth="10"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-black text-gray-900 font-mono tracking-tight">
          {safePct.toFixed(1)}%
        </span>
        <span className="text-[9px] font-bold text-[#D47A22] uppercase tracking-wider">
          Acquired
        </span>
      </div>
    </div>
  );
}

export default ProjectDetailPage;
