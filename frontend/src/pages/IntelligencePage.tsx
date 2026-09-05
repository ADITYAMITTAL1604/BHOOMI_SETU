import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Brain,
  AlertTriangle,
  TrendingUp,
  ChevronRight,
  Target,
  Zap,
  BarChart3,
  Layers,
} from "lucide-react";
import { fetchBottleneckAnalysis, fetchDelayRisk, fetchPriorityCases } from "@/api/analytics";
import { listProjects } from "@/api/projects";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { cn, formatNumber } from "@/lib/utils";

export function IntelligencePage() {
  const navigate = useNavigate();
  const [selectedProjectId, setSelectedProjectId] = useState<string>("default");

  const { data: projectsData } = useQuery({
    queryKey: ["projects-dropdown"],
    queryFn: () => listProjects({ limit: 50 }),
  });

  const { data: bottleneck, isLoading: bnLoading, isError: bnError, refetch: refetchBn } = useQuery({
    queryKey: ["bottleneck", selectedProjectId],
    queryFn: () => fetchBottleneckAnalysis(selectedProjectId),
    staleTime: 30_000,
    retry: 2,
  });

  const { data: delayRisk, isLoading: drLoading, isError: drError, refetch: refetchDr } = useQuery({
    queryKey: ["delay-risk", selectedProjectId],
    queryFn: () => fetchDelayRisk(selectedProjectId),
    staleTime: 30_000,
    retry: 2,
  });

  const { data: priorityRaw, isLoading: prLoading, isError: prError, refetch: refetchPr } = useQuery({
    queryKey: ["priority-cases", selectedProjectId],
    queryFn: () => fetchPriorityCases(selectedProjectId),
    staleTime: 30_000,
    retry: 2,
  });

  const projectsList = projectsData?.data || [];
  const allStages = (bottleneck as any)?.all_stages || (bottleneck as any)?.stages || [];
  const primaryBn = (bottleneck as any)?.primary_bottleneck;
  const featureList = (delayRisk as any)?.feature_importance || (delayRisk as any)?.top_factors || [];
  const priorityList = Array.isArray(priorityRaw) ? priorityRaw : ((priorityRaw as any)?.ranked_parcels || []);

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header with Project Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
            <Brain className="w-6 h-6 text-brand-copper" />
            Intelligence & Analytics
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI-powered insights for proactive decision making.
          </p>
        </div>

        {projectsList.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">Project:</span>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="text-xs bg-white border border-gray-200 rounded-none px-3 py-2 text-gray-700 font-semibold shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-copper/30"
            >
              <option value="default">Default Active Project</option>
              {projectsList.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* ── AI Executive Summary ─────────────── */}
      <Card className="bg-[#183a37]/5 border-[#183a37]/20 p-5 rounded-none border-l-4 border-l-[#183a37]">
        <div className="flex gap-4">
          <div className="flex-shrink-0 mt-0.5">
            <Brain className="w-6 h-6 text-[#183a37]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#183a37] uppercase tracking-wide mb-1">
              Project Intelligence Executive Summary
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed">
              {primaryBn 
                ? `The AI has identified a critical bottleneck at the ${String(primaryBn.stage || "SURVEY").replace(/_/g, " ")} stage, where ${primaryBn.pending_count || 0} parcels are currently pending. 
                   The primary drivers for this delay are ${featureList.length > 0 ? (featureList[0] as any).feature.replace(/_/g, " ").toLowerCase() : "administrative backlogs"} and 
                   ${featureList.length > 1 ? (featureList[1] as any).feature.replace(/_/g, " ").toLowerCase() : "local disputes"}. 
                   Immediate intervention is recommended for the top priority parcels to prevent cascading delays to the overall project timeline.`
                : "The project is currently progressing according to schedule with no major systemic bottlenecks detected. Minor processing delays are localized and within SLA tolerances. Continue monitoring high-priority parcels."}
            </p>
          </div>
        </div>
      </Card>

      {/* ── Top Row: Bottleneck + Delay Risk ──── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Bottleneck Intelligence */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-brand-copper" />
              Bottleneck Intelligence
            </CardTitle>
          </CardHeader>
          <CardContent>
            {bnLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-8 animate-shimmer rounded" />
                ))}
              </div>
            ) : bnError || !bottleneck ? (
              <div className="text-center py-8 text-sm text-gray-500">
                <Layers className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p>Bottleneck data not available for this project.</p>
                <button
                  onClick={() => refetchBn()}
                  className="mt-2 text-xs font-semibold text-brand-copper hover:underline"
                >
                  Retry Analysis
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Primary bottleneck alert */}
                {primaryBn && (
                  <div className="bg-red-50 border border-red-100 rounded-none p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="w-4 h-4 text-red-500" />
                      <span className="text-xs font-bold text-red-700 uppercase tracking-wider">
                        Primary Bottleneck
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-gray-800 mb-1">
                      {String(primaryBn.stage || "SURVEY").replace(/_/g, " ")} Stage
                    </p>
                    <p className="text-xs text-gray-600 leading-relaxed">
                      {primaryBn.impact_description || "Critical procedural backlog requiring attention."}
                    </p>
                    <div className="flex gap-4 mt-3">
                      <div className="text-center">
                        <p className="text-lg font-bold text-red-600">
                          {formatNumber(primaryBn.pending_count || 0)}
                        </p>
                        <p className="text-[10px] text-gray-500">Pending</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-brand-copper">
                          {primaryBn.avg_days_pending || 0}d
                        </p>
                        <p className="text-[10px] text-gray-500">Avg Wait</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-gray-800">
                          {Math.round((primaryBn.breach_rate || 0) * 100)}%
                        </p>
                        <p className="text-[10px] text-gray-500">SLA Breach</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* All stages ranked */}
                <div className="space-y-2">
                  {allStages.slice(0, 5).map((stage: any, i: number) => (
                    <div key={stage.stage} className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-gray-400 w-4">{i + 1}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-xs font-medium text-gray-700">
                            {String(stage.stage).replace(/_/g, " ")}
                          </span>
                          <span className="text-[10px] text-gray-400">
                            {stage.pending_count || stage.in_progress_count || 0} pending · {stage.avg_days_pending || 0}d avg
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-gray-100 rounded-none overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-none",
                              i === 0 ? "bg-red-500" : i === 1 ? "bg-orange-400" : "bg-brand-teal-blue"
                            )}
                            style={{ width: `${Math.min(100, Math.max(8, (stage.bottleneck_score || 0.1) * 100))}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Delay Risk Prediction */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-red-500" />
              Delay Risk Prediction
            </CardTitle>
          </CardHeader>
          <CardContent>
            {drLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-8 animate-shimmer rounded" />
                ))}
              </div>
            ) : drError || !delayRisk ? (
              <div className="text-center py-8 text-sm text-gray-500">
                <Brain className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p>Delay risk prediction not available for this project.</p>
                <button
                  onClick={() => refetchDr()}
                  className="mt-2 text-xs font-semibold text-brand-copper hover:underline"
                >
                  Retry Prediction
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Risk gauge */}
                <div className="flex items-center gap-6">
                  <div className="relative w-24 h-24">
                    <svg className="-rotate-90" width="96" height="96">
                      <circle cx="48" cy="48" r="40" stroke="#E5E7EB" strokeWidth="8" fill="none" />
                      <circle
                        cx="48"
                        cy="48"
                        r="40"
                        stroke={delayRisk.risk_score >= 0.7 ? "#DC2626" : delayRisk.risk_score >= 0.4 ? "#D47A22" : "#73A557"}
                        strokeWidth="8"
                        fill="none"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 40}`}
                        strokeDashoffset={`${2 * Math.PI * 40 * (1 - (delayRisk.risk_score ?? 0))}`}
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-xl font-bold">{Math.round((delayRisk.risk_score ?? 0) * 100)}%</span>
                      <span className="text-[9px] text-gray-400 font-semibold uppercase">Risk</span>
                    </div>
                  </div>
                  <div>
                    <Badge variant="risk" level={delayRisk.risk_level ?? "LOW"}>
                      {delayRisk.risk_level ?? "LOW"} RISK
                    </Badge>
                    <p className="text-xs text-gray-500 mt-2">
                      Confidence: {Math.round((delayRisk.confidence ?? 0) * 100)}%
                    </p>
                    <p className="text-[10px] text-gray-400">
                      Based on {delayRisk.snapshots_used ?? 0} data snapshot(s)
                    </p>
                  </div>
                </div>

                {/* Feature importance (SHAP) */}
                <div>
                  <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Key Delay Factors (SHAP)
                  </p>
                  <div className="space-y-2">
                    {featureList.map((feat: any) => {
                      const imp = typeof feat.importance === "number" ? feat.importance : (feat.shap_value || 0);
                      const dir = feat.direction || (imp > 0 ? "positive" : "negative");
                      const label = feat.label || feat.title || String(feat.feature).replace(/_/g, " ");

                      return (
                        <div key={feat.feature} className="flex items-center gap-2">
                          <span
                            className={cn(
                              "w-1.5 h-1.5 rounded-none flex-shrink-0",
                              dir === "positive" ? "bg-red-400" : "bg-emerald-400"
                            )}
                          />
                          <span className="text-xs text-gray-700 flex-1">{label}</span>
                          <div className="w-20 h-1.5 bg-gray-100 rounded-none overflow-hidden">
                            <div
                              className={cn("h-full rounded-none", dir === "positive" ? "bg-red-400" : "bg-emerald-400")}
                              style={{ width: `${Math.min(100, Math.max(10, Math.abs(imp) * 100 * 3))}%` }}
                            />
                          </div>
                          <span className="text-[10px] font-mono text-gray-500 w-8 text-right">
                            {imp > 0 ? "+" : ""}{imp.toFixed(2)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Priority Cases ───────────────────── */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Target className="w-4 h-4 text-brand-teal-blue" />
            AI-Recommended Priority Cases
          </CardTitle>
          <div className="flex items-center gap-2 text-[10px] text-gray-400">
            <button
              onClick={() => refetchPr()}
              className="font-medium text-brand-teal-blue hover:underline"
            >
              Refresh
            </button>
            <span className="text-gray-300">•</span>
            <div className="flex items-center gap-1">
              <BarChart3 className="w-3 h-3" />
              Sorted by priority score
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {prLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 animate-shimmer rounded" />
              ))}
            </div>
          ) : prError || priorityList.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-500">
              <Target className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p>No parcels currently flagged for priority intervention.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {priorityList.slice(0, 10).map((c: any, i: number) => (
                <div
                  key={c.parcel_id || i}
                  className="flex items-start gap-4 p-4 rounded-none border border-gray-100 hover:shadow-card-hover transition-shadow cursor-pointer group"
                  onClick={() => navigate(`/parcels/${c.parcel_id}`)}
                >
                  {/* Rank */}
                  <div
                    className={cn(
                      "w-8 h-8 rounded-none flex items-center justify-center flex-shrink-0 text-xs font-bold",
                      i === 0 ? "bg-red-100 text-red-700" :
                      i === 1 ? "bg-orange-100 text-orange-700" :
                      "bg-gray-100 text-gray-600"
                    )}
                  >
                    #{i + 1}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-gray-800 group-hover:text-brand-teal-blue transition-colors">
                        {c.survey_number}
                      </span>
                      <span className="text-[10px] font-mono text-gray-400">{c.parcel_id}</span>
                      <Badge variant="severity" level={c.impact || "INFO"}>
                        {c.impact || "INFO"}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">
                      {c.recommendation || c.intervention_recommendation || "Continue standard monitoring."}
                    </p>
                    <div className="flex items-center gap-4 mt-1.5 text-[10px] text-gray-400">
                      <span>Stage: {String(c.stage || c.current_stage || "SURVEY").replace(/_/g, " ")}</span>
                      <span>{c.days_pending || 0} days pending</span>
                      <span>Score: {typeof c.priority_score === "number" ? c.priority_score.toFixed(2) : c.priority_score}</span>
                    </div>
                  </div>

                  <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-brand-teal-blue flex-shrink-0 mt-2" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default IntelligencePage;
