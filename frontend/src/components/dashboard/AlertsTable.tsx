import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { ChevronDown, ChevronUp, ChevronRight, AlertOctagon } from "lucide-react";
import type { DashboardAlert } from "@/api/dashboard";

interface AlertsTableProps {
  alerts: DashboardAlert[];
  onViewAll?: () => void;
}

export function AlertsTable({ alerts, onViewAll }: AlertsTableProps) {
  const [expanded, setExpanded] = useState(false);

  const initialCount = 5;
  const displayedAlerts = expanded ? alerts : alerts.slice(0, initialCount);
  const remainingCount = Math.max(0, alerts.length - initialCount);

  if (!alerts || alerts.length === 0) {
    return (
      <div className="py-12 text-center text-gray-500 text-xs border border-dashed border-gray-200 m-4">
        <AlertOctagon className="w-6 h-6 mx-auto mb-2 text-gray-400" />
        No critical alerts or SLA compliance flags detected at this time.
      </div>
    );
  }

  return (
    <div className="border border-gray-200">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-[11px] font-bold text-gray-700 uppercase tracking-wider px-3.5 py-2.5 border-r border-gray-200">
                Project Name
              </th>
              <th className="text-[11px] font-bold text-gray-700 uppercase tracking-wider px-3.5 py-2.5 border-r border-gray-200">
                Issue / Incident Type
              </th>
              <th className="text-[11px] font-bold text-gray-700 uppercase tracking-wider px-3.5 py-2.5 border-r border-gray-200 text-center">
                Severity
              </th>
              <th className="text-right text-[11px] font-bold text-gray-700 uppercase tracking-wider px-3.5 py-2.5">
                Timestamp
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {displayedAlerts.map((alert) => (
              <tr
                key={alert.id}
                className="hover:bg-amber-50/40 transition-colors group cursor-pointer"
                onClick={onViewAll}
              >
                <td className="px-3.5 py-2.5 border-r border-gray-100 text-xs font-semibold text-gray-900 group-hover:text-[#D47A22]">
                  {alert.project_name}
                </td>
                <td className="px-3.5 py-2.5 border-r border-gray-100 text-xs text-gray-700 font-medium">
                  {alert.issue_type}
                </td>
                <td className="px-3.5 py-2.5 border-r border-gray-100 text-center">
                  <Badge variant="severity" level={alert.severity} className="rounded-none font-bold uppercase text-[9px] px-2 py-0.5">
                    {alert.severity}
                  </Badge>
                </td>
                <td className="px-3.5 py-2.5 text-right text-xs font-mono text-gray-500 whitespace-nowrap">
                  {alert.time_ago}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Action Footer: Show More Toggle & View All */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-gray-50/80 border-t border-gray-200">
        {alerts.length > initialCount ? (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 text-xs font-bold text-[#D47A22] hover:text-[#B56315] transition-colors cursor-pointer"
          >
            {expanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                Show Fewer Priority Alerts
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                Show More Priority Alerts ({remainingCount} more)
              </>
            )}
          </button>
        ) : (
          <span className="text-[11px] text-gray-500">Showing all {alerts.length} priority notifications</span>
        )}

        {onViewAll && (
          <button
            type="button"
            onClick={onViewAll}
            className="flex items-center gap-1 text-xs font-bold text-gray-700 hover:text-[#D47A22] transition-colors cursor-pointer"
          >
            View All Incident Logs
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
