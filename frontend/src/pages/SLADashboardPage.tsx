import { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingDown,
  Loader2,
  Building2,
  FolderKanban,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getSLADashboard,
  getStageDelays,
  getDistrictDelays,
  getProjectDelays,
} from "@/api/sla";
import { useAuthStore } from "@/store/authStore";
import type {
  SLADashboardData,
  SLAStageDelay,
  SLADistrictDelay,
  SLAProjectDelay,
} from "@/types/api";

function SLAStatusCard({
  label,
  value,
  icon: Icon,
  color,
  subtitle,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
  subtitle?: string;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            {label}
          </p>
          <p className={cn("text-2xl font-bold mt-1", color)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
          )}
        </div>
        <div
          className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center",
            color.includes("emerald")
              ? "bg-emerald-50"
              : color.includes("amber")
              ? "bg-amber-50"
              : color.includes("red")
              ? "bg-red-50"
              : "bg-blue-50"
          )}
        >
          <Icon className={cn("w-5 h-5", color)} />
        </div>
      </div>
    </div>
  );
}

function BreachBar({
  rate,
  breached,
  total,
}: {
  rate: number;
  breached?: number;
  total?: number;
}) {
  const pct =
    total && total > 0 && typeof breached === "number"
      ? (breached / total) * 100
      : rate > 1.0
      ? rate
      : rate * 100;
  const clamped = Math.min(100, Math.max(0, pct));
  const rounded = Math.round(clamped);

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            rounded > 40
              ? "bg-red-500"
              : rounded > 15
              ? "bg-amber-500"
              : rounded > 0
              ? "bg-emerald-500"
              : "bg-gray-200"
          )}
          style={{ width: `${rounded}%` }}
        />
      </div>
      <span
        className={cn(
          "text-xs font-semibold tabular-nums w-10 text-right",
          rounded > 40
            ? "text-red-600"
            : rounded > 15
            ? "text-amber-600"
            : rounded > 0
            ? "text-emerald-600"
            : "text-gray-400"
        )}
      >
        {rounded}%
      </span>
    </div>
  );
}

type TabKey = "stages" | "districts" | "projects";

