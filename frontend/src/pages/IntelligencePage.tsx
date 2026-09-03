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
} from "lucide-react";
import { fetchBottleneckAnalysis, fetchDelayRisk, fetchPriorityCases } from "@/api/analytics";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { cn, formatNumber } from "@/lib/utils";

export function IntelligencePage() {
  const navigate = useNavigate();

  const { data: bottleneck, isLoading: bnLoading } = useQuery({
    queryKey: ["bottleneck"], queryFn: fetchBottleneckAnalysis,
  });
  const { data: delayRisk, isLoading: drLoading } = useQuery({
    queryKey: ["delay-risk"], queryFn: () => fetchDelayRisk(),
  });
  const { data: priority, isLoading: prLoading } = useQuery({
    queryKey: ["priority-cases"], queryFn: fetchPriorityCases,
  });

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
          <Brain className="w-6 h-6 text-brand-copper" />
          Intelligence & Analytics
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          AI-powered insights for proactive decision making.
        </p>
      </div>

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
            {bnLoading || !bottleneck ? (
              <div className="space-y-4">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-8 animate-shimmer rounded" />)}</div>
            ) : (
              <div className="space-y-4">
                {/* Primary bottleneck alert */}
                <div className="bg-red-50 border border-red-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4 text-red-500" />
                    <span className="text-xs font-bold text-red-700 uppercase tracking-wider">
                      Primary Bottleneck
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-gray-800 mb-1">
                    {bottleneck.primary_bottleneck.stage.replace(/_/g, " ")} Stage
                  </p>
                  <p className="text-xs text-gray-600 leading-relaxed">
                    {bottleneck.primary_bottleneck.impact_description}
                  </p>
                  <div className="flex gap-4 mt-3">
                    <div className="text-center">
                      <p className="text-lg font-bold text-red-600">{formatNumber(bottleneck.primary_bottleneck.pending_count)}</p>
                      <p className="text-[10px] text-gray-500">Pending</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold text-brand-copper">{bottleneck.primary_bottleneck.avg_days_pending}d</p>
                      <p className="text-[10px] text-gray-500">Avg Wait</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold text-gray-800">{Math.round(bottleneck.primary_bottleneck.breach_rate * 100)}%</p>
                      <p className="text-[10px] text-gray-500">SLA Breach</p>
                    </div>
                  </div>
                </div>

                {/* All stages ranked */}
                <div className="space-y-2">
                  {bottleneck.all_stages.slice(0, 5).map((stage, i) => (
                    <div key={stage.stage} className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-gray-400 w-4">{i + 1}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-xs font-medium text-gray-700">
                            {stage.stage.replace(/_/g, " ")}
                          </span>
                          <span className="text-xs font-semibold text-gray-900">
                            {Math.round(stage.bottleneck_score * 100)}
                          </span>
                        </div>
                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full",
                              stage.bottleneck_score > 0.7 ? "bg-red-400" :
                              stage.bottleneck_score > 0.5 ? "bg-brand-copper" : "bg-brand-teal-blue"
                            )}
                            style={{ width: `${stage.bottleneck_score * 100}%` }}
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
            {drLoading || !delayRisk ? (
              <div className="space-y-4">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-8 animate-shimmer rounded" />)}</div>
            ) : (
              <div className="space-y-4">
                {/* Risk gauge */}
                <div className="flex items-center gap-6">
                  <div className="relative w-24 h-24">
                    <svg className="-rotate-90" width="96" height="96">
                      <circle cx="48" cy="48" r="40" stroke="#E5E7EB" strokeWidth="8" fill="none" />
                      <circle cx="48" cy="48" r="40"
                        stroke={delayRisk.risk_score >= 0.7 ? "#DC2626" : delayRisk.risk_score >= 0.4 ? "#D47A22" : "#73A557"}
                        strokeWidth="8" fill="none" strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 40}`}
                        strokeDashoffset={`${2 * Math.PI * 40 * (1 - delayRisk.risk_score)}`}
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-xl font-bold">{Math.round(delayRisk.risk_score * 100)}%</span>
                      <span className="text-[9px] text-gray-400 font-semibold uppercase">Risk</span>
                    </div>
                  </div>
                  <div>
                    <Badge variant="risk" level={delayRisk.risk_level}>{delayRisk.risk_level} RISK</Badge>
                    <p className="text-xs text-gray-500 mt-2">
                      Confidence: {Math.round(delayRisk.confidence * 100)}%
                    </p>
                    <p className="text-[10px] text-gray-400">
                      Based on {delayRisk.snapshots_used} data snapshots
                    </p>
                  </div>
                </div>

                {/* Feature importance (SHAP) */}
                <div>
                  <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Key Delay Factors (SHAP)
                  </p>
                  <div className="space-y-2">
                    {delayRisk.feature_importance.map((feat) => (
                      <div key={feat.feature} className="flex items-center gap-2">
                        <span className={cn(
                          "w-1.5 h-1.5 rounded-full flex-shrink-0",
                          feat.direction === "positive" ? "bg-red-400" : "bg-emerald-400"
                        )} />
                        <span className="text-xs text-gray-700 flex-1">{feat.label}</span>
                        <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={cn("h-full rounded-full", feat.direction === "positive" ? "bg-red-400" : "bg-emerald-400")}
                            style={{ width: `${Math.abs(feat.importance) * 100 * 3}%` }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-gray-500 w-8 text-right">
                          {feat.importance > 0 ? "+" : ""}{feat.importance.toFixed(2)}
                        </span>
                      </div>
                    ))}
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
          <div className="flex items-center gap-1 text-[10px] text-gray-400">
            <BarChart3 className="w-3 h-3" />
            Sorted by priority score
          </div>
        </CardHeader>
        <CardContent>
          {prLoading || !priority ? (
            <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-16 animate-shimmer rounded" />)}</div>
          ) : (
            <div className="space-y-3">
              {priority.map((c, i) => (
                <div
                  key={c.parcel_id}
                  className="flex items-start gap-4 p-4 rounded-xl border border-gray-100 hover:shadow-card-hover transition-shadow cursor-pointer group"
                  onClick={() => navigate(`/parcels/${c.parcel_id}`)}
                >
                  {/* Rank */}
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold",
                    i === 0 ? "bg-red-100 text-red-700" :
                    i === 1 ? "bg-orange-100 text-orange-700" :
                    "bg-gray-100 text-gray-600"
                  )}>
                    #{i + 1}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-gray-800 group-hover:text-brand-teal-blue transition-colors">
                        {c.survey_number}
                      </span>
                      <span className="text-[10px] font-mono text-gray-400">{c.parcel_id}</span>
                      <Badge variant="severity" level={c.impact}>{c.impact}</Badge>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">{c.recommendation}</p>
                    <div className="flex items-center gap-4 mt-1.5 text-[10px] text-gray-400">
                      <span>Stage: {c.stage.replace(/_/g, " ")}</span>
                      <span>{c.days_pending} days pending</span>
                      <span>Score: {c.priority_score}</span>
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
