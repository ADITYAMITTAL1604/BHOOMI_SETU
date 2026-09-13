import { useState, useEffect } from "react";
import {
  User,
  ArrowRight,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import apiClient from "@/api/client";

interface TimelineEvent {
  log_id: string;
  action: string;
  username: string | null;
  user_id: string | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  created_at: string | null;
}

interface AuditTimelineProps {
  entityType: string;
  entityId: string;
  className?: string;
}

const ACTION_COLORS: Record<string, string> = {
  CREATE: "bg-emerald-100 border-emerald-400 text-emerald-700",
  UPDATE: "bg-blue-100 border-blue-400 text-blue-700",
  DELETE: "bg-red-100 border-red-400 text-red-700",
  STAGE_TRANSITION: "bg-purple-100 border-purple-400 text-purple-700",
  APPROVE: "bg-emerald-100 border-emerald-400 text-emerald-700",
  REJECT: "bg-red-100 border-red-400 text-red-700",
  UPLOAD: "bg-amber-100 border-amber-400 text-amber-700",
};

function getActionColor(action: string): string {
  for (const [key, color] of Object.entries(ACTION_COLORS)) {
    if (action.toUpperCase().includes(key)) return color;
  }
  return "bg-gray-100 border-gray-400 text-gray-700";
}

export function AuditTimeline({
  entityType,
  entityId,
  className,
}: AuditTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTimeline() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get(
          `/audit-log/timeline/${entityType}/${entityId}`
        );
        setEvents(response.data?.timeline || []);
      } catch (err: any) {
        if (err?.response?.status === 404) {
          setEvents([]);
        } else {
          setError("Failed to load audit timeline.");
        }
      } finally {
        setLoading(false);
      }
    }
    if (entityType && entityId) {
      fetchTimeline();
    }
  }, [entityType, entityId]);

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center py-6", className)}>
        <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 py-4 text-sm text-red-500",
          className
        )}
      >
        <AlertCircle className="w-4 h-4" />
        {error}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div
        className={cn("text-xs text-gray-400 italic py-4 text-center", className)}
      >
        No audit events recorded for this entity.
      </div>
    );
  }

  return (
    <div className={cn("relative", className)}>
      <div className="absolute left-[15px] top-0 bottom-0 w-0.5 bg-gray-200" />
      <div className="space-y-4">
        {events.map((event) => {
          const colorClass = getActionColor(event.action);
          return (
            <div key={event.log_id} className="relative pl-10">
              {/* Dot */}
              <div
                className={cn(
                  "absolute left-[7px] top-1 w-[18px] h-[18px] rounded-full border-2 flex items-center justify-center",
                  colorClass
                )}
              >
                <div className="w-2 h-2 rounded-full bg-current" />
              </div>

              {/* Content */}
              <div className="bg-white border border-gray-100 rounded-lg p-3 hover:shadow-sm transition-shadow">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border",
                        colorClass
                      )}
                    >
                      {event.action.replace(/_/g, " ")}
                    </span>
                    <div className="flex items-center gap-2 mt-1.5 text-xs text-gray-500">
                      <User className="w-3 h-3" />
                      <span>{event.username || "System"}</span>
                    </div>
                  </div>
                  <span className="text-[10px] text-gray-400 flex-shrink-0">
                    {event.created_at
                      ? new Date(event.created_at).toLocaleString()
                      : ""}
                  </span>
                </div>

                {/* Changes summary */}
                {event.new_values &&
                  Object.keys(event.new_values).length > 0 && (
                    <div className="mt-2 text-xs text-gray-600 space-y-0.5">
                      {Object.entries(event.new_values)
                        .slice(0, 4)
                        .map(([key, val]) => (
                          <div
                            key={key}
                            className="flex items-center gap-1.5"
                          >
                            <ArrowRight className="w-3 h-3 text-gray-300" />
                            <span className="font-medium text-gray-700">
                              {key.replace(/_/g, " ")}:
                            </span>
                            <span className="truncate">{String(val)}</span>
                          </div>
                        ))}
                      {Object.keys(event.new_values).length > 4 && (
                        <span className="text-gray-400 italic">
                          +{Object.keys(event.new_values).length - 4} more
                          fields
                        </span>
                      )}
                    </div>
                  )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
