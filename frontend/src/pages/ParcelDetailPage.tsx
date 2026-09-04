import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronRight,
  MapPin,
  User,
  Calendar,
  Clock,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Lock,
  Brain,
} from "lucide-react";
import { getParcelById } from "@/api/parcels";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import type { AcquisitionStage, Parcel, StageRecord } from "@/types/api";

// Full 11-stage acquisition pipeline
const STAGES: { key: AcquisitionStage; label: string; sla_days: number }[] = [
  { key: "PROPOSAL", label: "Proposal", sla_days: 30 },
  { key: "IDENTIFICATION", label: "Identification (3A)", sla_days: 45 },
  { key: "SURVEY", label: "Survey & Demarcation", sla_days: 60 },
  { key: "VERIFICATION", label: "Verification (3D)", sla_days: 30 },
  { key: "NOTIFICATION", label: "Notification", sla_days: 15 },
  { key: "OBJECTION", label: "Objection Period", sla_days: 60 },
  { key: "AWARD", label: "Award (3G)", sla_days: 30 },
  { key: "COMPENSATION", label: "Compensation", sla_days: 90 },
  { key: "REHABILITATION_RESETTLEMENT", label: "R&R Plan", sla_days: 120 },
  { key: "POSSESSION", label: "Possession", sla_days: 30 },
  { key: "CLOSURE", label: "Closure", sla_days: 15 },
];

// Mock stage records for a parcel
function mockStageRecords(parcel: Parcel): StageRecord[] {
  const currentIdx = STAGES.findIndex((s) => s.key === parcel.current_stage);
  return STAGES.map((stage, i) => ({
    stage_id: `stg-${i}`,
    parcel_id: parcel.parcel_id,
    stage_name: stage.key,
    stage_order: i + 1,
    start_date: i <= currentIdx ? "2024-06-01T00:00:00Z" : null,
    target_date: i <= currentIdx + 1 ? "2025-01-15T00:00:00Z" : null,
    completion_date: i < currentIdx ? "2025-01-10T00:00:00Z" : null,
    status:
      i < currentIdx ? "COMPLETED" :
      i === currentIdx ? "IN_PROGRESS" : "PENDING",
    assigned_officer: parcel.assigned_officer,
    remarks: i === currentIdx && parcel.days_pending > 30 ? "SLA breach — requires escalation" : null,
  }));
}

