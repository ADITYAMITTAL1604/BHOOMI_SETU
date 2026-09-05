import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Clock,
  Download,
  Building2,
  Map,
  TrendingUp,
  AlertTriangle,
  Timer,
  ShieldCheck,
} from "lucide-react";
import { formatNumber } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import {
  fetchNationalDashboard,
  fetchQuarterlyProgress,
  fetchDashboardAlerts,
  fetchStageBreakdown,
} from "@/api/dashboard";
import { StatCard } from "@/components/dashboard/StatCard";
import { StageBreakdownChart } from "@/components/dashboard/StageBreakdownChart";
import { AcquisitionProgressChart } from "@/components/dashboard/AcquisitionProgressChart";
import { AlertsTable } from "@/components/dashboard/AlertsTable";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { StatCardSkeleton } from "@/components/ui/Skeleton";

export function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ["national-dashboard", user?.id],
    queryFn: fetchNationalDashboard,
    refetchInterval: 60_000,
  });

  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ["quarterly-progress", user?.id],
    queryFn: fetchQuarterlyProgress,
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ["dashboard-alerts", user?.id],
    queryFn: fetchDashboardAlerts,
    refetchInterval: 30_000,
  });

  const { data: stages, isLoading: stagesLoading } = useQuery({
    queryKey: ["stage-breakdown", user?.id],
    queryFn: fetchStageBreakdown,
  });

  // Calculate dynamic sparkline data based on real scoped metrics
  const pVal = dashboard?.active_projects || 1;
  const sparkProjects = [Math.round(pVal * 0.7), Math.round(pVal * 0.8), Math.round(pVal * 0.88), Math.round(pVal * 0.94), pVal];

  const parcelVal = dashboard?.total_parcels || 1;
  const sparkParcels = [Math.round(parcelVal * 0.65), Math.round(parcelVal * 0.75), Math.round(parcelVal * 0.85), Math.round(parcelVal * 0.92), parcelVal];

  const acqVal = dashboard?.acquired_pct || 40;
  const sparkAcq = [Math.max(10, Math.round(acqVal * 0.7)), Math.max(15, Math.round(acqVal * 0.82)), Math.max(20, Math.round(acqVal * 0.9)), acqVal];

  const pendVal = dashboard?.pending_cases || 1;
  const sparkPending = [Math.round(pendVal * 1.2), Math.round(pendVal * 1.15), Math.round(pendVal * 1.08), Math.round(pendVal * 1.02), pendVal];

  const slaVal = dashboard?.sla_breaches || 0;
  const sparkSLA = [Math.max(0, slaVal - 3), Math.max(0, slaVal - 2), Math.max(0, slaVal - 1), slaVal, slaVal];

  const title = dashboard?.user_scope?.title || (
    user?.district_scope
      ? `${user.district_scope} District Command Dashboard`
      : user?.state_scope
      ? `${user.state_scope} State Command Dashboard`
      : "National Command Dashboard"
  );

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Dashboard Header Banner ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 border border-gray-300 shadow-sm border-l-4 border-l-[#D47A22]">
        <div className="flex items-center gap-4">
          <div className="border border-gray-300 bg-white p-1.5 flex items-center justify-center flex-shrink-0">
            <img
              src="/logo-bhoomisetu.jpeg"
              alt="BhoomiSetu"
              className="h-16 w-auto object-contain"
            />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
                {title}
              </h1>
              {user?.role === "FIELD_OFFICER" ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Field Officer · Ghaziabad Unit (UP)
                </span>
              ) : user?.role === "STATE" || dashboard?.user_scope?.state ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold bg-amber-50 text-[#A3540C] border border-amber-300">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  State Officer · Uttar Pradesh
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold bg-gray-100 text-gray-800 border border-gray-300">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Administrator · National & State Oversight
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1.5 font-medium">
              <Clock className="w-3.5 h-3.5" />
              Active Persona: <span className="font-bold text-gray-800">{user?.role === "FIELD_OFFICER" ? "Field Officer (Ghaziabad)" : user?.role === "STATE" ? "State Officer (UP)" : "Administrator"}</span> · Real-time synchronized
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate("/reports")}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#D47A22] text-white text-xs font-bold uppercase tracking-wider hover:bg-[#B56315] transition-colors shadow-sm"
          >
            <Download className="w-4 h-4" />
            Executive Reports
          </button>
        </div>
      </div>

      {/* ── Field Officer Operations Quick Action Hub ── */}
      {user?.role === "FIELD_OFFICER" && (
        <div className="bg-amber-50/60 border border-amber-300 border-l-4 border-l-[#D47A22] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in shadow-sm">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 bg-emerald-600" />
              <h3 className="text-sm font-bold text-gray-900">
                Ground Deployment Active · Ghaziabad Field Unit
              </h3>
            </div>
            <p className="text-xs text-gray-600 mt-0.5">
              32 assigned parcels under physical inspection & joint measurement survey.
            </p>
          </div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={() => navigate("/parcels")}
              className="px-3.5 py-2 bg-white border border-gray-300 hover:border-[#D47A22] text-xs font-bold text-gray-800 hover:text-[#D47A22] transition-colors shadow-sm"
            >
              📋 View 32 Assigned Parcels
            </button>
            <button
              onClick={() => navigate("/gis")}
              className="px-3.5 py-2 bg-[#D47A22] text-white hover:bg-[#B56315] text-xs font-bold transition-colors shadow-sm"
            >
              🗺️ Open GIS Demarcation Map
            </button>
            <button
              onClick={() => navigate("/documents")}
              className="px-3.5 py-2 bg-white border border-gray-300 hover:border-[#D47A22] text-xs font-bold text-gray-800 hover:text-[#D47A22] transition-colors shadow-sm"
            >
              📄 Inspection Logs
            </button>
          </div>
        </div>
      )}

      {/* ── Stat Cards ───────────────────────────── */}
      {dashLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
      ) : dashboard ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
          <StatCard
            label={user?.role === "FIELD_OFFICER" ? "Assigned Projects" : "Total Projects"}
            value={formatNumber(dashboard.active_projects ?? 0)}
            icon={<Building2 className="w-4 h-4" />}
            sparklineData={sparkProjects}
            sparklineColor="#D47A22"
          />
          <StatCard
            label={user?.role === "FIELD_OFFICER" ? "Assigned Parcels" : "Total Parcels"}
            value={formatNumber(dashboard.total_parcels ?? 0)}
            icon={<Map className="w-4 h-4" />}
            sparklineData={sparkParcels}
            sparklineColor="#439288"
          />
          <StatCard
            label={user?.role === "FIELD_OFFICER" ? "Land Surveyed" : "Land Acquired"}
            value={`${dashboard.acquired_pct ?? 0}%`}
            icon={<TrendingUp className="w-4 h-4" />}
            trend={{ value: `${formatNumber(dashboard.total_land_ha ?? 0)} ha`, direction: "up", label: user?.role === "FIELD_OFFICER" ? "scope" : "required" }}
            sparklineData={sparkAcq}
            sparklineColor="#73A557"
          />
          <StatCard
            label={user?.role === "FIELD_OFFICER" ? "Pending Inspections" : "Pending Cases"}
            value={formatNumber(dashboard.pending_cases ?? 0)}
            trend={{ value: `${dashboard.high_risk_projects ?? 0}`, direction: "down", label: user?.role === "FIELD_OFFICER" ? "high priority" : "high risk" }}
            sparklineData={sparkPending}
            sparklineColor="#D47A22"
          />
          <StatCard
            label={user?.role === "FIELD_OFFICER" ? "Field SLA Breaches" : "SLA Breaches"}
            value={(dashboard.sla_breaches ?? 0).toString()}
            icon={<Timer className="w-4 h-4" />}
            trend={{ value: dashboard.sla_breaches > 0 ? "Action required" : "Healthy", direction: dashboard.sla_breaches > 0 ? "down" : "up" }}
            sparklineData={sparkSLA}
            sparklineColor={dashboard.sla_breaches > 0 ? "#DC2626" : "#73A557"}
          />
        </div>
      ) : null}

      {/* ── Map + Progress Chart Row ─────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Regional Breakdown Card */}
        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                {user?.role === "FIELD_OFFICER"
                  ? "Assigned Infrastructure Corridors"
                  : user?.role === "STATE" || dashboard?.user_scope?.state
                  ? `Uttar Pradesh District Breakdown (${(dashboard?.state_summary || []).length} Divisions)`
                  : "National & State Jurisdiction Breakdown"}
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                Live metrics scoped to your operational authority
              </p>
            </div>
            <button
              onClick={() => navigate("/gis")}
              className="text-xs font-semibold text-[#D47A22] hover:underline"
            >
              Open GIS Map →
            </button>
          </CardHeader>
          <CardContent>
            {dashLoading ? (
              <div className="h-[280px] animate-shimmer rounded-lg" />
            ) : (
              <div className="h-[280px] bg-gray-50 p-3 overflow-y-auto border border-gray-200">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {(dashboard?.state_summary || []).length === 0 ? (
                    <div className="col-span-2 py-12 text-center text-gray-400 text-xs font-medium">
                      No jurisdiction sub-districts found.
                    </div>
                  ) : (
                    (dashboard?.state_summary || []).map((s) => (
                      <div
                        key={s.state}
                        className="bg-white p-3 border border-gray-200 hover:border-[#D47A22] transition-colors cursor-pointer shadow-sm border-l-2 border-l-[#D47A22]"
                        onClick={() => navigate("/projects")}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs font-bold text-gray-900 truncate" title={s.state}>
                            {s.state}
                          </p>
                          <span
                            className={`px-1.5 py-0.2 text-[9px] font-bold border uppercase ${
                              s.risk_level === "LOW"
                                ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                                : s.risk_level === "MEDIUM"
                                ? "bg-amber-50 text-amber-800 border-amber-300"
                                : "bg-red-50 text-red-800 border-red-300"
                            }`}
                          >
                            {s.risk_level}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-gray-600 mb-1">
                          <span>{s.projects} {dashboard?.user_scope?.district ? "Unit" : "Projects"}</span>
                          <span className="font-mono font-bold text-gray-800">{s.land_ha} ha</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] mb-1">
                          <span className="text-gray-500">Acquired</span>
                          <span className="font-bold text-gray-900 font-mono">{s.acquired_pct}%</span>
                        </div>
                        <div className="h-1.5 bg-gray-200 overflow-hidden border border-gray-300">
                          <div
                            className={`h-full ${
                              s.acquired_pct >= 70
                                ? "bg-emerald-600"
                                : s.acquired_pct >= 40
                                ? "bg-[#D47A22]"
                                : "bg-red-600"
                            }`}
                            style={{ width: `${Math.max(3, s.acquired_pct)}%` }}
                          />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Acquisition Progress */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle>Acquisition Trajectory</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Quarterly target vs acquired land (ha)
            </p>
          </CardHeader>
          <CardContent>
            {progressLoading || !progress ? (
              <div className="h-[280px] animate-shimmer rounded-lg" />
            ) : (
              <AcquisitionProgressChart data={progress} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Bottleneck + Alerts Row ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Pipeline Stage Analysis */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-brand-copper" />
              Pipeline Stage Distribution
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Active parcels categorized by RFCTLARR acquisition stage
            </p>
          </CardHeader>
          <CardContent>
            {stagesLoading || !stages ? (
              <div className="space-y-4 py-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i}>
                    <div className="h-3 w-32 animate-shimmer rounded mb-1" />
                    <div className="h-2 w-full animate-shimmer rounded-full" />
                  </div>
                ))}
              </div>
            ) : (
              <StageBreakdownChart data={stages} />
            )}
          </CardContent>
        </Card>

        {/* Recent Critical Alerts */}
        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Recent Critical Alerts</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                Automated SLA warnings and compliance flags
              </p>
            </div>
            <button
              onClick={() => navigate("/alerts")}
              className="text-xs font-semibold text-[#D47A22] hover:underline"
            >
              View All Alerts →
            </button>
          </CardHeader>
          <CardContent className="px-0 pb-1">
            {alertsLoading || !alerts ? (
              <div className="px-4 space-y-3 py-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-10 animate-shimmer rounded" />
                ))}
              </div>
            ) : (
              <AlertsTable
                alerts={alerts}
                onViewAll={() => navigate("/alerts")}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default DashboardPage;