export function SLADashboardPage() {
  const { user } = useAuthStore();
  const [dashboard, setDashboard] = useState<SLADashboardData | null>(null);
  const [stageDelays, setStageDelays] = useState<SLAStageDelay[]>([]);
  const [districtDelays, setDistrictDelays] = useState<SLADistrictDelay[]>([]);
  const [projectDelays, setProjectDelays] = useState<SLAProjectDelay[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("stages");

  useEffect(() => {
    async function fetchAll() {
      setLoading(true);
      try {
        const queryParams = {
          state: user?.state_scope || undefined,
          district: user?.district_scope || undefined,
        };
        const [dash, stages, districts, projects] = await Promise.all([
          getSLADashboard(queryParams),
          getStageDelays(queryParams),
          getDistrictDelays(queryParams),
          getProjectDelays(queryParams),
        ]);
        setDashboard(dash);
        setStageDelays(stages);
        setDistrictDelays(districts);
        setProjectDelays(projects);
      } catch (err) {
        console.error("SLA fetch error:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, [user?.state_scope, user?.district_scope]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-8 h-8 text-[#D47A22] animate-spin" />
      </div>
    );
  }

  const d = dashboard || {
    total_parcels: 0,
    on_track: 0,
    at_risk: 0,
    breached: 0,
    overall_compliance_pct: 0,
    avg_days_pending: 0,
  };

  const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
    { key: "stages", label: "By Stage", icon: Layers },
    { key: "districts", label: user?.state_scope ? `Districts in ${user.state_scope}` : "By District", icon: Building2 },
    { key: "projects", label: "By Project", icon: FolderKanban },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Activity className="w-7 h-7 text-[#D47A22]" />
              SLA Monitoring Dashboard
            </h1>
            {user?.state_scope && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-bold bg-amber-50 text-[#A3540C] border border-amber-300">
                Jurisdiction: {user.state_scope} {user.district_scope ? `(${user.district_scope})` : ""}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {user?.state_scope
              ? `Real-time service level statutory compliance across acquisition stages in ${user.state_scope}`
              : "Real-time service level compliance across all acquisition stages nationwide"}
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SLAStatusCard
          label="On Track"
          value={d.on_track}
          icon={CheckCircle2}
          color="text-emerald-600"
          subtitle="Within SLA limits"
        />
        <SLAStatusCard
          label="At Risk"
          value={d.at_risk}
          icon={Clock}
          color="text-amber-600"
          subtitle="Approaching deadline"
        />
        <SLAStatusCard
          label="Breached"
          value={d.breached}
          icon={AlertTriangle}
          color="text-red-600"
          subtitle="Past SLA deadline"
        />
        <SLAStatusCard
          label="Compliance"
          value={`${Math.round(d.overall_compliance_pct)}%`}
          icon={TrendingDown}
          color="text-blue-600"
          subtitle={`Avg ${Math.round(d.avg_days_pending)} days pending`}
        />
      </div>

      {/* Compliance Gauge */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold text-gray-700">
            Overall SLA Compliance
          </p>
          <span
            className={cn(
              "text-xs font-bold px-2.5 py-1 rounded-full",
              d.overall_compliance_pct >= 80
                ? "bg-emerald-50 text-emerald-700"
                : d.overall_compliance_pct >= 50
                ? "bg-amber-50 text-amber-700"
                : "bg-red-50 text-red-700"
            )}
          >
            {Math.round(d.overall_compliance_pct)}%
          </span>
        </div>
        <div className="w-full h-4 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-700",
              d.overall_compliance_pct >= 80
                ? "bg-gradient-to-r from-emerald-400 to-emerald-500"
                : d.overall_compliance_pct >= 50
                ? "bg-gradient-to-r from-amber-400 to-amber-500"
                : "bg-gradient-to-r from-red-400 to-red-500"
            )}
            style={{ width: `${Math.min(100, d.overall_compliance_pct)}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-gray-400">
          <span>{d.on_track + d.at_risk + d.breached} total parcels</span>
          <span>
            {d.breached} breaches • {d.at_risk} at risk
          </span>
        </div>
      </div>

      {/* Breakdown Tabs */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex border-b border-gray-100">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  "flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors",
                  activeTab === tab.key
                    ? "border-[#D47A22] text-[#D47A22]"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="p-4">
          {activeTab === "stages" && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 uppercase tracking-wider border-b border-gray-100">
                    <th className="pb-3 pr-4">Stage</th>
                    <th className="pb-3 pr-4">SLA (days)</th>
                    <th className="pb-3 pr-4">Parcels</th>
                    <th className="pb-3 pr-4">Breached</th>
                    <th className="pb-3 pr-4 w-40">Breach Rate</th>
                    <th className="pb-3 pr-4">Avg Days</th>
                    <th className="pb-3">Max Days</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {stageDelays.map((s) => (
                    <tr key={s.stage} className="hover:bg-gray-50/50">
                      <td className="py-3 pr-4 font-medium text-gray-800">
                        {s.stage.replace(/_/g, " ")}
                      </td>
                      <td className="py-3 pr-4 text-gray-600">{s.sla_days}</td>
                      <td className="py-3 pr-4 text-gray-600">
                        {s.total_parcels}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={cn(
                            "font-semibold",
                            s.breached_count > 0
                              ? "text-red-600"
                              : "text-emerald-600"
                          )}
                        >
                          {s.breached_count}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <BreachBar
                          rate={s.breach_rate}
                          breached={s.breached_count}
                          total={s.total_parcels}
                        />
                      </td>
                      <td className="py-3 pr-4 text-gray-600">
                        {Math.round(s.avg_days_pending)}
                      </td>
                      <td className="py-3 text-gray-600">
                        {s.max_days_pending}
                      </td>
                    </tr>
                  ))}
                  {stageDelays.length === 0 && (
                    <tr>
                      <td
                        colSpan={7}
                        className="py-8 text-center text-gray-400"
                      >
                        No stage delay data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "districts" && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 uppercase tracking-wider border-b border-gray-100">
                    <th className="pb-3 pr-4">District</th>
                    <th className="pb-3 pr-4">State</th>
                    <th className="pb-3 pr-4">Parcels</th>
                    <th className="pb-3 pr-4">Breached</th>
                    <th className="pb-3 pr-4 w-40">Breach Rate</th>
                    <th className="pb-3">Avg Days</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {districtDelays.map((d, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/50">
                      <td className="py-3 pr-4 font-medium text-gray-800">
                        {d.district}
                      </td>
                      <td className="py-3 pr-4 text-gray-600">{d.state}</td>
                      <td className="py-3 pr-4 text-gray-600">
                        {d.total_parcels}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={cn(
                            "font-semibold",
                            d.breached_count > 0
                              ? "text-red-600"
                              : "text-emerald-600"
                          )}
                        >
                          {d.breached_count}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <BreachBar
                          rate={d.breach_rate}
                          breached={d.breached_count}
                          total={d.total_parcels}
                        />
                      </td>
                      <td className="py-3 text-gray-600">
                        {Math.round(d.avg_days_pending)}
                      </td>
                    </tr>
                  ))}
                  {districtDelays.length === 0 && (
                    <tr>
                      <td
                        colSpan={6}
                        className="py-8 text-center text-gray-400"
                      >
                        No district delay data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "projects" && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 uppercase tracking-wider border-b border-gray-100">
                    <th className="pb-3 pr-4">Project</th>
                    <th className="pb-3 pr-4">Parcels</th>
                    <th className="pb-3 pr-4">Breached</th>
                    <th className="pb-3 pr-4 w-40">Breach Rate</th>
                    <th className="pb-3 pr-4">Worst Stage</th>
                    <th className="pb-3">Avg Overdue</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {projectDelays.map((p) => (
                    <tr key={p.project_id} className="hover:bg-gray-50/50">
                      <td className="py-3 pr-4 font-medium text-gray-800">
                        {p.project_name}
                      </td>
                      <td className="py-3 pr-4 text-gray-600">
                        {p.total_parcels}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={cn(
                            "font-semibold",
                            p.breached_count > 0
                              ? "text-red-600"
                              : "text-emerald-600"
                          )}
                        >
                          {p.breached_count}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <BreachBar
                          rate={p.breach_rate}
                          breached={p.breached_count}
                          total={p.total_parcels}
                        />
                      </td>
                      <td className="py-3 pr-4 text-gray-600">
                        {p.worst_stage?.replace(/_/g, " ") || "—"}
                      </td>
                      <td className="py-3 text-gray-600">
                        {Math.round(p.avg_days_overdue)} days
                      </td>
                    </tr>
                  ))}
                  {projectDelays.length === 0 && (
                    <tr>
                      <td
                        colSpan={6}
                        className="py-8 text-center text-gray-400"
                      >
                        No project delay data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SLADashboardPage;
