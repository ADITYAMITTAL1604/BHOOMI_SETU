import React, { useState } from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskTooltipProps {
  score: number;
  className?: string;
  type?: "PARCEL" | "PROJECT";
}

const getRiskFactors = (score: number, type: "PARCEL" | "PROJECT") => {
  const factors = [];
  if (type === "PARCEL") {
    if (score >= 80) {
      factors.push({ label: "Severe legal dispute pending", weight: "+40%" });
      factors.push({ label: "Missing ownership records", weight: "+25%" });
      factors.push({ label: "SLA breached by >30 days", weight: "+15%" });
    } else if (score >= 60) {
      factors.push({ label: "Multiple heir dispute", weight: "+20%" });
      factors.push({ label: "Awaiting local clearance", weight: "+15%" });
      factors.push({ label: "Survey mismatch", weight: "+10%" });
    } else if (score >= 40) {
      factors.push({ label: "Minor border adjustment", weight: "+10%" });
      factors.push({ label: "Pending signature", weight: "+5%" });
    } else {
      factors.push({ label: "All clearances obtained", weight: "0%" });
      factors.push({ label: "Records verified", weight: "0%" });
    }
  } else {
    // PROJECT
    if (score >= 70) {
      factors.push({ label: "High proportion of disputed parcels", weight: "+35%" });
      factors.push({ label: "Budget allocation delays", weight: "+20%" });
    } else if (score >= 40) {
      factors.push({ label: "Some parcels pending clearance", weight: "+15%" });
      factors.push({ label: "Average processing delay", weight: "+10%" });
    } else {
      factors.push({ label: "On track with land acquisition", weight: "0%" });
    }
  }
  return factors;
};

export const RiskTooltip: React.FC<RiskTooltipProps> = ({ score, className, type = "PARCEL" }) => {
  const [show, setShow] = useState(false);
  const factors = getRiskFactors(score, type);

  return (
    <div 
      className={cn("relative inline-flex items-center", className)}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      <button className="text-gray-400 hover:text-brand-teal-blue transition-colors outline-none ml-1">
        <Info className="w-3.5 h-3.5" />
      </button>

      {show && (
        <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 bg-slate-900 border border-slate-700 shadow-xl z-50 p-3 rounded-none pointer-events-none">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-2 border-b border-slate-700 pb-1">
            Risk Score Breakdown
          </div>
          <div className="space-y-2">
            {factors.map((f, i) => (
              <div key={i} className="flex items-start justify-between text-xs">
                <span className="text-slate-200">{f.label}</span>
                <span className="text-amber-400 font-mono font-semibold ml-2 flex-shrink-0">{f.weight}</span>
              </div>
            ))}
          </div>
          {/* Arrow */}
          <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-900" />
        </div>
      )}
    </div>
  );
};
