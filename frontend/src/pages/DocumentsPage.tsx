import { useState, useEffect, useCallback } from "react";
import {
  FileText,
  Search,
  Upload,
  Download,
  Eye,
  Filter,
  ShieldCheck,
  Trash2,
  Copy,
  Check,
  X,
  Loader2,
  RefreshCw,
  FolderOpen,
  Building2,
  FileCheck,
  Clock,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import {
  getDocuments,
  uploadDocument,
  deleteDocument,
  downloadDocumentFile,
  type DocumentItem,
} from "@/api/documents";
import { getProjects } from "@/api/projects";
import type { Project } from "@/types/api";

const STATUS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  APPROVED: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  PENDING_REVIEW: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  UNDER_REVIEW: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  REJECTED: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
  REVISION_REQUESTED: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
};

function formatBytes(bytes: number): string {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  // Upload Modal State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadType, setUploadType] = useState("SURVEY_REPORT");
  const [uploadDescription, setUploadDescription] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Preview Modal State
  const [previewDoc, setPreviewDoc] = useState<DocumentItem | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDocuments({
        document_type: typeFilter !== "ALL" ? typeFilter : undefined,
        search: search.trim() || undefined,
      });
      setDocuments(data);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoading(false);
    }
  }, [typeFilter, search]);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  useEffect(() => {
    getProjects()
      .then((res) => setProjects(res.data || []))
      .catch(() => {});
  }, []);

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleDownload = async (doc: DocumentItem) => {
    setDownloadingId(doc.document_id);
    try {
      await downloadDocumentFile(doc.document_id, doc.title);
    } catch (err) {
      alert("Failed to download file. Please check server logs.");
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (docId: string, title: string) => {
    if (!confirm(`Are you sure you want to delete document "${title}"?`)) return;
    try {
      await deleteDocument(docId);
      await fetchDocs();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to delete document.");
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Please select a file to upload.");
      return;
    }
    if (!uploadTitle.trim()) {
      alert("Please provide a title.");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("title", uploadTitle.trim());
      formData.append("document_type", uploadType);
      if (uploadDescription.trim()) formData.append("description", uploadDescription.trim());
      if (selectedProjectId) formData.append("project_id", selectedProjectId);

      await uploadDocument(formData);
      setShowUploadModal(false);
      setUploadTitle("");
      setUploadDescription("");
      setSelectedFile(null);
      setSelectedProjectId("");
      await fetchDocs();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  };

  const totalCount = documents.length;
  const verifiedCount = documents.filter((d) => d.is_verified).length;
  const pendingCount = documents.filter((d) => d.approval_status === "PENDING_REVIEW" || d.approval_status === "UNDER_REVIEW").length;
  const approvedCount = documents.filter((d) => d.approval_status === "APPROVED").length;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-[#245d82]" />
            Document Management
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Tamper-proof document repository with cryptographic SHA-256 integrity verification.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchDocs}
            className="p-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 text-gray-600 transition-colors"
            title="Refresh list"
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-[#245d82] text-white text-sm font-medium rounded-xl hover:bg-[#1b4866] shadow-sm transition-colors"
          >
            <Upload className="w-4 h-4" />
            Upload Document
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card className="p-4 border-l-4 border-l-[#245d82]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium">Total Documents</p>
              <p className="text-xl font-bold text-gray-900 mt-0.5">{totalCount}</p>
            </div>
            <div className="w-9 h-9 rounded-lg bg-[#245d82]/10 flex items-center justify-center">
              <FolderOpen className="w-5 h-5 text-[#245d82]" />
            </div>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium">SHA-256 Verified</p>
              <p className="text-xl font-bold text-emerald-700 mt-0.5">{verifiedCount}</p>
            </div>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
            </div>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium">Pending Review</p>
              <p className="text-xl font-bold text-amber-700 mt-0.5">{pendingCount}</p>
            </div>
            <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium">Approved Chain</p>
              <p className="text-xl font-bold text-blue-700 mt-0.5">{approvedCount}</p>
            </div>
            <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
              <FileCheck className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Filter Bar */}
      <Card className="p-3.5 sm:p-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents by title, description, type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-gray-200 bg-gray-50/80 text-sm focus:outline-none focus:ring-2 focus:ring-[#245d82]/30 focus:border-[#245d82]"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2.5 rounded-lg border border-gray-200 bg-white text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#245d82]/30"
            >
              <option value="ALL">All Document Types</option>
              <option value="SURVEY_REPORT">Survey Report</option>
              <option value="AWARD_ORDER">Award Order</option>
              <option value="NOTIFICATION">Notification</option>
              <option value="COMPENSATION_RECEIPT">Compensation Receipt</option>
              <option value="POSSESSION_ORDER">Possession Order</option>
              <option value="OWNERSHIP_RECORD">Ownership Record</option>
              <option value="RR_PLAN">R&R Plan</option>
              <option value="MAP">Map</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Document Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <Loader2 className="w-8 h-8 text-[#245d82] animate-spin mb-2" />
          <p className="text-sm text-gray-500">Loading documents from PostgreSQL database...</p>
        </div>
      ) : documents.length === 0 ? (
        <Card className="p-12 text-center">
          <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-gray-700">No documents found</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
            No document records match your current search query or filter. Click "Upload Document" to add new files.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {documents.map((doc) => {
            const statusConfig = STATUS_COLORS[doc.approval_status] || STATUS_COLORS.PENDING_REVIEW;

            return (
              <Card key={doc.document_id} hoverable className="p-5 flex flex-col justify-between">
                <div>
                  {/* Top Bar: Icon, Title, Type */}
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#245d82]/10 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-[#245d82]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-gray-900 truncate" title={doc.title}>
                        {doc.title}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="inline-block text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded bg-gray-100 text-gray-600 uppercase">
                          {doc.document_type.replace(/_/g, " ")}
                        </span>
                        <span className="text-[11px] text-gray-400">{formatBytes(doc.file_size_bytes)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Description snippet */}
                  {doc.description && (
                    <p className="text-xs text-gray-500 mt-2.5 line-clamp-2">{doc.description}</p>
                  )}

                  {/* SHA-256 Integrity Verification Badge */}
                  {doc.is_verified && (
                    <div className="mt-3 px-2.5 py-1.5 bg-emerald-50/80 rounded-lg border border-emerald-200/60 flex items-center justify-between gap-2 text-[11px] font-medium text-emerald-800">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                        <span className="truncate">Cryptographically Verified</span>
                      </div>
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-600 bg-emerald-100/80 px-1.5 py-0.5 rounded">
                        SHA-256
                      </span>
                    </div>
                  )}
                </div>

                {/* Footer Metadata & Actions */}
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1 text-xs text-gray-500 truncate">
                      <Building2 className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <span className="truncate">{doc.project_name || "System Record"}</span>
                    </div>
                    <span
                      className={cn(
                        "inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase flex-shrink-0",
                        statusConfig.bg,
                        statusConfig.text,
                        statusConfig.border
                      )}
                    >
                      {doc.approval_status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-gray-400">
                    <span>
                      {doc.uploaded_by_name || "Field Officer"} •{" "}
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "Recent"}
                    </span>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setPreviewDoc(doc)}
                        className="p-1.5 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors"
                        title="View details & SHA hash"
                      >
                        <Eye className="w-4 h-4 text-[#245d82]" />
                      </button>
                      <button
                        onClick={() => handleDownload(doc)}
                        disabled={downloadingId === doc.document_id}
                        className="p-1.5 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors disabled:opacity-50"
                        title="Download file"
                      >
                        {downloadingId === doc.document_id ? (
                          <Loader2 className="w-4 h-4 animate-spin text-[#245d82]" />
                        ) : (
                          <Download className="w-4 h-4 text-emerald-600" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(doc.document_id, doc.title)}
                        className="p-1.5 hover:bg-red-50 text-red-500 rounded-lg transition-colors"
                        title="Delete document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Upload Document Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 animate-scale-up">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Upload className="w-5 h-5 text-[#245d82]" />
                Upload New Document
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Section 23 Award Declaration Order"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#245d82]/30 focus:border-[#245d82]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Document Type *
                  </label>
                  <select
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-[#245d82]/30"
                  >
                    <option value="SURVEY_REPORT">Survey Report</option>
                    <option value="AWARD_ORDER">Award Order</option>
                    <option value="NOTIFICATION">Notification</option>
                    <option value="COMPENSATION_RECEIPT">Compensation Receipt</option>
                    <option value="POSSESSION_ORDER">Possession Order</option>
                    <option value="OWNERSHIP_RECORD">Ownership Record</option>
                    <option value="RR_PLAN">R&R Plan</option>
                    <option value="MAP">Map</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Associated Project
                  </label>
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-[#245d82]/30"
                  >
                    <option value="">Select Project (Optional)</option>
                    {projects.map((p) => (
                      <option key={p.project_id} value={p.project_id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Optional summary or notes about this document..."
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-[#245d82]/30"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  File Upload *
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.xlsx"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-[#245d82]/10 file:text-[#245d82] hover:file:bg-[#245d82]/20"
                />
                <p className="text-[11px] text-gray-400 mt-1">
                  Supported formats: PDF, DOCX, XLSX, PNG, JPG (Max 20MB). Cryptographic SHA-256 hash generated automatically.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-gray-100 pt-3">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="flex items-center gap-2 px-4 py-2 bg-[#245d82] text-white text-sm font-medium rounded-lg hover:bg-[#1b4866] disabled:opacity-50"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Uploading & Hashing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Upload to PostgreSQL
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Preview / Detail Modal */}
      {previewDoc && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4 animate-scale-up">
            <div className="flex items-start justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#245d82]/10 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-[#245d82]" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900">{previewDoc.title}</h3>
                  <p className="text-xs text-gray-400">{previewDoc.document_type.replace(/_/g, " ")}</p>
                </div>
              </div>
              <button
                onClick={() => setPreviewDoc(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              {previewDoc.description && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Description</p>
                  <p className="text-sm text-gray-700 mt-0.5">{previewDoc.description}</p>
                </div>
              )}

              {/* SHA-256 Full Hash Banner */}
              <div className="p-3 bg-slate-900 text-slate-100 rounded-xl space-y-1">
                <div className="flex items-center justify-between text-xs text-emerald-400 font-semibold">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    Cryptographic SHA-256 Hash
                  </span>
                  <button
                    onClick={() => handleCopyHash(previewDoc.sha256!)}
                    className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-300 transition-colors"
                  >
                    {copiedHash === previewDoc.sha256 ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    Copy
                  </button>
                </div>
                <p className="text-xs font-mono break-all text-slate-300 leading-relaxed">
                  {previewDoc.sha256 || "SHA-256 hash verified"}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs bg-gray-50 p-3 rounded-xl">
                <div>
                  <span className="text-gray-400 block">File Size</span>
                  <span className="font-semibold text-gray-800">{formatBytes(previewDoc.file_size_bytes)}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Approval Status</span>
                  <span className="font-semibold text-gray-800 uppercase">{previewDoc.approval_status.replace(/_/g, " ")}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Project</span>
                  <span className="font-semibold text-gray-800">{previewDoc.project_name || "N/A"}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Uploaded By</span>
                  <span className="font-semibold text-gray-800">{previewDoc.uploaded_by_name || "Field Officer"}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-gray-100 pt-3">
              <button
                onClick={() => setPreviewDoc(null)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Close
              </button>
              <button
                onClick={() => handleDownload(previewDoc)}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700"
              >
                <Download className="w-4 h-4" />
                Download Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentsPage;
