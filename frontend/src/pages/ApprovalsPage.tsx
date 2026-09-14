import { useState, useEffect, useCallback } from "react";
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  Clock,
  FileText,
  ChevronDown,
  ChevronUp,
  Shield,
  Send,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import {
  getApprovalQueue,
  approveDocument,
  rejectDocument,
  requestRevision,
  getApprovalHistory,
} from "@/api/approvals";
import type {
  ApprovalQueueItem,
  DocumentApproval,
  ApprovalStatus,
} from "@/types/api";

const STATUS_CONFIG: Record<
  ApprovalStatus,
  { label: string; color: string; bg: string; icon: React.ElementType }
> = {
  PENDING_REVIEW: {
    label: "Pending Review",
    color: "text-amber-700",
    bg: "bg-amber-50 border-amber-200",
    icon: Clock,
  },
  UNDER_REVIEW: {
    label: "Under Review",
    color: "text-blue-700",
    bg: "bg-blue-50 border-blue-200",
    icon: Shield,
  },
  APPROVED: {
    label: "Approved",
    color: "text-emerald-700",
    bg: "bg-emerald-50 border-emerald-200",
    icon: CheckCircle2,
  },
  REJECTED: {
    label: "Rejected",
    color: "text-red-700",
    bg: "bg-red-50 border-red-200",
    icon: XCircle,
  },
  REVISION_REQUESTED: {
    label: "Revision Requested",
    color: "text-orange-700",
    bg: "bg-orange-50 border-orange-200",
    icon: RotateCcw,
  },
};

const APPROVAL_CHAIN = [
  "FIELD_OFFICER",
  "DISTRICT",
  "STATE",
  "PROJECT_AGENCY",
] as const;