export function ParcelDetailPage() {
  const { parcelId } = useParams<{ parcelId: string }>();

  const { data: parcel, isLoading } = useQuery({
    queryKey: ["parcel-detail", parcelId],
    queryFn: () => getParcelById(parcelId!),
    enabled: !!parcelId,
  });
  const stages = parcel ? mockStageRecords(parcel) : [];
  const currentStageIdx = parcel
    ? STAGES.findIndex((s) => s.key === parcel.current_stage)
    : -1;

  if (isLoading) {
    return (
      <div className="animate-fade-in space-y-6">
        <div className="h-8 w-64 animate-shimmer rounded" />
        <div className="h-64 animate-shimmer rounded-xl" />
      </div>
    );
  }

  if (!parcel) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500">Parcel not found</p>
        <Link to="/projects" className="text-brand-teal-blue text-sm mt-2 inline-block">← Back to Projects</Link>
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-xs text-gray-400">
        <Link to="/dashboard" className="hover:text-brand-teal-blue transition-colors">Dashboard</Link>
        <ChevronRight className="w-3 h-3" />
        <Link to="/projects" className="hover:text-brand-teal-blue transition-colors">Projects</Link>
        <ChevronRight className="w-3 h-3" />
        <Link to={`/projects/${parcel.project_id}`} className="hover:text-brand-teal-blue transition-colors">
          {parcel.project_id}
        </Link>
        <ChevronRight className="w-3 h-3" />
        <span className="text-gray-600 font-medium">{parcel.survey_number}</span>
      </div>

      {/* ── Header ────────────────────────────── */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="status" level={parcel.status}>
                {parcel.status.replace(/_/g, " ")}
              </Badge>
              <Badge variant="risk" level={
                parcel.risk_score >= 70 ? "HIGH" : parcel.risk_score >= 40 ? "MEDIUM" : "LOW"
              }>
                Risk: {parcel.risk_score}
              </Badge>
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-1">
              {parcel.survey_number}
            </h1>
            <p className="text-xs font-mono text-gray-400">ID: {parcel.parcel_id}</p>
          </div>

          {/* Quick Info */}
          <div className="flex gap-6 text-sm text-gray-500">
            <div className="flex items-center gap-1.5">
              <MapPin className="w-4 h-4" />
              {parcel.village}, {parcel.district}
            </div>
            <div className="flex items-center gap-1.5">
              <User className="w-4 h-4" />
              {parcel.owner_name}
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4" />
              {parcel.area_ha} HA
            </div>
          </div>
        </div>
      </Card>

      {/* ── 11-Stage Pipeline (Vertical) ──────── */}
      <Card>
        <CardHeader>
          <CardTitle>Acquisition Pipeline — {parcel.current_stage.replace(/_/g, " ")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            {stages.map((stage, i) => {
              const stageInfo = STAGES[i];
              const isCompleted = stage.status === "COMPLETED";
              const isCurrent = stage.status === "IN_PROGRESS";
              const isPending = stage.status === "PENDING";
              const isLast = i === stages.length - 1;

              return (
                <div key={stage.stage_id} className="flex gap-4">
                  {/* Timeline */}
                  <div className="flex flex-col items-center">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 z-10",
                        isCompleted && "bg-brand-teal-blue text-white",
                        isCurrent && "bg-white border-2 border-brand-teal-blue text-brand-teal-blue",
                        isPending && "bg-gray-100 text-gray-400"
                      )}
                    >
                      {isCompleted ? <CheckCircle2 className="w-4 h-4" /> :
                       isCurrent ? <Circle className="w-4 h-4" /> :
                       <Lock className="w-3.5 h-3.5" />}
                    </div>
                    {!isLast && (
                      <div className={cn(
                        "w-0.5 flex-1 min-h-[32px]",
                        i < currentStageIdx ? "bg-brand-teal-blue" : "bg-gray-200"
                      )} />
                    )}
                  </div>

                  {/* Content */}
                  <div className={cn("pb-6 flex-1", isLast && "pb-0")}>
                    <div className={cn(
                      "rounded-xl p-4 transition-all",
                      isCurrent && "bg-brand-teal-blue/5 border border-brand-teal-blue/20",
                      isCompleted && "bg-gray-50",
                      isPending && "opacity-50"
                    )}>
                      <div className="flex items-center justify-between mb-1">
                        <h4 className={cn(
                          "text-sm font-semibold",
                          isCurrent ? "text-brand-teal-blue" : "text-gray-800"
                        )}>
                          {stageInfo.label}
                        </h4>
                        <span className="text-[10px] text-gray-400">
                          SLA: {stageInfo.sla_days} days
                        </span>
                      </div>

                      {/* Stage metadata */}
                      <div className="flex items-center gap-4 text-[11px] text-gray-500 mt-1">
                        {stage.assigned_officer && (
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {stage.assigned_officer}
                          </span>
                        )}
                        {isCurrent && parcel.days_pending > 0 && (
                          <span className={cn(
                            "flex items-center gap-1 font-semibold",
                            parcel.days_pending > stageInfo.sla_days ? "text-red-600" : "text-amber-600"
                          )}>
                            <Clock className="w-3 h-3" />
                            {parcel.days_pending} days pending
                          </span>
                        )}
                      </div>

                      {/* SLA breach warning */}
                      {stage.remarks && (
                        <div className="mt-2 flex items-center gap-1.5 text-xs text-red-600 bg-red-50 px-2.5 py-1.5 rounded-lg">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          {stage.remarks}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* ── Bottom Row ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Documents */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-teal-blue" />
              Attached Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { name: "Joint Measurement Report.pdf", type: "SURVEY_REPORT", date: "Aug 28" },
                { name: "Ownership Record (7/12).pdf", type: "OWNERSHIP_RECORD", date: "Aug 15" },
                { name: "Notification Under Section 3A.pdf", type: "NOTIFICATION", date: "Jul 20" },
              ].map((doc) => (
                <div
                  key={doc.name}
                  className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-2.5">
                    <FileText className="w-4 h-4 text-gray-400 group-hover:text-brand-teal-blue" />
                    <div>
                      <p className="text-sm text-gray-700 group-hover:text-brand-teal-blue transition-colors">
                        {doc.name}
                      </p>
                      <p className="text-[10px] text-gray-400">{doc.type.replace(/_/g, " ")}</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-gray-400">{doc.date}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI Risk Assessment */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-brand-copper" />
              AI Risk Assessment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="relative w-16 h-16">
                  <svg className="-rotate-90" width="64" height="64">
                    <circle cx="32" cy="32" r="26" stroke="#E5E7EB" strokeWidth="6" fill="none" />
                    <circle
                      cx="32" cy="32" r="26"
                      stroke={parcel.risk_score >= 70 ? "#DC2626" : parcel.risk_score >= 40 ? "#D47A22" : "#73A557"}
                      strokeWidth="6" fill="none" strokeLinecap="round"
                      strokeDasharray={`${2 * Math.PI * 26}`}
                      strokeDashoffset={`${2 * Math.PI * 26 * (1 - parcel.risk_score / 100)}`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-bold">{parcel.risk_score}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-800">
                    {parcel.risk_score >= 70 ? "High Risk" : parcel.risk_score >= 40 ? "Medium Risk" : "Low Risk"}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Based on stage duration, historical patterns, and dispute indicators
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                {[
                  { factor: "Stage Duration", impact: parcel.days_pending > 30 ? "high" : "low", desc: `${parcel.days_pending} days in current stage` },
                  { factor: "Legal Complexity", impact: parcel.status === "BLOCKED" ? "high" : "low", desc: parcel.status === "BLOCKED" ? "Active dispute flagged" : "No disputes" },
                  { factor: "Compensation Status", impact: "medium", desc: "Valuation pending approval" },
                ].map((f) => (
                  <div key={f.factor} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
                    <div>
                      <p className="text-xs font-medium text-gray-700">{f.factor}</p>
                      <p className="text-[10px] text-gray-400">{f.desc}</p>
                    </div>
                    <Badge level={f.impact === "high" ? "HIGH" : f.impact === "medium" ? "MEDIUM" : "LOW"}>
                      {f.impact}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ParcelDetailPage;
