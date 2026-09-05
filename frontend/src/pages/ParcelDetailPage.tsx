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
import { RiskTooltip } from "@/components/RiskTooltip";
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
    assigned_officer: parcel.assigned_officer ?? null,
    remarks: i === currentIdx && (parcel.days_pending ?? 0) > 30 ? "SLA breach — requires escalation" : null,
  }));
}

export function ParcelDetailPage() {
  const { parcelId } = useParams<{ parcelId: string }>();

  const { data: parcel, isLoading, error: parcelError } = useQuery({
    queryKey: ["parcel-detail", parcelId],
    queryFn: () => getParcelById(parcelId!),
    enabled: !!parcelId,
    retry: (failureCount, err: any) => {
      const status = err?.response?.status;
      if (status === 403 || status === 404) return false;
      return failureCount < 2;
    },
  });
  const stages = parcel ? mockStageRecords(parcel) : [];

  if (isLoading) {
    return (
      <div className="animate-fade-in space-y-6">
        <div className="h-8 w-64 animate-shimmer rounded" />
        <div className="h-64 animate-shimmer rounded-xl" />
      </div>
    );
  }

  if (!parcel) {
    const status = (parcelError as any)?.response?.status;
    const isForbidden = status === 403;
    const serverDetail = (parcelError as any)?.response?.data?.detail;

    return (
      <div className="text-center py-20">
        <p className="text-gray-500">
          {isForbidden ? "You don't have access to this parcel" : "Parcel not found"}
        </p>
        <p className="text-gray-400 text-xs mt-2 max-w-md mx-auto">
          {isForbidden
            ? serverDetail ||
              "This parcel is outside your assigned state/district scope. Contact an administrator if you believe this is an error."
            : "This parcel may have been removed, or the link is invalid."}
        </p>
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
              } className="flex items-center gap-1">
                Risk: {parcel.risk_score}
                <RiskTooltip score={parcel.risk_score} type="PARCEL" />
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

      {/* ── AI Summary ────────────────────────── */}
      <Card className="bg-[#183a37]/5 border-[#183a37]/20 p-5 rounded-none border-l-4 border-l-[#183a37]">
        <div className="flex gap-4">
          <div className="flex-shrink-0 mt-0.5">
            <Brain className="w-6 h-6 text-[#183a37]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#183a37] uppercase tracking-wide mb-1">
              AI Analysis & Current State
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed">
              {parcel.status === "COMPLETED" 
                ? "This parcel has successfully completed the land acquisition process and possession has been taken. No further action is required." 
                : parcel.status === "BLOCKED" 
                ? `Critical bottleneck at the ${parcel.current_stage.replace(/_/g, " ")} stage. The parcel is currently blocked due to a high risk factor (Score: ${parcel.risk_score}). Immediate intervention required to resolve local disputes or missing documentation.`
                : parcel.risk_score >= 70
                ? `High risk of severe delay at the ${parcel.current_stage.replace(/_/g, " ")} stage. Risk score of ${parcel.risk_score} indicates potential legal or inheritance disputes. Escalation to SDM recommended.`
                : parcel.risk_score >= 40
                ? `Moderate risk at the ${parcel.current_stage.replace(/_/g, " ")} stage. Monitor SLA deadlines closely, as minor discrepancies in owner records may cause processing delays.`
                : `Processing normally at the ${parcel.current_stage.replace(/_/g, " ")} stage. Risk profile is low (${parcel.risk_score}), indicating clear title and alignment with SLA targets.`}
            </p>
          </div>
        </div>
      </Card>

      {/* ── 11-Stage Pipeline (Vertical) ──────── */}
      <Card className="rounded-none border border-gray-300 shadow-none">
        <CardHeader className="border-b border-gray-200 bg-gray-50/80 pb-4">
          <CardTitle className="text-lg font-bold text-gray-800 uppercase tracking-wide">
            Statutory Acquisition Pipeline — {parcel.current_stage.replace(/_/g, " ")}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="relative border-l-2 border-gray-200 ml-4 space-y-6">
            {stages.map((stage, i) => {
              const stageInfo = STAGES[i];
              const isCompleted = stage.status === "COMPLETED";
              const isCurrent = stage.status === "IN_PROGRESS";
              const isPending = stage.status === "PENDING";

              return (
                <div key={stage.stage_id} className="relative pl-6">
                  {/* Node Icon */}
                  <div className={cn(
                    "absolute -left-[17px] top-1 w-8 h-8 flex items-center justify-center border-2 bg-white rounded-none",
                    isCompleted && "border-[#183a37] text-[#183a37]",
                    isCurrent && "border-[#D47A22] bg-amber-50 text-[#D47A22] ring-4 ring-amber-100",
                    isPending && "border-gray-300 text-gray-400"
                  )}>
                    {isCompleted ? <CheckCircle2 className="w-4 h-4" /> :
                     isCurrent ? <Circle className="w-3 h-3 fill-current animate-pulse" /> :
                     <Lock className="w-3.5 h-3.5" />}
                  </div>

                  {/* Content Box */}
                  <div className={cn(
                    "p-4 border rounded-none transition-all",
                    isCurrent ? "bg-amber-50/40 border-[#D47A22] shadow-sm" : 
                    isCompleted ? "bg-white border-gray-200 hover:border-[#183a37]/50" : 
                    "bg-gray-50 border-gray-200 opacity-60"
                  )}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <h4 className={cn(
                        "text-sm font-bold uppercase tracking-wide",
                        isCurrent ? "text-[#D47A22]" : 
                        isCompleted ? "text-[#183a37]" : "text-gray-500"
                      )}>
                        Step {i + 1}: {stageInfo.label}
                      </h4>
                      <span className="text-[10px] font-bold font-mono px-2 py-0.5 bg-gray-100 text-gray-600 border border-gray-300">
                        SLA Limit: {stageInfo.sla_days} Days
                      </span>
                    </div>

                    {/* Stage metadata */}
                    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-medium mt-3">
                      {stage.assigned_officer && (
                        <span className="flex items-center gap-1.5 text-gray-700">
                          <User className="w-3.5 h-3.5 text-gray-400" />
                          <span className="text-gray-500 uppercase text-[10px] tracking-wider">Officer:</span> 
                          {stage.assigned_officer}
                        </span>
                      )}
                      
                      {isCurrent && (parcel.days_pending ?? 0) > 0 && (
                        <span className={cn(
                          "flex items-center gap-1.5 font-bold border px-2 py-0.5",
                          (parcel.days_pending ?? 0) > stageInfo.sla_days 
                            ? "text-red-700 border-red-300 bg-red-50" 
                            : "text-[#D47A22] border-amber-300 bg-amber-50"
                        )}>
                          <Clock className="w-3.5 h-3.5" />
                          {parcel.days_pending} Days Active
                        </span>
                      )}
                    </div>

                    {/* SLA breach warning */}
                    {stage.remarks && (
                      <div className="mt-3 flex items-start gap-2 text-xs font-semibold text-red-700 bg-red-50 border-l-2 border-red-500 p-2.5">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{stage.remarks}</span>
                      </div>
                    )}
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
                    <span className="text-sm font-bold">{Math.round(parcel.risk_score)}</span>
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
                {(() => {
                  const currentStageData = parcel.stages?.find((s: any) => s.status === "IN_PROGRESS" || s.stage_name === parcel.current_stage);
                  let daysPending = 0;
                  if (currentStageData?.start_date) {
                    const start = new Date(currentStageData.start_date).getTime();
                    daysPending = Math.max(0, Math.floor((Date.now() - start) / (1000 * 60 * 60 * 24)));
                  }

                  const factors = [];
                  // Dynamic factor 1: Historical / ML Risk
                  factors.push({
                    factor: "Historical Trend",
                    impact: parcel.risk_score >= 70 ? "high" : parcel.risk_score >= 40 ? "medium" : "low",
                    desc: parcel.risk_score >= 70 ? "High historical delay probability" : "Clearance velocity is nominal"
                  });

                  // Dynamic factor 2: Legal Complexity
                  factors.push({
                    factor: "Legal Complexity",
                    impact: (parcel.status === "BLOCKED" || parcel.status === "DISPUTED") ? "high" : "low",
                    desc: (parcel.status === "BLOCKED" || parcel.status === "DISPUTED") ? "Active dispute or block flagged" : "No active disputes"
                  });

                  // Dynamic factor 3: Stage Duration
                  factors.push({
                    factor: "Stage Duration",
                    impact: daysPending > 30 ? "high" : daysPending > 15 ? "medium" : "low",
                    desc: `${daysPending} days in current stage`
                  });

                  return factors.map((f) => (
                    <div key={f.factor} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-xs font-medium text-gray-700">{f.factor}</p>
                        <p className="text-[10px] text-gray-400">{f.desc}</p>
                      </div>
                      <Badge level={f.impact === "high" ? "HIGH" : f.impact === "medium" ? "MEDIUM" : "LOW"}>
                        {f.impact}
                      </Badge>
                    </div>
                  ));
                })()}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ParcelDetailPage;