function ApprovalTimeline({ history }: { history: DocumentApproval[] }) {
  if (!history || history.length === 0) {
    return (
      <p className="text-xs text-gray-400 italic py-2">
        No approval actions yet.
      </p>
    );
  }

  return (
    <div className="relative pl-6 py-2 space-y-3">
      <div className="absolute left-[11px] top-0 bottom-0 w-0.5 bg-gray-200" />
      {history.map((entry, idx) => {
        const isApprove = entry.action === "APPROVE";
        const isReject = entry.action === "REJECT";
        return (
          <div key={entry.approval_id || idx} className="relative flex gap-3">
            <div
              className={cn(
                "absolute -left-6 top-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center",
                isApprove
                  ? "bg-emerald-100 border-emerald-400"
                  : isReject
                  ? "bg-red-100 border-red-400"
                  : "bg-amber-100 border-amber-400"
              )}
            >
              {isApprove ? (
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              ) : isReject ? (
                <XCircle className="w-3 h-3 text-red-600" />
              ) : (
                <RotateCcw className="w-3 h-3 text-amber-600" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">
                {entry.action.replace(/_/g, " ")}{" "}
                <span className="text-gray-500 font-normal">
                  by {entry.approver_username || entry.approver_role}
                </span>
              </p>
              {entry.remarks && (
                <p className="text-xs text-gray-500 mt-0.5">
                  "{entry.remarks}"
                </p>
              )}
              <p className="text-[10px] text-gray-400 mt-0.5">
                Step {entry.step_order} •{" "}
                {new Date(entry.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ApprovalsPage() {
  const { user } = useAuthStore();
  const [items, setItems] = useState<ApprovalQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [remarks, setRemarks] = useState<Record<string, string>>({});
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [historyCache, setHistoryCache] = useState<
    Record<string, DocumentApproval[]>
  >({});

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter !== "ALL") params.status = statusFilter;
      const data = await getApprovalQueue(params);
      setItems(data);
    } catch (err) {
      console.error("Failed to fetch approval queue:", err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const handleExpand = async (docId: string) => {
    if (expandedId === docId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(docId);
    if (!historyCache[docId]) {
      try {
        const history = await getApprovalHistory(docId);
        setHistoryCache((prev) => ({ ...prev, [docId]: history }));
      } catch {
        // Silently fail — timeline will show empty
      }
    }
  };

  const handleAction = async (
    docId: string,
    action: "approve" | "reject" | "revise"
  ) => {
    const docRemarks = remarks[docId] || "";
    if ((action === "reject" || action === "revise") && !docRemarks.trim()) {
      alert("Please provide remarks for rejection or revision request.");
      return;
    }
    setActionLoading(docId);
    try {
      if (action === "approve") {
        await approveDocument(docId, docRemarks || undefined);
      } else if (action === "reject") {
        await rejectDocument(docId, docRemarks);
      } else {
        await requestRevision(docId, docRemarks);
      }
      setRemarks((prev) => ({ ...prev, [docId]: "" }));
      await fetchQueue();
    } catch (err: any) {
      alert(
        err?.response?.data?.detail || `Failed to ${action} document.`
      );
    } finally {
      setActionLoading(null);
    }
  };

  const pendingCount = items.filter(
    (i) =>
      i.approval_status === "PENDING_REVIEW" ||
      i.approval_status === "UNDER_REVIEW"
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-7 h-7 text-[#D47A22]" />
            Approval Queue
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Multi-level document approval workflow •{" "}
            <span className="font-semibold text-amber-600">
              {pendingCount} pending
            </span>
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700 focus:ring-2 focus:ring-[#D47A22]/30 focus:border-[#D47A22]"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="REVISION_REQUESTED">Revision Requested</option>
          </select>
        </div>
      </div>

      {/* Approval Chain Visualization */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Approval Chain
        </p>
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {APPROVAL_CHAIN.map((role, idx) => (
            <div key={role} className="flex items-center gap-1 flex-shrink-0">
              <div
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold border",
                  user?.role === role
                    ? "bg-[#D47A22] text-white border-[#D47A22]"
                    : "bg-gray-50 text-gray-600 border-gray-200"
                )}
              >
                {role.replace(/_/g, " ")}
              </div>
              {idx < APPROVAL_CHAIN.length - 1 && (
                <Send className="w-3 h-3 text-gray-300 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Queue Table */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 text-[#D47A22] animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 bg-white border border-gray-200 rounded-xl">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">
            No documents in the approval queue
          </p>
          <p className="text-xs text-gray-400 mt-1">
            All clear! Documents will appear here when uploaded.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const config = STATUS_CONFIG[item.approval_status] || STATUS_CONFIG.PENDING_REVIEW;
            const StatusIcon = config.icon;
            const isExpanded = expandedId === item.document_id;
            const isActionable =
              (item as any).is_actionable !== undefined
                ? (item as any).is_actionable
                : (item.approval_status === "PENDING_REVIEW" || item.approval_status === "UNDER_REVIEW");

            return (
              <div
                key={item.document_id}
                className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Row */}
                <div
                  className="flex items-center gap-4 px-4 py-3 cursor-pointer"
                  onClick={() => handleExpand(item.document_id)}
                >
                  <div className="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4 text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">
                      {item.title || item.document_type}
                    </p>
                    <p className="text-xs text-gray-400">
                      by {item.uploader_username || item.uploaded_by} •{" "}
                      {item.project_name ? `${item.project_name} • ` : ""}
                      {new Date(item.created_at).toLocaleDateString()} •
                      Step {item.current_approval_step}/
                      {APPROVAL_CHAIN.length}
                    </p>
                  </div>
                  <span
                    className={cn(
                      "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border",
                      config.bg,
                      config.color
                    )}
                  >
                    <StatusIcon className="w-3.5 h-3.5" />
                    {config.label}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </div>

                {/* Expanded Panel */}
                {isExpanded && (
                  <div className="border-t border-gray-100 px-4 py-4 bg-gray-50/50">
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Timeline */}
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                          Approval Timeline
                        </p>
                        <ApprovalTimeline
                          history={
                            historyCache[item.document_id] ||
                            item.approval_history ||
                            []
                          }
                        />
                      </div>

                      {/* Actions */}
                      {isActionable ? (
                        <div>
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                            Actions
                          </p>
                          <textarea
                            value={remarks[item.document_id] || ""}
                            onChange={(e) =>
                              setRemarks((prev) => ({
                                ...prev,
                                [item.document_id]: e.target.value,
                              }))
                            }
                            placeholder="Add remarks (required for reject/revise)..."
                            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 mb-3 resize-none h-20 focus:ring-2 focus:ring-[#D47A22]/30 focus:border-[#D47A22]"
                          />
                          <div className="flex items-center gap-2 flex-wrap">
                            <button
                              onClick={() =>
                                handleAction(item.document_id, "approve")
                              }
                              disabled={actionLoading === item.document_id}
                              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors cursor-pointer"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                              Approve
                            </button>
                            <button
                              onClick={() =>
                                handleAction(item.document_id, "revise")
                              }
                              disabled={actionLoading === item.document_id}
                              className="flex items-center gap-1.5 px-4 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors cursor-pointer"
                            >
                              <RotateCcw className="w-4 h-4" />
                              Request Revision
                            </button>
                            <button
                              onClick={() =>
                                handleAction(item.document_id, "reject")
                              }
                              disabled={actionLoading === item.document_id}
                              className="flex items-center gap-1.5 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors cursor-pointer"
                            >
                              <XCircle className="w-4 h-4" />
                              Reject
                            </button>
                          </div>
                          {actionLoading === item.document_id && (
                            <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Processing...
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-sm text-gray-500 bg-amber-50/60 p-3 rounded-lg border border-amber-200/50">
                          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />
                          <span>
                            {item.approval_status === "APPROVED"
                              ? "This document has been fully approved."
                              : item.approval_status === "REJECTED"
                              ? "This document was rejected."
                              : `Pending review at Step ${item.current_approval_step + 1} (${APPROVAL_CHAIN[item.current_approval_step] || "Next Officer"}).`}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ApprovalsPage;
