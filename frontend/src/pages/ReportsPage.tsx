import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Download,
  Printer,
  Building2,
  Clock,
  Coins,
  Users,
  ShieldCheck,
  CheckCircle2,
  Layers,
  MapPin,
} from "lucide-react";
import { getProjects } from "@/api/projects";
import { fetchExecutiveSummary, getExecutiveSummaryHtmlUrl } from "@/api/reports";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { formatNumber, formatCurrency } from "@/lib/utils";

export function ReportsPage() {
  const [selectedProject, setSelectedProject] = useState<string>("");

  const { data: projectsData } = useQuery({
    queryKey: ["projects-dropdown"],
    queryFn: () => getProjects(),
  });

  const {
    data: report,
    isLoading,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["executive-summary", selectedProject],
    queryFn: () => fetchExecutiveSummary(selectedProject || undefined),
  });

  const handlePrint = () => {
    window.print();
  };

  const htmlDownloadUrl = getExecutiveSummaryHtmlUrl(selectedProject || undefined);

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header ───────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
              <BarChart3 className="w-6 h-6 text-brand-teal-blue" />
              Executive Analytics & Statutory Reports
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              RFCTLARR 2013 Compliant
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Generate and export high-level portfolio summaries, compensation audits, and project milestone reports.
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-gray-200 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-colors"
          >
            <Printer className="w-4 h-4 text-gray-500" />
            Print Report
          </button>
          <a
            href={htmlDownloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#D47A22] text-white text-sm font-medium rounded-xl hover:bg-[#B56315] shadow-sm transition-colors"
          >
            <Download className="w-4 h-4" />
            Download HTML
          </a>
        </div>
      </div>

      {/* ── Selector Bar ─────────────────────────── */}
      <div className="bg-white rounded-xl border border-gray-200/80 shadow-sm p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Building2 className="w-5 h-5 text-gray-400 flex-shrink-0" />
          <div className="w-full sm:w-80">
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-[#D47A22]/30 focus:border-[#D47A22] transition-all"
            >
              <option value="">National Portfolio (All Projects)</option>
              {(projectsData as any)?.items?.map((p: any) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground w-full sm:w-auto justify-end">
          <Clock className="w-3.5 h-3.5" />
          <span>Generated: {report?.generated_at || "Just now"}</span>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="ml-2 font-semibold text-[#D47A22] hover:underline disabled:opacity-50"
          >
            {isFetching ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* ── Report Document Preview ───────────────── */}
      {isLoading || !report ? (
        <div className="space-y-4">
          <div className="h-32 animate-shimmer rounded-xl" />
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 animate-shimmer rounded-xl" />
            ))}
          </div>
          <div className="h-64 animate-shimmer rounded-xl" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Executive Overview Banner */}
          <div className="bg-gradient-to-r from-[#D47A22] to-[#A2550D] text-white rounded-2xl p-6 sm:p-8 shadow-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-sm mb-3">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Official Executive Briefing
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
                  {report.project?.name || "National Portfolio Summary"}
                </h2>
                <div className="flex items-center gap-4 text-xs text-white/80 mt-2">
                  <span className="flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5" />
                    Status: <span className="font-semibold text-white uppercase">{report.project?.status || "ACTIVE"}</span>
                  </span>
                  {report.project?.districts && (
                    <span className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5" />
                      {report.project.districts.join(", ")}
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-right border border-white/15">
                <span className="text-xs text-white/70 block uppercase tracking-wider">Overall Acquisition</span>
                <span className="text-3xl font-black text-white">{report.metrics.progress_pct}%</span>
                <span className="text-[11px] text-white/80 block mt-0.5">
                  {report.metrics.land_acquired_ha} ha of {report.metrics.land_required_ha} ha
                </span>
              </div>
            </div>
          </div>

          {/* KPI Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-5">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Parcels</span>
              <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(report.metrics.total_parcels)}</p>
              <span className="text-xs text-gray-500 mt-1 block">
                {report.metrics.total_parcel_area_ha} ha surveyed area
              </span>
            </Card>

            <Card className="p-5">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Required Land</span>
              <p className="text-2xl font-bold text-gray-900 mt-1">{report.metrics.land_required_ha} <span className="text-sm font-normal text-gray-500">ha</span></p>
              <span className="text-xs text-emerald-600 font-semibold mt-1 block">
                {report.metrics.land_acquired_ha} ha completed
              </span>
            </Card>

            <Card className="p-5">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Pending Acquisition</span>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {Math.max(0, report.metrics.land_required_ha - report.metrics.land_acquired_ha).toFixed(1)} <span className="text-sm font-normal text-gray-500">ha</span>
              </p>
              <span className="text-xs text-amber-600 font-medium mt-1 block">In pipeline verification</span>
            </Card>

            <Card className="p-5">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Avg Portfolio Risk</span>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {report.metrics.avg_risk_score} <span className="text-sm font-normal text-gray-500">/ 100</span>
              </p>
              <span className={`text-xs font-semibold mt-1 block ${report.metrics.avg_risk_score > 60 ? "text-red-600" : "text-emerald-600"}`}>
                {report.metrics.avg_risk_score > 60 ? "Elevated compliance review" : "Standard operational risk"}
              </span>
            </Card>
          </div>

          {/* Compensation & Financial Disbursement */}
          <Card>
            <CardHeader className="border-b border-gray-100 pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Coins className="w-5 h-5 text-brand-copper" />
                Statutory Compensation & Direct Benefit Transfer (DBT) Audit
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-50/80 rounded-xl p-4 border border-gray-100">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Approved Award</span>
                  <p className="text-xl font-bold text-gray-900 mt-1">
                    {formatCurrency(report.compensation.approved_amount)}
                  </p>
                  <span className="text-[11px] text-gray-400 mt-0.5 block">Statutory compensation assessed</span>
                </div>

                <div className="bg-emerald-50/50 rounded-xl p-4 border border-emerald-100">
                  <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Disbursed (Paid)</span>
                  <p className="text-xl font-bold text-emerald-800 mt-1">
                    {formatCurrency(report.compensation.paid_amount)}
                  </p>
                  <span className="text-[11px] text-emerald-600 font-medium mt-0.5 block">
                    {report.compensation.disbursement_pct}% released to beneficiaries
                  </span>
                </div>

                <div className="bg-amber-50/50 rounded-xl p-4 border border-amber-100">
                  <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">Pending Release</span>
                  <p className="text-xl font-bold text-amber-800 mt-1">
                    {formatCurrency(report.compensation.pending_amount)}
                  </p>
                  <span className="text-[11px] text-amber-600 font-medium mt-0.5 block">Awaiting bank verification / claims</span>
                </div>
              </div>

              {/* Progress bar */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-gray-600">Disbursement Completion Rate</span>
                  <span className="text-gray-900">{report.compensation.disbursement_pct}%</span>
                </div>
                <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(2, report.compensation.disbursement_pct)}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Acquisition Stages & R&R */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Stages Table */}
            <Card className="lg:col-span-2">
              <CardHeader className="border-b border-gray-100 pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Layers className="w-5 h-5 text-brand-teal-blue" />
                  Statutory Acquisition Stage Distribution
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-2 px-0">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 text-gray-500 font-semibold border-b border-gray-100">
                    <tr>
                      <th className="px-5 py-2.5">RFCTLARR Stage</th>
                      <th className="px-5 py-2.5 text-right">Active Parcels</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {Object.entries(report.stages || {}).length === 0 ? (
                      <tr>
                        <td colSpan={2} className="px-5 py-4 text-center text-gray-400">
                          No stage data found
                        </td>
                      </tr>
                    ) : (
                      Object.entries(report.stages).map(([stageName, count]) => (
                        <tr key={stageName} className="hover:bg-gray-50/60">
                          <td className="px-5 py-2.5 font-medium text-gray-800">
                            {stageName.replace(/_/g, " ")}
                          </td>
                          <td className="px-5 py-2.5 text-right font-bold text-gray-900">
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
            <Card>
              <CardHeader className="border-b border-gray-100 pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Users className="w-5 h-5 text-brand-sea-green" />
                  R&R Social Safeguards
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="bg-brand-linen/70 rounded-xl p-4 border border-gray-200/60 text-center">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
                    Project Affected Families
                  </span>
                  <span className="text-3xl font-extrabold text-brand-teal-blue mt-1 block">
                    {report.rehabilitation.total_affected_families.toLocaleString()}
                  </span>
                  <span className="text-xs text-gray-500 mt-1 block">
                    Entitled to resettlement & rehabilitation benefits
                  </span>
                </div>

                <div className="space-y-2 text-xs text-gray-600">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>RFCTLARR Schedule II & III Entitlement matrix verified</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>Relocation site allotment mapping active</span>
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
