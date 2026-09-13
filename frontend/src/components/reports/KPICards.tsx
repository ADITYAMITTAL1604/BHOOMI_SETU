import {
  Building2,
  Layers,
  Coins,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { formatNumber, formatCurrency } from "@/lib/utils";
import type { ReportKPIs } from "@/api/reports";

interface KPICardsProps {
  kpis?: ReportKPIs;
  isLoading?: boolean;
}

export function KPICards({ kpis, isLoading }: KPICardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-gray-100 rounded-none border border-gray-200" />
        ))}
      </div>
    );
  }

  if (!kpis) return null;

  const disbursementPct = kpis.compensation?.disbursement_pct ?? 0;

  return (
    <div className="space-y-4">
      {/* ── Top-line Metric Cards ────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Projects */}
        <Card className="rounded-none border border-gray-300 bg-white shadow-none hover:border-[#D47A22] transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
                Total Projects
              </span>
              <div className="w-8 h-8 rounded-none bg-amber-50 border border-amber-200 flex items-center justify-center text-[#D47A22]">
                <Building2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black font-mono text-gray-900">
                {kpis.total_projects}
              </span>
              <span className="text-xs text-gray-500 font-medium">Corridors</span>
            </div>
            <p className="text-[11px] text-gray-500 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-600" />
              Active multi-state infrastructure
            </p>
          </CardContent>
        </Card>

        {/* Parcels & Completion Rate */}
        <Card className="rounded-none border border-gray-300 bg-white shadow-none hover:border-[#D47A22] transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
                Total Parcels
              </span>
              <div className="w-8 h-8 rounded-none bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black font-mono text-gray-900">
                {formatNumber(kpis.total_parcels)}
              </span>
              <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 border border-emerald-200">
                {kpis.completion_pct}% Done
              </span>
            </div>
            <div className="w-full bg-gray-100 h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-emerald-600 h-full transition-all duration-500"
                style={{ width: `${Math.min(100, kpis.completion_pct)}%` }}
              />
            </div>
            <p className="text-[11px] text-gray-500 mt-1">
              {formatNumber(kpis.completed_parcels)} of {formatNumber(kpis.total_parcels)} possession granted
            </p>
          </CardContent>
        </Card>

        {/* Land Acquisition Area */}
        <Card className="rounded-none border border-gray-300 bg-white shadow-none hover:border-[#D47A22] transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
                Acquisition Footprint
              </span>
              <div className="w-8 h-8 rounded-none bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black font-mono text-gray-900">
                {formatNumber(kpis.total_area_ha)}
              </span>
              <span className="text-xs text-gray-500 font-medium">Hectares</span>
            </div>
            <p className="text-[11px] text-gray-500 mt-1 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Total surveyed parcel coverage
            </p>
          </CardContent>
        </Card>

        {/* Compensation Disbursed */}
        <Card className="rounded-none border border-gray-300 bg-white shadow-none hover:border-[#D47A22] transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
                Compensation Disbursed
              </span>
              <div className="w-8 h-8 rounded-none bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
                <Coins className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black font-mono text-gray-900">
                {formatCurrency(kpis.compensation?.paid || 0)}
              </span>
              <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 border border-amber-200">
                {disbursementPct}%
              </span>
            </div>
            <div className="w-full bg-gray-100 h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-[#D47A22] h-full transition-all duration-500"
                style={{ width: `${Math.min(100, disbursementPct)}%` }}
              />
            </div>
            <p className="text-[11px] text-gray-500 mt-1">
              Pending release: {formatCurrency(kpis.compensation?.pending || 0)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* ── Status Health Sub-Row ────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 border border-gray-200 bg-gray-50 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-gray-500 uppercase">In Progress</span>
            <p className="text-lg font-black font-mono text-gray-900">
              {formatNumber(kpis.in_progress_parcels)}
            </p>
          </div>
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
        </div>

        <div className="p-3 border border-gray-200 bg-gray-50 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-gray-500 uppercase">Completed</span>
            <p className="text-lg font-black font-mono text-emerald-700">
              {formatNumber(kpis.completed_parcels)}
            </p>
          </div>
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
        </div>

        <div className="p-3 border border-gray-200 bg-amber-50/50 border-amber-200 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-amber-700 uppercase">Disputed</span>
            <p className="text-lg font-black font-mono text-amber-900">
              {formatNumber(kpis.disputed_parcels)}
            </p>
          </div>
          <AlertTriangle className="w-4 h-4 text-amber-600" />
        </div>

        <div className="p-3 border border-red-200 bg-red-50/50 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-red-700 uppercase">Blocked</span>
            <p className="text-lg font-black font-mono text-red-900">
              {formatNumber(kpis.blocked_parcels)}
            </p>
          </div>
          <div className="w-2.5 h-2.5 rounded-full bg-red-600 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
