import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  FolderKanban,
  Search,
  Download,
  Plus,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
} from "lucide-react";
import { listProjects } from "@/api/projects";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn, formatDate } from "@/lib/utils";

export function ProjectListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const limit = 10;

  const { data, isLoading } = useQuery({
    queryKey: ["projects", { search, page, sortBy, sortOrder }],
    queryFn: () =>
      listProjects({ search, page, limit, sort_by: sortBy, sort_order: sortOrder }),
  });

  const handleSort = (key: string) => {
    if (sortBy === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(key);
      setSortOrder("asc");
    }
  };

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
            <FolderKanban className="w-6 h-6 text-brand-teal-blue" />
            Project Inventory
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage and monitor all land acquisition projects across active regions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 text-sm font-medium rounded-xl hover:bg-gray-50 transition-colors">
            <Download className="w-4 h-4" />
            Export Report
          </button>
          <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-teal-blue text-white text-sm font-medium rounded-xl hover:bg-[#245d82] transition-colors">
            <Plus className="w-4 h-4" />
            Create New Project
          </button>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search project name..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-gray-200 bg-gray-50/80 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30 focus:border-brand-teal-blue"
            />
          </div>
          <select className="px-3 py-2.5 rounded-lg border border-gray-200 bg-white text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30">
            <option>All States</option>
            <option>Maharashtra</option>
            <option>Gujarat</option>
            <option>Karnataka</option>
            <option>Uttar Pradesh</option>
            <option>Kerala</option>
          </select>
          <select className="px-3 py-2.5 rounded-lg border border-gray-200 bg-white text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30">
            <option>All Districts</option>
          </select>
          <button className="px-3 py-2.5 rounded-lg border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors flex items-center gap-1.5">
            <ArrowUpDown className="w-3.5 h-3.5" />
            More Filters
          </button>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/50">
                {[
                  { key: "name", label: "Project Name" },
                  { key: "states", label: "State / District" },
                  { key: "land_required_ha", label: "Land Required (HA)" },
                  { key: "progress_pct", label: "Acquisition Progress" },
                  { key: "risk_score", label: "Risk Level" },
                  { key: "target_date", label: "Target Date" },
                ].map((col) => (
                  <th
                    key={col.key}
                    className="text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider px-4 py-3 cursor-pointer hover:text-gray-700 select-none"
                    onClick={() => handleSort(col.key)}
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      {sortBy === col.key && (
                        <span className="text-brand-teal-blue">
                          {sortOrder === "asc" ? "↑" : "↓"}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} className="px-4 py-4">
                          <div className="h-4 animate-shimmer rounded w-full" />
                        </td>
                      ))}
                    </tr>
                  ))
                : data?.data.map((project) => (
                    <tr
                      key={project.project_id}
                      className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors cursor-pointer group"
                      onClick={() => navigate(`/projects/${project.project_id}`)}
                    >
                      <td className="px-4 py-3.5">
                        <div>
                          <p className="text-sm font-semibold text-brand-teal-blue group-hover:underline">
                            {project.name}
                          </p>
                          <p className="text-[11px] text-gray-400 font-mono mt-0.5">
                            ID: {project.project_id}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <p className="text-sm text-gray-700">
                          {project.states.join(", ")}
                        </p>
                        <p className="text-[11px] text-gray-400">
                          {project.districts.join(", ")}
                        </p>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-sm font-mono text-gray-800">
                          {project.land_required_ha.toLocaleString("en-IN", {
                            minimumFractionDigits: 2,
                          })}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                "h-full rounded-full transition-all",
                                project.progress_pct >= 75
                                  ? "bg-brand-sage-green"
                                  : project.progress_pct >= 40
                                  ? "bg-brand-teal-blue"
                                  : "bg-brand-copper"
                              )}
                              style={{ width: `${project.progress_pct}%` }}
                            />
                          </div>
                          <span className="text-xs font-medium text-gray-600 w-8">
                            {project.progress_pct}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <Badge
                          variant="risk"
                          level={
                            project.risk_score >= 70
                              ? "HIGH"
                              : project.risk_score >= 40
                              ? "MEDIUM"
                              : "LOW"
                          }
                        >
                          {project.risk_score >= 70
                            ? "High"
                            : project.risk_score >= 40
                            ? "Med"
                            : "Low"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-sm text-gray-600">
                          {formatDate(project.target_date)}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-brand-teal-blue transition-colors" />
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              Showing {(page - 1) * limit + 1} to{" "}
              {Math.min(page * limit, data.total)} of {data.total} entries
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i + 1)}
                  className={cn(
                    "w-8 h-8 rounded-lg text-xs font-medium transition-colors",
                    page === i + 1
                      ? "bg-brand-teal-blue text-white"
                      : "hover:bg-gray-100 text-gray-600"
                  )}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
