import { useState } from "react";
import { FileText, Search, Upload, Download, Eye, Filter } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

interface DocItem {
  id: string;
  filename: string;
  type: string;
  entity: string;
  uploaded_by: string;
  date: string;
  size: string;
  status: "VERIFIED" | "PENDING" | "REJECTED";
}

const MOCK_DOCS: DocItem[] = [
  { id: "d1", filename: "Joint_Measurement_Report_SN145A.pdf", type: "SURVEY_REPORT", entity: "Parcel SN-145/A", uploaded_by: "Rahul Sharma", date: "Aug 28, 2025", size: "2.4 MB", status: "VERIFIED" },
  { id: "d2", filename: "Ownership_Record_7_12_SN146B.pdf", type: "OWNERSHIP_RECORD", entity: "Parcel SN-146/B", uploaded_by: "Suresh Jadhav", date: "Aug 15, 2025", size: "1.2 MB", status: "VERIFIED" },
  { id: "d3", filename: "Section_3A_Notification.pdf", type: "NOTIFICATION", entity: "NHAI Bharatmala II", uploaded_by: "Collector Office", date: "Jul 20, 2025", size: "3.1 MB", status: "VERIFIED" },
  { id: "d4", filename: "Award_Order_SN201.pdf", type: "AWARD_ORDER", entity: "Parcel SN-201", uploaded_by: "District Admin", date: "Jun 15, 2025", size: "890 KB", status: "VERIFIED" },
  { id: "d5", filename: "Compensation_Receipt_SN310C.pdf", type: "COMPENSATION_RECEIPT", entity: "Parcel SN-310/C", uploaded_by: "Treasury", date: "Aug 29, 2025", size: "540 KB", status: "PENDING" },
  { id: "d6", filename: "RR_Plan_Bharatmala.pdf", type: "RR_PLAN", entity: "NHAI Bharatmala II", uploaded_by: "Social Welfare", date: "Aug 10, 2025", size: "5.8 MB", status: "PENDING" },
];

const STATUS_COLORS: Record<string, string> = {
  VERIFIED: "bg-emerald-100 text-emerald-800",
  PENDING: "bg-amber-100 text-amber-800",
  REJECTED: "bg-red-100 text-red-800",
};

export function DocumentsPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");

  const filtered = MOCK_DOCS.filter((d) => {
    if (search && !d.filename.toLowerCase().includes(search.toLowerCase()) && !d.entity.toLowerCase().includes(search.toLowerCase())) return false;
    if (typeFilter !== "ALL" && d.type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-brand-teal-blue" />
            Document Management
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Tamper-proof document storage with SHA-256 verification.
          </p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-teal-blue text-white text-sm font-medium rounded-xl hover:bg-[#245d82] transition-colors">
          <Upload className="w-4 h-4" />
          Upload Document
        </button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-gray-200 bg-gray-50/80 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30 focus:border-brand-teal-blue"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2.5 rounded-lg border border-gray-200 bg-white text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30"
            >
              <option value="ALL">All Types</option>
              <option value="SURVEY_REPORT">Survey Report</option>
              <option value="OWNERSHIP_RECORD">Ownership Record</option>
              <option value="NOTIFICATION">Notification</option>
              <option value="AWARD_ORDER">Award Order</option>
              <option value="COMPENSATION_RECEIPT">Compensation Receipt</option>
              <option value="RR_PLAN">R&R Plan</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Document Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((doc) => (
          <Card key={doc.id} hoverable className="p-5">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-teal-blue/10 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-brand-teal-blue" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-800 truncate" title={doc.filename}>
                  {doc.filename}
                </p>
                <p className="text-[10px] text-gray-400 mt-0.5">
                  {doc.type.replace(/_/g, " ")} • {doc.size}
                </p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">{doc.entity}</span>
                <span className={cn("inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase", STATUS_COLORS[doc.status])}>
                  {doc.status}
                </span>
              </div>
              <div className="flex items-center justify-between text-[10px] text-gray-400">
                <span>By {doc.uploaded_by} • {doc.date}</span>
                <div className="flex items-center gap-2">
                  <button className="p-1 hover:text-brand-teal-blue transition-colors" title="Preview">
                    <Eye className="w-3.5 h-3.5" />
                  </button>
                  <button className="p-1 hover:text-brand-teal-blue transition-colors" title="Download">
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
