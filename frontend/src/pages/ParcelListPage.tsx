import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Layers,
  Search,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  MapPin,
  CheckCircle2,
  Clock,
  ExternalLink,
} from "lucide-react";
import { RiskTooltip } from "@/components/RiskTooltip";
import { getParcels } from "@/api/parcels";
import { getProjects } from "@/api/projects";
import { cn } from "@/lib/utils";
import type { Parcel } from "@/types/api";

const STAGES_LIST = [
  { value: "", label: "All Stages" },
  { value: "IDENTIFICATION", label: "Land Identification" },
  { value: "SURVEY", label: "Survey & Demarcation" },
  { value: "VERIFICATION", label: "Ownership Verification" },
  { value: "NOTIFICATION", label: "Notification (Sec 11)" },
  { value: "OBJECTION", label: "Objections & Hearings (Sec 15)" },
  { value: "AWARD", label: "Compensation Assessment (Sec 23)" },
  { value: "COMPENSATION", label: "Compensation Disbursement" },
  { value: "REHABILITATION_RESETTLEMENT", label: "Rehabilitation & Resettlement (R&R)" },
  { value: "POSSESSION", label: "Possession Handover" },
  { value: "CLOSURE", label: "Statutory Closure" },
];

const STATUS_LIST = [
  { value: "", label: "All Statuses" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "COMPLETED", label: "Possession Completed" },
  { value: "BLOCKED", label: "Blocked / Injunction" },
  { value: "NOT_STARTED", label: "Not Started" },
];

