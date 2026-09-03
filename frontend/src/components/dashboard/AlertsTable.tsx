import { Badge } from "@/components/ui/Badge";
import { ChevronRight } from "lucide-react";
import type { DashboardAlert } from "@/api/dashboard";

interface AlertsTableProps {
  alerts: DashboardAlert[];
  onViewAll?: () => void;
}

export function AlertsTable({ alerts, onViewAll }: AlertsTableProps) {
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-4 py-2.5">
                Project Name
              </th>
              <th className="text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-4 py-2.5">
                Issue Type
              </th>
              <th className="text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-4 py-2.5">
                Severity
              </th>
              <th className="text-right text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-4 py-2.5">
                Time
              </th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr
                key={alert.id}
                className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors cursor-pointer group"
              >
                <td className="px-4 py-3">
                  <span className="text-sm font-medium text-gray-800 group-hover:text-brand-teal-blue transition-colors">
                    {alert.project_name}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-600">{alert.issue_type}</span>
                </td>
                <td className="px-4 py-3">
                  <Badge variant="severity" level={alert.severity}>
                    {alert.severity}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs text-gray-400">{alert.time_ago}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {onViewAll && (
        <button
          onClick={onViewAll}
          className="flex items-center gap-1 px-4 py-2.5 text-xs font-semibold text-brand-teal-blue hover:text-brand-sea-green transition-colors mt-1"
        >
          View All
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
