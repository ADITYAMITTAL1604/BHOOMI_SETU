import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle2, Filter, AlertTriangle, Info, AlertCircle, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import { getAlerts, markAlertAsRead, markAllAlertsAsRead } from "@/api/alerts";

const SEVERITY_ICON: Record<string, React.ReactNode> = {
  CRITICAL: <AlertCircle className="w-4 h-4 text-red-500" />,
  WARNING: <AlertTriangle className="w-4 h-4 text-amber-500" />,
  INFO: <Info className="w-4 h-4 text-blue-500" />,
};

export function AlertsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<string>("ALL");

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => getAlerts(false),
  });

  const markReadMutation = useMutation({
    mutationFn: markAlertAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-alerts"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllAlertsAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-alerts"] });
    },
  });

  const filtered = filter === "ALL" ? alerts : alerts.filter((a) => a.severity === filter);
  const unreadCount = alerts.filter((a) => !a.is_read).length;

  const handleAlertClick = (alert: any) => {
    if (!alert.is_read) {
      markReadMutation.mutate(alert.alert_id);
    }
    
    // Navigate based on available context
    if (alert.parcel_id) {
      navigate(`/parcels/${alert.parcel_id}`);
    } else if (alert.project_id) {
      navigate(`/projects/${alert.project_id}`);
    }
  };

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
            <Bell className="w-6 h-6 text-[#D47A22]" />
            Alerts & Interventions
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {unreadCount} unread alerts requiring attention.
          </p>
        </div>
        <button
          onClick={() => markAllReadMutation.mutate()}
          disabled={markAllReadMutation.isPending || unreadCount === 0}
          className="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-300 text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 transition-colors rounded-none disabled:opacity-50"
        >
          {markAllReadMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
          Mark All Read
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-400" />
        {["ALL", "CRITICAL", "WARNING", "INFO"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "px-3 py-1.5 rounded-none text-xs font-semibold transition-colors border border-transparent",
              filter === f ? "bg-[#183a37] text-white border-[#183a37]" : "bg-white border-gray-300 text-gray-600 hover:bg-gray-100"
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Alert List */}
      <div className="space-y-2">
        {isLoading ? (
          <div className="py-12 text-center text-sm text-gray-500">Loading alerts...</div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-sm text-gray-500">No alerts found.</div>
        ) : (
          filtered.map((alert) => {
            let entityStr = "System";
            let typeStr = "ALERT";
            let timeStr = new Date(alert.created_at).toLocaleString();
            
            try {
              if (alert.metadata) {
                const meta = typeof alert.metadata === 'string' ? JSON.parse(alert.metadata) : alert.metadata;
                entityStr = meta.survey_number ? `Parcel ${meta.survey_number}` : meta.project_name || "Project Alert";
                typeStr = meta.issue_type || meta.stage_name || typeStr;
                timeStr = meta.time_ago || timeStr;
              }
            } catch (e) {
              console.error("Failed to parse alert metadata", e);
            }

            return (
              <Card
                key={alert.alert_id}
                className={cn(
                  "p-4 cursor-pointer hover:shadow-sm transition-all rounded-none border border-gray-200", 
                  !alert.is_read ? "border-l-4 border-l-[#D47A22] bg-amber-50/30" : "bg-white"
                )}
                onClick={() => handleAlertClick(alert)}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{SEVERITY_ICON[alert.severity] || SEVERITY_ICON.INFO}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <Badge variant="risk" level={alert.severity} className="rounded-none px-2 py-0.5 text-[10px] uppercase font-bold">{alert.severity}</Badge>
                      <span className="text-[10px] text-gray-500 font-mono uppercase">{typeStr}</span>
                    </div>
                    <p className="text-sm text-gray-900 font-semibold">{alert.title}</p>
                    <p className="text-xs text-gray-600 mt-1">{alert.message}</p>
                    <p className="text-xs text-[#183a37] font-semibold mt-1.5">{entityStr}</p>
                  </div>
                  <span className="text-[10px] text-gray-400 font-mono flex-shrink-0">{timeStr}</span>
                </div>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}

export default AlertsPage;
