import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Clock,
  Download,
  Building2,
  Map,
  TrendingUp,
  AlertTriangle,
  Timer,
} from "lucide-react";
import { formatNumber } from "@/lib/utils";
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
import { StatCardSkeleton, ChartSkeleton } from "@/components/ui/Skeleton";

export function DashboardPage() {
  const navigate = useNavigate();

  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ["national-dashboard"],
    queryFn: fetchNationalDashboard,
    refetchInterval: 60_000, // Auto-refresh every 60s
  });

  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ["quarterly-progress"],
    queryFn: fetchQuarterlyProgress,
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ["dashboard-alerts"],
    queryFn: fetchDashboardAlerts,
    refetchInterval: 30_000,
  });

  const { data: stages, isLoading: stagesLoading } = useQuery({
    queryKey: ["stage-breakdown"],
    queryFn: fetchStageBreakdown,
  });

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header ───────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
            <LayoutDashboard className="w-6 h-6 text-brand-teal-blue" />
            National Command Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            Last updated: Just now
          </p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-teal-blue text-white text-sm font-medium rounded-xl hover:bg-[#245d82] transition-colors">
          <Download className="w-4 h-4" />
          Export Report
        </button>
      </div>

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
            label="Total Projects"
            value={formatNumber(dashboard.active_projects)}
            icon={<Building2 className="w-4 h-4" />}
            sparklineData={[800, 920, 1050, 1100, 1180, 1248]}
            sparklineColor="#2B6D97"
          />
          <StatCard
            label="Total Parcels"
            value={`${(dashboard.total_parcels / 1000).toFixed(1)}K`}
            icon={<Map className="w-4 h-4" />}
            sparklineData={[28, 32, 36, 38, 42, 45.2]}
            sparklineColor="#439288"
          />
          <StatCard
            label="Land Acquired"
            value={`${dashboard.acquired_pct}%`}
            icon={<TrendingUp className="w-4 h-4" />}
            trend={{ value: "+12%", direction: "up", label: "this month" }}
            sparklineData={[42, 48, 52, 58, 63, 68.4]}
            sparklineColor="#73A557"
          />
          <StatCard
            label="Pending Cases"
            value={formatNumber(dashboard.pending_cases)}
            trend={{ value: "-12%", direction: "down", label: "this month" }}
            sparklineData={[4200, 4000, 3800, 3600, 3500, 3402]}
            sparklineColor="#D47A22"
          />
          <StatCard
            label="SLA Breaches"
            value={dashboard.sla_breaches.toString()}
            icon={<Timer className="w-4 h-4" />}
            trend={{ value: "Action required", direction: "up" }}
            sparklineData={[28, 32, 35, 38, 40, 42]}
            sparklineColor="#DC2626"
          />
        </div>
      ) : null}

      {/* ── Map + Progress Chart Row ─────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* State-wise Acquisition Heatmap */}
        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              State-wise Acquisition Heatmap
            </CardTitle>
            <button className="text-gray-400 hover:text-gray-600">
              <span className="text-lg">⋮</span>
            </button>
          </CardHeader>
          <CardContent>
            {dashLoading ? (
              <div className="h-[280px] animate-shimmer rounded-lg" />
            ) : (
              <div className="h-[280px] bg-brand-linen rounded-xl flex items-center justify-center relative overflow-hidden">
                {/* Mini state summary cards inside the map area */}
                <div className="absolute inset-4 flex flex-wrap gap-2 content-start overflow-y-auto">
                  {dashboard?.state_summary.map((s) => (
                    <div
                      key={s.state}
                      className="bg-white/90 backdrop-blur-sm rounded-lg px-3 py-2 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => navigate(`/dashboard?state=${s.state}`)}
                    >
                      <p className="text-xs font-semibold text-gray-800">
                        {s.state}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-gray-500">
                          {s.projects} projects
                        </span>
                        <span
                          className={`w-2 h-2 rounded-full ${
                            s.risk_level === "LOW"
                              ? "bg-emerald-400"
                              : s.risk_level === "MEDIUM"
                              ? "bg-amber-400"
                              : "bg-red-400"
                          }`}
                        />
                        <span className="text-[10px] font-semibold text-gray-700">
                          {s.acquired_pct}%
                        </span>
                      </div>
                      {/* Mini progress bar */}
                      <div className="h-1 bg-gray-100 rounded-full mt-1.5 w-24">
                        <div
                          className={`h-full rounded-full ${
                            s.acquired_pct > 70
                              ? "bg-emerald-400"
                              : s.acquired_pct > 50
                              ? "bg-amber-400"
                              : "bg-red-400"
                          }`}
                          style={{ width: `${s.acquired_pct}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Acquisition Progress */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Acquisition Progress</CardTitle>
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
        {/* Bottleneck Stage Analysis */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-brand-copper" />
              Bottleneck Stage Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stagesLoading || !stages ? (
              <div className="space-y-4">
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
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Critical Alerts</CardTitle>
          </CardHeader>
          <CardContent className="px-0 pb-1">
            {alertsLoading || !alerts ? (
              <div className="px-4 space-y-3">
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
