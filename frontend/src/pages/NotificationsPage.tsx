import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  Info,
  Shield,
  Clock,
  FileText,
  DollarSign,
  Settings,
  Check,
  Loader2,
  Filter,
  Layers,
  Building2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from "@/api/notifications";
import type { AppNotification, NotificationCategory } from "@/types/api";

const CATEGORY_CONFIG: Record<
  NotificationCategory,
  { label: string; icon: React.ElementType; color: string }
> = {
  APPROVAL: {
    label: "Approval",
    icon: Shield,
    color: "text-blue-600 bg-blue-50",
  },
  SLA_BREACH: {
    label: "SLA Breach",
    icon: AlertTriangle,
    color: "text-red-600 bg-red-50",
  },
  DOCUMENT: {
    label: "Document",
    icon: FileText,
    color: "text-purple-600 bg-purple-50",
  },
  COMPENSATION: {
    label: "Compensation",
    icon: DollarSign,
    color: "text-emerald-600 bg-emerald-50",
  },
  SYSTEM: {
    label: "System",
    icon: Settings,
    color: "text-gray-600 bg-gray-50",
  },
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export function NotificationsPage() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [markingAll, setMarkingAll] = useState(false);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (categoryFilter !== "ALL") params.category = categoryFilter;
      const data = await getNotifications(params);
      setNotifications(data);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    } finally {
      setLoading(false);
    }
  }, [categoryFilter]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) =>
          n.notification_id === id
            ? { ...n, is_read: true, read_at: new Date().toISOString() }
            : n
        )
      );
    } catch {
      // Silently fail
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await markAllNotificationsRead();
      setNotifications((prev) =>
        prev.map((n) => ({
          ...n,
          is_read: true,
          read_at: new Date().toISOString(),
        }))
      );
    } catch {
      // Silently fail
    } finally {
      setMarkingAll(false);
    }
  };

  const handleClick = (n: AppNotification) => {
    if (!n.is_read) handleMarkRead(n.notification_id);
    
    // Resolve specific detail page route if entity_id is available
    if (n.entity_type === "parcel" && n.entity_id) {
      navigate(`/parcels/${n.entity_id}`);
    } else if (n.entity_type === "project" && n.entity_id) {
      navigate(`/projects/${n.entity_id}`);
    } else if (n.action_url) {
      navigate(n.action_url);
    } else {
      navigate("/parcels");
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bell className="w-7 h-7 text-[#D47A22]" />
            Notifications
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {unreadCount > 0 ? (
              <>
                <span className="font-semibold text-[#D47A22]">
                  {unreadCount} unread
                </span>{" "}
                notification{unreadCount !== 1 ? "s" : ""}
              </>
            ) : (
              "All caught up!"
            )}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Category Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700 focus:ring-2 focus:ring-[#D47A22]/30 focus:border-[#D47A22]"
            >
              <option value="ALL">All Categories</option>
              <option value="APPROVAL">Approvals</option>
              <option value="SLA_BREACH">SLA Breaches</option>
              <option value="DOCUMENT">Documents</option>
              <option value="COMPENSATION">Compensation</option>
              <option value="SYSTEM">System</option>
            </select>
          </div>

          {/* Mark All Read */}
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={markingAll}
              className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-[#D47A22] bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 disabled:opacity-50 transition-colors"
            >
              {markingAll ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
              Mark All Read
            </button>
          )}
        </div>
      </div>

      {/* Notification List */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 text-[#D47A22] animate-spin" />
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-16 bg-white border border-gray-200 rounded-xl">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No notifications</p>
          <p className="text-xs text-gray-400 mt-1">
            You're all caught up! Notifications will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => {
            const catConfig =
              CATEGORY_CONFIG[n.category] || CATEGORY_CONFIG.SYSTEM;
            const CatIcon = catConfig.icon;
            const sevIcon =
              n.severity === "CRITICAL"
                ? AlertTriangle
                : n.severity === "WARNING"
                ? Clock
                : Info;
            const SevIcon = sevIcon;

            return (
              <div
                key={n.notification_id}
                onClick={() => handleClick(n)}
                className={cn(
                  "flex items-start gap-4 px-4 py-3 rounded-xl border cursor-pointer transition-all hover:shadow-sm",
                  n.is_read
                    ? "bg-white border-gray-100"
                    : "bg-amber-50/40 border-amber-200/60"
                )}
              >
                {/* Category Icon */}
                <div
                  className={cn(
                    "w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0",
                    catConfig.color
                  )}
                >
                  <CatIcon className="w-4 h-4" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p
                      className={cn(
                        "text-sm",
                        n.is_read
                          ? "text-gray-700"
                          : "text-gray-900 font-semibold"
                      )}
                    >
                      {n.title}
                    </p>
                    <span className="text-[10px] text-gray-400 flex-shrink-0">
                      {timeAgo(n.created_at)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                    {n.message}
                  </p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded",
                        catConfig.color
                      )}
                    >
                      {catConfig.label}
                    </span>
                    {n.severity !== "INFO" && (
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded",
                          n.severity === "CRITICAL"
                            ? "bg-red-50 text-red-600"
                            : "bg-amber-50 text-amber-600"
                        )}
                      >
                        <SevIcon className="w-3 h-3" />
                        {n.severity}
                      </span>
                    )}
                    {/* Linked Entity Pill */}
                    {n.entity_type === "parcel" && n.entity_id && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                        <Layers className="w-3 h-3 text-blue-600" />
                        {n.metadata?.entity_name || "Linked Parcel"}
                      </span>
                    )}
                    {n.entity_type === "project" && n.entity_id && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-300">
                        <Building2 className="w-3 h-3 text-amber-700" />
                        {n.metadata?.entity_name || "Linked Project"}
                      </span>
                    )}
                  </div>
                </div>

                {/* Unread Dot */}
                {!n.is_read && (
                  <div className="w-2.5 h-2.5 rounded-full bg-[#D47A22] flex-shrink-0 mt-1.5" />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default NotificationsPage;
