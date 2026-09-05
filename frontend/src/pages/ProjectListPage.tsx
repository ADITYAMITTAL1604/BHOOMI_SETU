import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  FolderKanban,
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  RotateCcw,
  ChevronDown,
  FileSpreadsheet,
  FileText,
  Printer,
  Check,
  Loader2,
} from "lucide-react";
import { listProjects, getProjectDistricts, downloadProjectsCsv } from "@/api/projects";
import { getExecutiveSummaryHtmlUrl } from "@/api/reports";
import { RiskTooltip } from "@/components/RiskTooltip";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn, formatDate } from "@/lib/utils";

export function ProjectListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [selectedState, setSelectedState] = useState<string>("All States");
  const [selectedDistrict, setSelectedDistrict] = useState<string>("All Districts");
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<string | undefined>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);
  const limit = 10;

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Dynamically fetch districts across active projects
  const { data: availableDistricts = [] } = useQuery({
    queryKey: ["project-districts", selectedState],
    queryFn: () => getProjectDistricts(selectedState),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["projects", { search, selectedState, selectedDistrict, page, sortBy, sortOrder }],
    queryFn: () =>
      listProjects({
        search: search || undefined,
        state: selectedState === "All States" ? undefined : selectedState,
        district: selectedDistrict === "All Districts" ? undefined : selectedDistrict,
        page,
        limit,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  const handleExportCsv = async () => {
    try {
      setIsExporting(true);
      setShowExportMenu(false);
      await downloadProjectsCsv({
        search: search || undefined,
        state: selectedState,
        district: selectedDistrict,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setExportSuccess(`Projects exported successfully (${data?.total || 15} projects).`);
      setTimeout(() => setExportSuccess(null), 4000);
    } catch (err) {
      console.error("Failed to export projects CSV", err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportHtml = () => {
    setShowExportMenu(false);
    window.open(getExecutiveSummaryHtmlUrl(), "_blank");
  };

  const handlePrint = () => {
    setShowExportMenu(false);
    window.print();
  };

  const handleSort = (key: string) => {
    if (sortBy === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(key);
      setSortOrder("asc");
    }
    setPage(1);
  };

  const handleResetFilters = () => {
    setSearch("");
    setSelectedState("All States");
    setSelectedDistrict("All Districts");
    setSortBy("created_at");
    setSortOrder("desc");
    setPage(1);
  };

  const isFiltered =
    search !== "" ||
    selectedState !== "All States" ||
    selectedDistrict !== "All Districts" ||
    (sortBy && sortBy !== "created_at");

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <FolderKanban className="w-6 h-6 text-[#D47A22]" />
            Project Inventory
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage and monitor land acquisition projects across all active districts and corridors.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {exportSuccess && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs font-semibold rounded-none">
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              {exportSuccess}
            </div>
          )}

          <div className="relative z-30" ref={exportMenuRef}>
            <div className="inline-flex items-stretch border border-gray-300 shadow-sm bg-white">
              <button
                onClick={handleExportCsv}
                disabled={isExporting}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white text-sm font-semibold text-gray-800 hover:bg-amber-50/60 hover:text-[#D47A22] transition-colors rounded-none disabled:opacity-50"
                title="Download Projects Inventory CSV"
              >
                {isExporting ? (
                  <Loader2 className="w-4 h-4 text-[#D47A22] animate-spin" />
                ) : (
                  <Download className="w-4 h-4 text-[#D47A22]" />
                )}
                <span>{isExporting ? "Generating Report..." : "Export Report"}</span>
              </button>
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="px-2.5 py-2 border-l border-gray-300 bg-gray-50 text-gray-600 hover:bg-gray-100 transition-colors rounded-none"
                aria-label="More export options"
                title="Select export format"
              >
                <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", showExportMenu && "rotate-180")} />
              </button>
            </div>

            {/* Dropdown Menu */}
            {showExportMenu && (
              <div className="absolute right-0 mt-1 w-64 bg-white border border-gray-300 shadow-2xl z-50 py-1 rounded-none text-left">
                <div className="px-3 py-1.5 border-b border-gray-100 text-[11px] font-bold uppercase tracking-wider text-gray-500 bg-gray-50/80">
                  Export Formats
                </div>
                <button
                  onClick={handleExportCsv}
                  className="w-full flex items-start gap-2.5 px-3 py-2 text-xs text-gray-800 hover:bg-amber-50/60 hover:text-[#D47A22] transition-colors text-left"
                >
                  <FileSpreadsheet className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">Spreadsheet Data (.csv)</p>
                    <p className="text-[11px] text-gray-500">Filtered project inventory with land, progress & risk</p>
                  </div>
                </button>
                <button
                  onClick={handleExportHtml}
                  className="w-full flex items-start gap-2.5 px-3 py-2 text-xs text-gray-800 hover:bg-amber-50/60 hover:text-[#D47A22] transition-colors text-left"
                >
                  <FileText className="w-4 h-4 text-[#D47A22] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">Executive Summary (.html)</p>
                    <p className="text-[11px] text-gray-500">Official RFCTLARR statutory portfolio briefing</p>
                  </div>
                </button>
                <button
                  onClick={handlePrint}
                  className="w-full flex items-start gap-2.5 px-3 py-2 text-xs text-gray-800 hover:bg-amber-50/60 hover:text-[#D47A22] transition-colors text-left border-t border-gray-100"
                >
                  <Printer className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">Print Inventory</p>
                    <p className="text-[11px] text-gray-500">Official printable registry sheet</p>
                  </div>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <Card className="p-3.5 rounded-none border border-gray-300 bg-white shadow-none">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="flex-1 min-w-[240px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by project name or type..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 rounded-none border border-gray-300 bg-gray-50/60 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-[#D47A22] focus:border-[#D47A22]"
            />
          </div>

          {/* State Filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">State:</label>
            <select
              value={selectedState}
              onChange={(e) => {
                setSelectedState(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-none border border-gray-300 bg-white text-sm text-gray-700 font-medium focus:outline-none focus:ring-1 focus:ring-[#D47A22] focus:border-[#D47A22]"
            >
              <option value="All States">All States</option>
              <option value="Uttar Pradesh">Uttar Pradesh</option>
              <option value="Maharashtra">Maharashtra</option>
              <option value="Gujarat">Gujarat</option>
              <option value="Haryana">Haryana</option>
              <option value="Karnataka">Karnataka</option>
              <option value="Kerala">Kerala</option>
            </select>
          </div>

          {/* District Dropdown Filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">District:</label>
            <select
              value={selectedDistrict}
              onChange={(e) => {
                setSelectedDistrict(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 rounded-none border border-gray-300 bg-white text-sm text-gray-700 font-medium focus:outline-none focus:ring-1 focus:ring-[#D47A22] focus:border-[#D47A22]"
            >
              <option value="All Districts">
                All Districts {availableDistricts.length > 0 ? `(${availableDistricts.length})` : ""}
              </option>
              {availableDistricts.map((dist) => (
                <option key={dist} value={dist}>
                  {dist}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By Quick Dropdown */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Sort:</label>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [col, order] = e.target.value.split("-");
                setSortBy(col);
                setSortOrder(order as "asc" | "desc");
                setPage(1);
              }}
              className="px-3 py-2 rounded-none border border-gray-300 bg-white text-sm text-gray-700 font-medium focus:outline-none focus:ring-1 focus:ring-[#D47A22] focus:border-[#D47A22]"
            >
              <option value="created_at-desc">Default (Newest)</option>
              <option value="name-asc">Project Name (A-Z)</option>
              <option value="progress_pct-asc">Progress (Low to High)</option>
              <option value="progress_pct-desc">Progress (High to Low)</option>
              <option value="risk_score-desc">Risk Level (High to Low)</option>
              <option value="risk_score-asc">Risk Level (Low to High)</option>
              <option value="land_required_ha-desc">Land Area (Largest)</option>
              <option value="target_date-asc">Target Date (Nearest)</option>
            </select>
          </div>

          {/* Reset Filters */}
          {isFiltered && (
            <button
              onClick={handleResetFilters}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-none border border-gray-300 bg-gray-50 text-xs font-semibold text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-gray-500" />
              Reset Filters
            </button>
          )}
        </div>
      </Card>

      {/* Table */}
      <Card className="rounded-none border border-gray-300 bg-white shadow-none overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-300 bg-gray-100/80">
                {[
                  { key: "name", label: "Project Name" },
                  { key: "districts", label: "State / District" },
                  { key: "land_required_ha", label: "Land Required (HA)" },
                  { key: "progress_pct", label: "Acquisition Progress" },
                  { key: "risk_score", label: "Risk Level" },
                  { key: "target_date", label: "Target Date" },
                ].map((col) => (
                  <th
                    key={col.key}
                    className="text-left text-xs font-bold text-gray-700 uppercase tracking-wider px-4 py-3 cursor-pointer hover:bg-gray-200/70 select-none border-r border-gray-200 last:border-r-0"
                    onClick={() => handleSort(col.key)}
                  >
                    <div className="flex items-center justify-between gap-1.5">
                      <span>{col.label}</span>
                      <span className="text-[11px]">
                        {sortBy === col.key ? (
                          <span className="text-[#D47A22] font-black">
                            {sortOrder === "asc" ? "▲" : "▼"}
                          </span>
                        ) : (
                          <ArrowUpDown className="w-3 h-3 text-gray-400" />
                        )}
                      </span>
                    </div>
                  </th>
                ))}
                <th className="px-3 py-3 w-10 text-center" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-200">
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-4">
                        <div className="h-4 bg-gray-200 animate-pulse rounded-none w-full" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : data && data.data.length > 0 ? (
                data.data.map((project) => {
                  const progPct =
                    typeof project.progress_pct === "number"
                      ? project.progress_pct
                      : project.land_required_ha > 0
                      ? Number(((project.land_acquired_ha / project.land_required_ha) * 100).toFixed(1))
                      : 0;

                  const riskScore =
                    typeof project.risk_score === "number" ? project.risk_score : 50;

                  const riskLevel =
                    project.risk_level ||
                    (riskScore >= 70 ? "HIGH" : riskScore >= 40 ? "MEDIUM" : "LOW");

                  return (
                    <tr
                      key={project.project_id}
                      className="hover:bg-amber-50/40 transition-colors cursor-pointer group"
                      onClick={() => navigate(`/projects/${project.project_id}`)}
                    >
                      {/* Name */}
                      <td className="px-4 py-3.5 border-r border-gray-100">
                        <div>
                          <p className="text-sm font-semibold text-gray-900 group-hover:text-[#D47A22] transition-colors">
                            {project.name}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wide">
                              {project.type}
                            </span>
                            <span className="text-gray-300">•</span>
                            <span className="text-[10px] text-gray-400 font-mono">
                              ID: {project.project_id.slice(0, 8)}...
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* State / District */}
                      <td className="px-4 py-3.5 border-r border-gray-100">
                        <p className="text-xs font-semibold text-gray-800">
                          {project.states?.join(", ") || "Uttar Pradesh"}
                        </p>
                        <p className="text-xs text-gray-600 mt-0.5">
                          {project.districts?.join(", ") || "—"}
                        </p>
                      </td>

                      {/* Land Required */}
                      <td className="px-4 py-3.5 border-r border-gray-100 whitespace-nowrap">
                        <span className="text-sm font-bold font-mono text-gray-900">
                          {project.land_required_ha.toLocaleString("en-IN", {
                            minimumFractionDigits: 2,
                          })}
                        </span>
                        <span className="text-xs text-gray-500 ml-1">HA</span>
                      </td>

                      {/* Acquisition Progress */}
                      <td className="px-4 py-3.5 border-r border-gray-100 min-w-[180px]">
                        <div className="flex flex-col gap-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-gray-900 font-mono">
                              {progPct.toFixed(1)}%
                            </span>
                            <span className="text-[11px] text-gray-500 font-mono">
                              {project.land_acquired_ha?.toFixed(1) || 0} /{" "}
                              {project.land_required_ha?.toFixed(1) || 0} HA
                            </span>
                          </div>
                          <div className="w-full h-2.5 bg-gray-100 border border-gray-300 rounded-none overflow-hidden">
                            <div
                              className={cn(
                                "h-full rounded-none transition-all duration-300",
                                progPct >= 50
                                  ? "bg-emerald-600"
                                  : progPct >= 35
                                  ? "bg-[#D47A22]"
                                  : "bg-amber-600"
                              )}
                              style={{ width: `${Math.min(progPct, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Risk Level */}
                      <td className="px-4 py-3.5 border-r border-gray-100 whitespace-nowrap">
                        <div className="flex flex-col items-start gap-1">
                          <Badge
                            variant="risk"
                            level={riskLevel}
                            className={cn(
                              "rounded-none px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider",
                              riskLevel === "HIGH" && "bg-red-50 text-red-800 border border-red-300",
                              riskLevel === "MEDIUM" && "bg-amber-50 text-amber-800 border border-amber-300",
                              riskLevel === "LOW" && "bg-emerald-50 text-emerald-800 border border-emerald-300"
                            )}
                          >
                            {riskLevel}
                          </Badge>
                          <div className="flex items-center gap-1">
                            <span className="text-[11px] font-mono text-gray-500">
                              Score: {riskScore.toFixed(1)}/100
                            </span>
                            <RiskTooltip score={riskScore} type="PROJECT" />
                          </div>
                        </div>
                      </td>

                      {/* Target Date */}
                      <td className="px-4 py-3.5 border-r border-gray-100 whitespace-nowrap">
                        <span className="text-xs font-medium text-gray-700">
                          {project.target_date ? formatDate(project.target_date) : "TBD"}
                        </span>
                      </td>

                      {/* Action Chevron */}
                      <td className="px-3 py-3.5 text-center">
                        <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-[#D47A22] transition-colors" />
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-gray-500">
                    <p className="text-sm font-semibold">No projects found</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Try adjusting search terms or resetting the district/state filters.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 border-t border-gray-300 bg-gray-50">
            <p className="text-xs text-gray-600 font-medium">
              Showing <span className="font-bold text-gray-900">{(page - 1) * limit + 1}</span> to{" "}
              <span className="font-bold text-gray-900">{Math.min(page * limit, data.total)}</span> of{" "}
              <span className="font-bold text-gray-900">{data.total}</span> entries
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-2.5 py-1.5 rounded-none border border-gray-300 bg-white text-xs font-semibold text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5 inline mr-1" />
                Previous
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i + 1)}
                  className={cn(
                    "w-7 h-7 rounded-none border text-xs font-semibold transition-colors",
                    page === i + 1
                      ? "bg-[#D47A22] text-white border-[#D47A22]"
                      : "bg-white border-gray-300 text-gray-700 hover:bg-gray-100"
                  )}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="px-2.5 py-1.5 rounded-none border border-gray-300 bg-white text-xs font-semibold text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5 inline ml-1" />
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

export default ProjectListPage;
