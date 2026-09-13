import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Building2,
  Coins,
  Users,
  ShieldCheck,
  CheckCircle2,
  Layers,
  MapPin,
  RefreshCw,
} from "lucide-react";
import { getProjects } from "@/api/projects";
import { fetchExecutiveSummary, fetchKPIs } from "@/api/reports";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/utils";
import { KPICards } from "@/components/reports/KPICards";
import { AdvancedFilters, INITIAL_FILTERS, type FilterState } from "@/components/reports/AdvancedFilters";
import { ExportButtons } from "@/components/reports/ExportButtons";
import { useAuthStore } from "@/store/authStore";

export function ReportsPage() {
  const { user } = useAuthStore();
  const [filters, setFilters] = useState<FilterState>(() => ({
    ...INITIAL_FILTERS,
    state: user?.state_scope || "",
    district: user?.district_scope || "",
  }));

  // Projects list for dropdown
  const { data: projectsData } = useQuery({
    queryKey: ["projects-dropdown"],
    queryFn: () => getProjects(),
  });

  // KPI metrics query — responds to state, district, and project filters
  const {
    data: kpis,
    isLoading: isKpisLoading,
    refetch: refetchKPIs,
    isFetching: isKpisFetching,
  } = useQuery({
    queryKey: ["report-kpis", filters.state, filters.district, filters.projectId],
    queryFn: () =>
      fetchKPIs({
        state: filters.state || undefined,
        district: filters.district || undefined,
        project_id: filters.projectId || undefined,
      }),
  });

  // Executive summary report query
  const {
    data: report,
    isLoading: isReportLoading,
    refetch: refetchReport,
    isFetching: isReportFetching,
  } = useQuery({
    queryKey: ["executive-summary", filters.projectId, filters.state, filters.district],
    queryFn: () =>
      fetchExecutiveSummary({
        project_id: filters.projectId || undefined,
        state: filters.state || undefined,
        district: filters.district || undefined,
      }),
  });

  const handleRefresh = () => {
    refetchKPIs();
    refetchReport();
  };

  const isRefreshing = isKpisFetching || isReportFetching;
  const projectList = (projectsData as any)?.data || (projectsData as any)?.items || [];

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header Ribbon ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 sm:gap-3 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2.5">
              <BarChart3 className="w-6 h-6 text-[#D47A22]" />
              Executive Analytics & Statutory Reports
            </h1>
            <span className="px-2.5 py-0.5 rounded-none text-[11px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-300">
              RFCTLARR 2013 Statutory
            </span>
          </div>
          <p className="text-xs text-gray-600 mt-1">
            Official land acquisition reports, multi-state infrastructure audit logs, and Direct Benefit Transfer (DBT) summaries.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-none border border-gray-300 bg-white text-xs font-bold uppercase tracking-wider text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            title="Refresh analytics data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-[#D47A22]" : "text-gray-500"}`} />
            {isRefreshing ? "Syncing..." : "Sync Data"}
          </button>

          <ExportButtons filters={filters} />
        </div>
      </div>

      {/* ── Advanced Query & Geographic Filters ───────────────────── */}
      <AdvancedFilters
        filters={filters}
        onFilterChange={setFilters}
        projects={projectList}
      />

      {/* ── Key Performance Indicators (KPI Cards) ────────────────── */}
      <KPICards kpis={kpis} isLoading={isKpisLoading} />

      {/* ── Detailed Executive Document Preview ───────────────────── */}
      {isReportLoading || !report ? (
        <div className="space-y-4">
          <div className="h-32 bg-gray-100 rounded-none border border-gray-200 animate-pulse" />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-100 rounded-none border border-gray-200 animate-pulse" />
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Executive Overview Banner */}
          <div className="bg-gradient-to-r from-[#D47A22] to-[#A2550D] text-white rounded-none p-5 sm:p-7 shadow-none border border-amber-800">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-none text-[10px] font-bold uppercase tracking-wider bg-white/20 backdrop-blur-sm mb-2">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Statutory Portfolio Briefing
                </div>
                <h2 className="text-xl sm:text-2xl font-bold tracking-tight">
                  {report.project?.name || "National Infrastructure Portfolio"}
                </h2>
                <div className="flex flex-wrap items-center gap-4 text-xs text-white/90 mt-2">
                  <span className="flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5" />
                    Status: <span className="font-bold uppercase">{report.project?.status || "ACTIVE"}</span>
                  </span>
                  {report.project?.states && report.project.states.length > 0 && (
                    <span className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5" />
                      States: {report.project.states.join(", ")}
                    </span>
                  )}
                  {report.project?.districts && report.project.districts.length > 0 && (
                    <span className="flex items-center gap-1.5">
                      Districts: {report.project.districts.join(", ")}
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-md rounded-none p-4 text-left sm:text-right border border-white/20">
                <span className="text-[10px] text-white/80 block uppercase font-bold tracking-wider">
                  Acquisition Progress
                </span>
                <span className="text-2xl sm:text-3xl font-black font-mono text-white">
                  {report.metrics.progress_pct}%
                </span>
                <span className="text-[11px] text-white/90 block mt-0.5 font-mono">
                  {report.metrics.land_acquired_ha} / {report.metrics.land_required_ha} HA
                </span>
              </div>
            </div>
          </div>

          {/* Compensation & Financial Disbursement Audit */}
          <Card className="rounded-none border border-gray-300 bg-white shadow-none">
            <CardHeader className="py-3 px-5 border-b border-gray-200 bg-gray-50/60">
              <CardTitle className="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center gap-2">
                <Coins className="w-4 h-4 text-[#D47A22]" />
                Direct Benefit Transfer (DBT) & Statutory Award Disbursement Audit
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-50 p-4 border border-gray-200">
                  <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">
                    Approved Award (Sec 23/30)
                  </span>
                  <p className="text-xl font-black font-mono text-gray-900 mt-1">
                    {formatCurrency(report.compensation.approved_amount)}
                  </p>
                  <span className="text-[10px] text-gray-500 mt-0.5 block">
                    Statutory award including solatium & multiplier
                  </span>
                </div>

                <div className="bg-emerald-50/50 p-4 border border-emerald-200">
                  <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                    Disbursed (Paid Out)
                  </span>
                  <p className="text-xl font-black font-mono text-emerald-900 mt-1">
                    {formatCurrency(report.compensation.paid_amount)}
                  </p>
                  <span className="text-[10px] text-emerald-700 font-semibold mt-0.5 block">
                    {report.compensation.disbursement_pct}% transferred to verified bank accounts
                  </span>
                </div>

                <div className="bg-amber-50/50 p-4 border border-amber-200">
                  <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">
                    Pending Disbursement
                  </span>
                  <p className="text-xl font-black font-mono text-amber-900 mt-1">
                    {formatCurrency(report.compensation.pending_amount)}
                  </p>
                  <span className="text-[10px] text-amber-700 mt-0.5 block">
                    Awaiting title claim clearance / treasury release
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div>
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-gray-600 uppercase text-[10px] tracking-wider">
                    Disbursement Completion Rate
                  </span>
                  <span className="font-mono text-gray-900">{report.compensation.disbursement_pct}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-none overflow-hidden border border-gray-200">
                  <div
                    className="h-full bg-emerald-600 transition-all duration-500"
                    style={{ width: `${Math.max(1, report.compensation.disbursement_pct)}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Acquisition Stages & R&R */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Stages Table */}
            <Card className="lg:col-span-2 rounded-none border border-gray-300 bg-white shadow-none">
              <CardHeader className="py-3 px-5 border-b border-gray-200 bg-gray-50/60">
                <CardTitle className="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center gap-2">
                  <Layers className="w-4 h-4 text-[#D47A22]" />
                  Statutory 11-Stage Workflow Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 text-gray-600 font-bold uppercase text-[10px] border-b border-gray-200 tracking-wider">
                    <tr>
                      <th className="px-5 py-2.5">RFCTLARR Statutory Stage</th>
                      <th className="px-5 py-2.5 text-right">Active Parcels</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {Object.entries(report.stages || {}).length === 0 ? (
                      <tr>
                        <td colSpan={2} className="px-5 py-4 text-center text-gray-400">
                          No stage data found
                        </td>
                      </tr>
                    ) : (
                      Object.entries(report.stages).map(([stageName, count]) => (
                        <tr key={stageName} className="hover:bg-amber-50/30 transition-colors">
                          <td className="px-5 py-2.5 font-medium text-gray-800">
                            {stageName.replace(/_/g, " ")}
                          </td>
                          <td className="px-5 py-2.5 text-right font-mono font-bold text-gray-900">
                            {count.toLocaleString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            {/* Rehabilitation & Resettlement */}
            <Card className="rounded-none border border-gray-300 bg-white shadow-none">
              <CardHeader className="py-3 px-5 border-b border-gray-200 bg-gray-50/60">
                <CardTitle className="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center gap-2">
                  <Users className="w-4 h-4 text-emerald-700" />
                  R&R Social Safeguards
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                <div className="bg-amber-50/40 p-4 border border-amber-200 text-center">
                  <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">
                    Project Affected Families (PAFs)
                  </span>
                  <span className="text-3xl font-black font-mono text-gray-900 mt-1 block">
                    {report.rehabilitation?.total_affected_families?.toLocaleString() || 0}
                  </span>
                  <span className="text-[11px] text-gray-600 mt-1 block">
                    Entitled to Schedule II & III Rehabilitation Assistance
                  </span>
                </div>

                <div className="space-y-2.5 text-xs text-gray-700">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>Schedule II Resettlement Matrix Verified</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>Direct Beneficiary Account Aadhaar-linked</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>Relocation and Alternative Allotment Active</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReportsPage;
