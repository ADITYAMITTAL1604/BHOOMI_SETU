import { useState, useMemo, useEffect } from "react";
import {
  Filter,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  Search,
  Lock,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";

export interface FilterState {
  state: string;
  district: string;
  projectId: string;
  projectType: string;
  stage: string;
  status: string;
  delayedOnly: boolean;
  compensationPending: boolean;
  approvalsPending: boolean;
  highRiskOnly: boolean;
  searchQuery: string;
}

export const INITIAL_FILTERS: FilterState = {
  state: "",
  district: "",
  projectId: "",
  projectType: "",
  stage: "",
  status: "",
  delayedOnly: false,
  compensationPending: false,
  approvalsPending: false,
  highRiskOnly: false,
  searchQuery: "",
};

const STATE_DISTRICTS_MAP: Record<string, string[]> = {
  Maharashtra: ["Pune", "Thane", "Raigad", "Palghar", "Nagpur"],
  Rajasthan: ["Jaipur", "Jodhpur", "Udaipur", "Kota"],
  "Uttar Pradesh": ["Moradabad", "Bahraich", "Sitapur", "Ghaziabad"],
  Delhi: ["South Delhi", "North West Delhi", "South West Delhi", "New Delhi", "East Delhi"],
  Punjab: ["Amritsar", "Ludhiana", "Patiala", "Jalandhar"],
  Gujarat: ["Ahmedabad", "Surat", "Vadodara"],
};

const PROJECT_TYPES = [
  "Highway",
  "Railway",
  "Metro",
  "Port",
  "Industrial",
  "Airport",
];

const WORKFLOW_STAGES = [
  { key: "IDENTIFICATION", label: "Land Identification" },
  { key: "SURVEY", label: "Survey / Parcel Mapping" },
  { key: "VERIFICATION", label: "Ownership Verification" },
  { key: "NOTIFICATION", label: "Statutory Notification (Sec 4)" },
  { key: "OBJECTION", label: "Objections & Hearings" },
  { key: "DECLARATION", label: "Declaration (Sec 19)" },
  { key: "AWARD", label: "Award Assessment" },
  { key: "COMPENSATION", label: "Compensation Disbursement" },
  { key: "REHABILITATION_RESETTLEMENT", label: "R&R Assistance" },
  { key: "POSSESSION", label: "Possession & Handover" },
  { key: "CLOSURE", label: "Mutation & Project Closure" },
];

interface AdvancedFiltersProps {
  filters: FilterState;
  onFilterChange: (newFilters: FilterState) => void;
  projects?: Array<{ project_id: string; name: string; type?: string; states?: string[] }>;
}

export function AdvancedFilters({
  filters,
  onFilterChange,
  projects = [],
}: AdvancedFiltersProps) {
  const { user } = useAuthStore();
  const [isExpanded, setIsExpanded] = useState(false);

  const isStateLocked = Boolean(user?.state_scope);
  const isDistrictLocked = Boolean(user?.district_scope);

  // Sync user scope on initial mount if not set
  useEffect(() => {
    if (user?.state_scope && filters.state !== user.state_scope) {
      onFilterChange({
        ...filters,
        state: user.state_scope,
        district: user.district_scope || filters.district,
      });
    }
  }, [user?.state_scope, user?.district_scope]); // eslint-disable-line react-hooks/exhaustive-deps

  const availableDistricts = useMemo(() => {
    const targetState = user?.state_scope || filters.state;
    if (!targetState) {
      return Object.values(STATE_DISTRICTS_MAP).flat();
    }
    return STATE_DISTRICTS_MAP[targetState] || [];
  }, [filters.state, user?.state_scope]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.state && !isStateLocked) count++;
    if (filters.district && !isDistrictLocked) count++;
    if (filters.projectId) count++;
    if (filters.projectType) count++;
    if (filters.stage) count++;
    if (filters.status) count++;
    if (filters.delayedOnly) count++;
    if (filters.compensationPending) count++;
    if (filters.approvalsPending) count++;
    if (filters.highRiskOnly) count++;
    if (filters.searchQuery) count++;
    return count;
  }, [filters, isStateLocked, isDistrictLocked]);

  const handleFieldChange = (field: keyof FilterState, value: any) => {
    if (field === "state" && isStateLocked) return;
    if (field === "district" && isDistrictLocked) return;

    const updated = { ...filters, [field]: value };
    // If state changes and district no longer matches, clear district
    if (field === "state" && value && filters.district) {
      const allowed = STATE_DISTRICTS_MAP[value] || [];
      if (!allowed.includes(filters.district)) {
        updated.district = "";
      }
    }
    onFilterChange(updated);
  };

  const handleReset = () => {
    onFilterChange({
      ...INITIAL_FILTERS,
      state: user?.state_scope || "",
      district: user?.district_scope || "",
    });
  };

  return (
    <div className="bg-white border border-gray-300 rounded-none shadow-none">
      {/* ── Filter Bar Header ────────────────────────────────────────── */}
      <div className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-gray-200">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-2 font-bold text-sm text-gray-900 uppercase tracking-wide">
            <Filter className="w-4 h-4 text-[#D47A22]" />
            Report Query & Statutory Filters
          </div>
          {isStateLocked && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-bold bg-amber-50 text-[#A3540C] border border-amber-300">
              <Lock className="w-3 h-3" />
              Jurisdiction: {user?.state_scope} {user?.district_scope ? `(${user.district_scope})` : ""}
            </span>
          )}
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              {activeFilterCount} Active Filters
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Quick Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search survey / village..."
              value={filters.searchQuery}
              onChange={(e) => handleFieldChange("searchQuery", e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs border border-gray-300 bg-gray-50 focus:bg-white focus:outline-none focus:border-[#D47A22] w-48 sm:w-64"
            />
          </div>

          {activeFilterCount > 0 && (
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-gray-600 hover:text-red-700 bg-gray-100 hover:bg-red-50 border border-gray-300 hover:border-red-200 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Reset
            </button>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-gray-700 bg-gray-100 hover:bg-gray-200 border border-gray-300 transition-colors"
          >
            {isExpanded ? (
              <>
                <span>Less Filters</span>
                <ChevronUp className="w-3.5 h-3.5" />
              </>
            ) : (
              <>
                <span>Advanced Filters</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Primary Filters (Always Visible) ─────────────────────────── */}
      <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-gray-50/50">
        {/* Project Selector */}
        <div>
          <label className="block text-[10px] font-bold text-gray-600 uppercase mb-1">
            Project Corridor
          </label>
          <select
            value={filters.projectId}
            onChange={(e) => handleFieldChange("projectId", e.target.value)}
            className="w-full text-xs py-1.5 px-2 border border-gray-300 bg-white focus:outline-none focus:border-[#D47A22]"
          >
            <option value="">All Projects ({projects.length})</option>
            {projects.map((p) => (
              <option key={p.project_id} value={p.project_id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* State Filter */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-[10px] font-bold text-gray-600 uppercase">
              State Jurisdiction
            </label>
            {isStateLocked && (
              <span className="text-[9px] font-bold text-[#A3540C] flex items-center gap-0.5">
                <Lock className="w-2.5 h-2.5" /> Locked
              </span>
            )}
          </div>
          <select
            value={isStateLocked ? (user?.state_scope || "") : filters.state}
            onChange={(e) => handleFieldChange("state", e.target.value)}
            disabled={isStateLocked}
            className={`w-full text-xs py-1.5 px-2 border border-gray-300 focus:outline-none focus:border-[#D47A22] ${
              isStateLocked ? "bg-gray-100 text-gray-600 font-bold cursor-not-allowed" : "bg-white"
            }`}
          >
            {!isStateLocked && <option value="">All States (National)</option>}
            {isStateLocked ? (
              <option value={user?.state_scope || ""}>{user?.state_scope}</option>
            ) : (
              Object.keys(STATE_DISTRICTS_MAP).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))
            )}
          </select>
        </div>

        {/* District Filter */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-[10px] font-bold text-gray-600 uppercase">
              District Unit
            </label>
            {isDistrictLocked && (
              <span className="text-[9px] font-bold text-[#A3540C] flex items-center gap-0.5">
                <Lock className="w-2.5 h-2.5" /> Locked
              </span>
            )}
          </div>
          <select
            value={isDistrictLocked ? (user?.district_scope || "") : filters.district}
            onChange={(e) => handleFieldChange("district", e.target.value)}
            disabled={isDistrictLocked}
            className={`w-full text-xs py-1.5 px-2 border border-gray-300 focus:outline-none focus:border-[#D47A22] ${
              isDistrictLocked ? "bg-gray-100 text-gray-600 font-bold cursor-not-allowed" : "bg-white"
            }`}
          >
            {!isDistrictLocked && <option value="">All Districts ({availableDistricts.length})</option>}
            {isDistrictLocked ? (
              <option value={user?.district_scope || ""}>{user?.district_scope}</option>
            ) : (
              availableDistricts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Stage Filter */}
        <div>
          <label className="block text-[10px] font-bold text-gray-600 uppercase mb-1">
            Current Stage
          </label>
          <select
            value={filters.stage}
            onChange={(e) => handleFieldChange("stage", e.target.value)}
            className="w-full text-xs py-1.5 px-2 border border-gray-300 bg-white focus:outline-none focus:border-[#D47A22]"
          >
            <option value="">All Acquisition Stages</option>
            {WORKFLOW_STAGES.map((st) => (
              <option key={st.key} value={st.key}>
                {st.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ── Collapsible Advanced Filter Row ──────────────────────────── */}
      {isExpanded && (
        <div className="p-4 border-t border-gray-200 bg-white space-y-4 animate-fade-in">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Project Type */}
            <div>
              <label className="block text-[10px] font-bold text-gray-600 uppercase mb-1">
                Infrastructure Type
              </label>
              <select
                value={filters.projectType}
                onChange={(e) => handleFieldChange("projectType", e.target.value)}
                className="w-full text-xs py-1.5 px-2 border border-gray-300 bg-white focus:outline-none focus:border-[#D47A22]"
              >
                <option value="">All Types (Highway, Metro, etc.)</option>
                {PROJECT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            {/* Parcel Status */}
            <div>
              <label className="block text-[10px] font-bold text-gray-600 uppercase mb-1">
                Parcel Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFieldChange("status", e.target.value)}
                className="w-full text-xs py-1.5 px-2 border border-gray-300 bg-white focus:outline-none focus:border-[#D47A22]"
              >
                <option value="">All Statuses</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed (Possession)</option>
                <option value="BLOCKED">Blocked</option>
                <option value="DISPUTED">Disputed</option>
              </select>
            </div>

            {/* Statutory Stage Status */}
            <div>
              <label className="block text-[10px] font-bold text-gray-600 uppercase mb-1">
                Workflow Health
              </label>
              <div className="text-xs text-gray-500 py-2">
                Filter by SLA breaches or pending statutory milestones
              </div>
            </div>
          </div>

          {/* Preset Flag Checkboxes */}
          <div>
            <span className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
              Statutory Incident & Exception Filters
            </span>
            <div className="flex flex-wrap gap-4">
              <label className="inline-flex items-center gap-2 text-xs font-semibold text-gray-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.delayedOnly}
                  onChange={(e) => handleFieldChange("delayedOnly", e.target.checked)}
                  className="rounded-none text-[#D47A22] focus:ring-0 border-gray-300"
                />
                <span className="text-red-700 bg-red-50 px-1.5 py-0.5 border border-red-200">
                  SLA Breached / Delayed
                </span>
              </label>

              <label className="inline-flex items-center gap-2 text-xs font-semibold text-gray-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.compensationPending}
                  onChange={(e) =>
                    handleFieldChange("compensationPending", e.target.checked)
                  }
                  className="rounded-none text-[#D47A22] focus:ring-0 border-gray-300"
                />
                <span className="text-amber-800 bg-amber-50 px-1.5 py-0.5 border border-amber-200">
                  Compensation Pending Release
                </span>
              </label>

              <label className="inline-flex items-center gap-2 text-xs font-semibold text-gray-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.approvalsPending}
                  onChange={(e) =>
                    handleFieldChange("approvalsPending", e.target.checked)
                  }
                  className="rounded-none text-[#D47A22] focus:ring-0 border-gray-300"
                />
                <span className="text-blue-800 bg-blue-50 px-1.5 py-0.5 border border-blue-200">
                  Approvals Pending
                </span>
              </label>

              <label className="inline-flex items-center gap-2 text-xs font-semibold text-gray-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.highRiskOnly}
                  onChange={(e) => handleFieldChange("highRiskOnly", e.target.checked)}
                  className="rounded-none text-[#D47A22] focus:ring-0 border-gray-300"
                />
                <span className="text-purple-800 bg-purple-50 px-1.5 py-0.5 border border-purple-200 flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3" />
                  High Risk Parcels (&gt;70%)
                </span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
