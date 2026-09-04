import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, CheckCircle2, Filter, AlertTriangle, Info, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

interface AlertItem {
  id: string;
  type: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  message: string;
  entity: string;
  entity_type: string;
  time: string;
  is_read: boolean;
}

const MOCK_ALERTS: AlertItem[] = [
  { id: "a1", type: "SLA_BREACH", severity: "CRITICAL", message: "SLA breached for verification stage — 78 days pending", entity: "Parcel SN-310/C", entity_type: "parcel", time: "10 mins ago", is_read: false },
  { id: "a2", type: "DISPUTE", severity: "CRITICAL", message: "Legal dispute filed by landowner — objection under Sec 3H", entity: "Parcel SN-310/C", entity_type: "parcel", time: "1 hr ago", is_read: false },
  { id: "a3", type: "COMPENSATION_DELAY", severity: "WARNING", message: "Compensation disbursement delayed > 30 days", entity: "Mumbai-Ahmedabad HSR", entity_type: "project", time: "3 hrs ago", is_read: false },
  { id: "a4", type: "DOCUMENT_UPLOADED", severity: "INFO", message: "Joint Measurement Report uploaded and verified", entity: "Parcel SN-145/A", entity_type: "parcel", time: "5 hrs ago", is_read: true },
  { id: "a5", type: "STAGE_TRANSITION", severity: "INFO", message: "Parcel moved from Survey to Verification stage", entity: "Parcel SN-550", entity_type: "parcel", time: "6 hrs ago", is_read: true },
  { id: "a6", type: "RISK_ESCALATION", severity: "WARNING", message: "Risk score increased from 45 to 78 — project flagged", entity: "Coastal Road Extension", entity_type: "project", time: "Yesterday", is_read: true },
];

const SEVERITY_ICON = {
  CRITICAL: <AlertCircle className="w-4 h-4 text-red-500" />,
  WARNING: <AlertTriangle className="w-4 h-4 text-amber-500" />,
  INFO: <Info className="w-4 h-4 text-blue-500" />,
};

export function AlertsPage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<string>("ALL");
  const [alerts, setAlerts] = useState(MOCK_ALERTS);

  const filtered = filter === "ALL" ? alerts : alerts.filter((a) => a.severity === filter);
  const unreadCount = alerts.filter((a) => !a.is_read).length;

  const markRead = (id: string) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true } : a)));
  };

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
            <Bell className="w-6 h-6 text-brand-copper" />
            Alerts & Interventions
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {unreadCount} unread alerts requiring attention.
          </p>
        </div>
        <button
          onClick={() => setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })))}
          className="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 text-sm font-medium rounded-xl hover:bg-gray-50 transition-colors"
        >
          <CheckCircle2 className="w-4 h-4" />
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
              "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors",
              filter === f ? "bg-brand-teal-blue text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Alert List */}
      <div className="space-y-2">
        {filtered.map((alert) => (
          <Card
            key={alert.id}
            className={cn("p-4 cursor-pointer hover:shadow-card-hover transition-all", !alert.is_read && "border-l-4 border-l-brand-copper bg-amber-50/30")}
            onClick={() => { markRead(alert.id); navigate(alert.entity_type === "parcel" ? `/parcels/${alert.id}` : `/projects/${alert.id}`); }}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5">{SEVERITY_ICON[alert.severity]}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <Badge variant="severity" level={alert.severity}>{alert.severity}</Badge>
                  <span className="text-[10px] text-gray-400">{alert.type.replace(/_/g, " ")}</span>
                </div>
                <p className="text-sm text-gray-800 font-medium">{alert.message}</p>
                <p className="text-xs text-brand-teal-blue font-medium mt-0.5">{alert.entity}</p>
              </div>
              <span className="text-[10px] text-gray-400 flex-shrink-0">{alert.time}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default AlertsPage;
