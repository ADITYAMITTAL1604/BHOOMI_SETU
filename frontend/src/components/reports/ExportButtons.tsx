import { useState } from "react";
import { Printer, Download, FileSpreadsheet, Loader2 } from "lucide-react";
import apiClient from "@/api/client";
import type { FilterState } from "./AdvancedFilters";

interface ExportButtonsProps {
  filters: FilterState;
  onPrint?: () => void;
  className?: string;
}

async function downloadBlob(url: string, filename: string) {
  const response = await apiClient.get(url, { responseType: "blob" });
  const blob = new Blob([response.data]);
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}

export function ExportButtons({ filters, onPrint, className = "" }: ExportButtonsProps) {
  const [downloadingHtml, setDownloadingHtml] = useState(false);
  const [downloadingCsv, setDownloadingCsv] = useState(false);

  const handlePrint = () => {
    if (onPrint) {
      onPrint();
    } else {
      window.print();
    }
  };

  const handleDownloadHtml = async () => {
    setDownloadingHtml(true);
    try {
      const params = new URLSearchParams({ format: "html" });
      if (filters.projectId) params.append("project_id", filters.projectId);
      await downloadBlob(
        `/reports/executive-summary?${params.toString()}`,
        `bhoomisetu_executive_summary.html`
      );
    } catch (err) {
      console.error("HTML download failed:", err);
    } finally {
      setDownloadingHtml(false);
    }
  };

  const handleDownloadCsv = async () => {
    setDownloadingCsv(true);
    try {
      const params = new URLSearchParams();
      if (filters.state) params.append("state", filters.state);
      if (filters.district) params.append("district", filters.district);
      if (filters.projectId) params.append("project_id", filters.projectId);
      if (filters.stage) params.append("stage", filters.stage);
      if (filters.status) params.append("status", filters.status);
      await downloadBlob(
        `/reports/export/excel?${params.toString()}`,
        `bhoomisetu_report.csv`
      );
    } catch (err) {
      console.error("CSV download failed:", err);
    } finally {
      setDownloadingCsv(false);
    }
  };

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      {/* Print Report */}
      <button
        type="button"
        onClick={handlePrint}
        className="inline-flex items-center gap-2 px-3.5 py-2 rounded-none border border-gray-300 bg-white text-xs font-bold uppercase tracking-wider text-gray-700 hover:bg-gray-50 shadow-none transition-colors"
        title="Print this executive report or save as PDF"
      >
        <Printer className="w-3.5 h-3.5 text-gray-500" />
        Print Report
      </button>

      {/* Download Official HTML Summary — Authenticated */}
      <button
        type="button"
        onClick={handleDownloadHtml}
        disabled={downloadingHtml}
        className="inline-flex items-center gap-2 px-3.5 py-2 rounded-none bg-[#D47A22] text-white text-xs font-bold uppercase tracking-wider hover:bg-[#B56315] shadow-none transition-colors disabled:opacity-60"
        title="Download official executive summary document"
      >
        {downloadingHtml ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Download className="w-3.5 h-3.5" />
        )}
        Download HTML
      </button>

      {/* Export Filtered CSV / Excel — Authenticated */}
      <button
        type="button"
        onClick={handleDownloadCsv}
        disabled={downloadingCsv}
        className="inline-flex items-center gap-2 px-3.5 py-2 rounded-none bg-emerald-700 text-white text-xs font-bold uppercase tracking-wider hover:bg-emerald-800 shadow-none transition-colors disabled:opacity-60"
        title="Export full parcel dataset as Excel-compatible CSV"
      >
        {downloadingCsv ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <FileSpreadsheet className="w-3.5 h-3.5" />
        )}
        Export CSV (Excel)
      </button>
    </div>
  );
}