export function ParcelListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [selectedProject, setSelectedProject] = useState("");
  const [selectedStage, setSelectedStage] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const { data: projectsData } = useQuery({
    queryKey: ["projects-dropdown"],
    queryFn: () => getProjects({ limit: 100 }),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["parcels-list", selectedProject, selectedStage, selectedStatus, search, page],
    queryFn: () =>
      getParcels({
        project_id: selectedProject || undefined,
        stage: selectedStage || undefined,
        status: selectedStatus || undefined,
        search: search || undefined,
        page,
        limit: pageSize,
      }),
  });

  const parcels: Parcel[] = (data as any)?.items || (data as any)?.data || [];
  const total = (data as any)?.total || 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const projectsList = (projectsData as any)?.data || (projectsData as any)?.items || [];

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header ───────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
              <Layers className="w-6 h-6 text-brand-teal-blue" />
              Land Parcel Repository
            </h1>
            <span className="px-2.5 py-0.5 rounded-none text-xs font-semibold bg-brand-teal-blue/10 text-brand-teal-blue border border-brand-teal-blue/20">
              {total.toLocaleString()} Total Records
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Official cadastral registry with survey boundaries, ownership records, and statutory milestones.
          </p>
        </div>
      </div>

      {/* ── Filter Bar ────────────────────────────── */}
      <div className="bg-white rounded-none border border-gray-300 shadow-sm p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative md:col-span-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search survey #, owner..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-300 rounded-none text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-brand-teal-blue focus:border-brand-teal-blue transition-all"
            />
          </div>

          {/* Project Filter */}
          <div>
            <select
              value={selectedProject}
              onChange={(e) => {
                setSelectedProject(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-none text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-brand-teal-blue focus:border-brand-teal-blue transition-all"
            >
              <option value="">All Projects</option>
              {projectsList.map((p: any) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Stage Filter */}
          <div>
            <select
              value={selectedStage}
              onChange={(e) => {
                setSelectedStage(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-none text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-brand-teal-blue focus:border-brand-teal-blue transition-all"
            >
              {STAGES_LIST.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-none text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-brand-teal-blue focus:border-brand-teal-blue transition-all"
            >
              {STATUS_LIST.map((st) => (
                <option key={st.value} value={st.value}>
                  {st.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Clear Filters Button if any active */}
        {(search || selectedProject || selectedStage || selectedStatus) && (
          <div className="flex items-center justify-between pt-2 border-t border-gray-100 text-xs text-gray-500">
            <span>Filtered results active</span>
            <button
              onClick={() => {
                setSearch("");
                setSelectedProject("");
                setSelectedStage("");
                setSelectedStatus("");
                setPage(1);
              }}
              className="text-brand-teal-blue font-semibold hover:underline"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* ── Table ─────────────────────────────────── */}
      <div className="bg-white rounded-none border border-gray-300 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50/80 text-gray-500 font-semibold border-b border-gray-200 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Survey # & Location</th>
                <th className="px-4 py-3.5">Owner / Landholder</th>
                <th className="px-4 py-3.5">Area</th>
                <th className="px-4 py-3.5">Pipeline Stage</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">Risk Profile</th>
                <th className="px-4 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-5 py-4"><div className="h-4 bg-gray-200 rounded-none w-32 mb-1" /><div className="h-3 bg-gray-100 rounded-none w-24" /></td>
                    <td className="px-4 py-4"><div className="h-4 bg-gray-200 rounded-none w-28" /></td>
                    <td className="px-4 py-4"><div className="h-4 bg-gray-200 rounded-none w-16" /></td>
                    <td className="px-4 py-4"><div className="h-6 bg-gray-200 rounded-none w-28" /></td>
                    <td className="px-4 py-4"><div className="h-6 bg-gray-200 rounded-none w-20" /></td>
                    <td className="px-4 py-4"><div className="h-4 bg-gray-200 rounded-none w-20" /></td>
                    <td className="px-4 py-4 text-right"><div className="h-4 bg-gray-200 rounded-none w-16 ml-auto" /></td>
                  </tr>
                ))
              ) : parcels.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    <Layers className="w-8 h-8 mx-auto text-gray-300 mb-2" />
                    <p className="font-semibold text-gray-700">No parcels found</p>
                    <p className="text-xs text-gray-400 mt-1">Try modifying your search query or filters.</p>
                  </td>
                </tr>
              ) : (
                parcels.map((parcel) => {
                  const risk = Number(parcel.risk_score) || 0;
                  const isHighRisk = risk >= 70;
                  const isMedRisk = risk >= 35 && risk < 70;

                  return (
                    <tr
                      key={parcel.parcel_id}
                      onClick={() => navigate(`/parcels/${parcel.parcel_id}`)}
                      className="hover:bg-gray-50/80 transition-colors cursor-pointer group"
                    >
                      {/* Survey # & Location */}
                      <td className="px-5 py-3.5">
                        <div className="font-bold text-gray-900 group-hover:text-brand-teal-blue transition-colors">
                          {parcel.survey_number}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-0.5">
                          <MapPin className="w-3 h-3 text-gray-400 flex-shrink-0" />
                          <span>{parcel.village}, {parcel.district}</span>
                        </div>
                      </td>

                      {/* Owner */}
                      <td className="px-4 py-3.5">
                        <div className="font-medium text-gray-900">{parcel.owner_name || "Unregistered"}</div>
                        <div className="text-[11px] text-gray-400 font-mono">{parcel.owner_reference || "—"}</div>
                      </td>

                      {/* Area */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span className="font-semibold text-gray-800">{parcel.area_ha}</span>
                        <span className="text-xs text-gray-500 ml-1">ha</span>
                      </td>

                      {/* Stage */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-none text-xs font-semibold bg-gray-100 text-gray-800 border border-gray-200">
                          {parcel.current_stage?.replace(/_/g, " ")}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-none text-xs font-semibold",
                            parcel.status === "COMPLETED"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : parcel.status === "BLOCKED"
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : "bg-blue-50 text-blue-700 border border-blue-200"
                          )}
                        >
                          {parcel.status === "COMPLETED" && <CheckCircle2 className="w-3 h-3" />}
                          {parcel.status === "BLOCKED" && <AlertTriangle className="w-3 h-3" />}
                          {parcel.status === "IN_PROGRESS" && <Clock className="w-3 h-3" />}
                          {parcel.status === "COMPLETED" ? "POSSESSION COMPLETED" : parcel.status?.replace(/_/g, " ")}
                        </span>
                      </td>

                      {/* Risk */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              "font-bold text-xs",
                              isHighRisk ? "text-red-600" : isMedRisk ? "text-amber-600" : "text-emerald-600"
                            )}
                          >
                            {risk.toFixed(1)}%
                          </span>
                          <span
                            className={cn(
                              "text-[10px] font-bold px-1.5 py-0.5 rounded-none",
                              isHighRisk
                                ? "bg-red-100 text-red-800"
                                : isMedRisk
                                ? "bg-amber-100 text-amber-800"
                                : "bg-emerald-100 text-emerald-800"
                            )}
                          >
                            {isHighRisk ? "HIGH" : isMedRisk ? "MED" : "LOW"}
                          </span>
                          <RiskTooltip score={risk} type="PARCEL" />
                        </div>
                      </td>

                      {/* Action */}
                      <td className="px-4 py-3.5 text-right whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-brand-teal-blue group-hover:underline">
                          Inspect <ExternalLink className="w-3 h-3" />
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* ── Pagination ────────────────────────────── */}
        <div className="px-5 py-3.5 bg-gray-50/60 border-t border-gray-200 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Showing <span className="font-semibold text-gray-800">{parcels.length}</span> of{" "}
            <span className="font-semibold text-gray-800">{total}</span> parcels
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-none border border-gray-300 bg-white text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Previous
            </button>
            <span className="text-xs font-medium text-gray-600 px-2">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-none border border-gray-300 bg-white text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ParcelListPage;
