import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import type { Layer, PathOptions } from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  Globe,
  Layers,
  X,
  MapPin,
  User,
  Clock,
  AlertTriangle,
  ChevronRight,
} from "lucide-react";
import { fetchGISParcels } from "@/api/gis";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import type { Parcel } from "@/types/api";

// Color parcels by status
function getParcelStyle(parcel: Parcel): PathOptions {
  const base: PathOptions = { weight: 2, opacity: 0.8, fillOpacity: 0.4 };

  if (parcel.status === "COMPLETED") return { ...base, color: "#73A557", fillColor: "#73A557" };
  if (parcel.status === "BLOCKED") return { ...base, color: "#DC2626", fillColor: "#DC2626", fillOpacity: 0.5 };
  if (parcel.risk_score >= 60) return { ...base, color: "#D47A22", fillColor: "#D47A22" };
  return { ...base, color: "#2B6D97", fillColor: "#2B6D97" };
}

// Auto-fit map to GeoJSON bounds
function FitBounds({ geojson }: { geojson: GeoJSON.FeatureCollection }) {
  const map = useMap();
  useMemo(() => {
    if (geojson.features.length > 0) {
      import("leaflet").then((L) => {
        const layer = L.geoJSON(geojson);
        const bounds = layer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [50, 50] });
        }
      });
    }
  }, [geojson, map]);
  return null;
}

export function GISPage() {
  const navigate = useNavigate();
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);

  const { data: geojson, isLoading } = useQuery({
    queryKey: ["gis-parcels"],
    queryFn: () => fetchGISParcels(),
  });

  const onEachFeature = (feature: GeoJSON.Feature, layer: Layer) => {
    const parcel = feature.properties as Parcel;
    layer.on({
      click: () => setSelectedParcel(parcel),
      mouseover: (e) => {
        const target = e.target;
        target.setStyle({ fillOpacity: 0.7, weight: 3 });
      },
      mouseout: (e) => {
        const target = e.target;
        target.setStyle(getParcelStyle(parcel));
      },
    });
  };

  return (
    <div className="animate-fade-in -m-6 flex h-[calc(100vh-4rem)]">
      {/* ── Map ──────────────────────────────── */}
      <div className="flex-1 relative">
        {/* Header overlay */}
        <div className="absolute top-4 left-4 z-[1000] bg-white/90 backdrop-blur-md rounded-xl px-4 py-2.5 shadow-lg border border-gray-100">
          <h1 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Globe className="w-4 h-4 text-brand-teal-blue" />
            GIS Monitoring Center
          </h1>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 z-[1000] bg-white/90 backdrop-blur-md rounded-xl p-3 shadow-lg border border-gray-100">
          <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Parcel Status
          </p>
          <div className="space-y-1.5">
            {[
              { color: "bg-brand-teal-blue", label: "In Progress" },
              { color: "bg-brand-sage-green", label: "Completed" },
              { color: "bg-brand-copper", label: "High Risk" },
              { color: "bg-red-500", label: "Blocked" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div className={cn("w-3 h-3 rounded-sm", item.color)} />
                <span className="text-[11px] text-gray-600">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="w-full h-full bg-gray-100 flex items-center justify-center">
            <div className="flex items-center gap-2 text-gray-400">
              <Layers className="w-5 h-5 animate-spin" />
              <span className="text-sm">Loading map data...</span>
            </div>
          </div>
        ) : (
          <MapContainer
            center={[18.58, 73.75]}
            zoom={13}
            style={{ width: "100%", height: "100%" }}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {geojson && (
              <>
                <FitBounds geojson={geojson as unknown as GeoJSON.FeatureCollection} />
                <GeoJSON
                  key={JSON.stringify(geojson)}
                  data={geojson as unknown as GeoJSON.FeatureCollection}
                  style={(feature) => {
                    const parcel = feature?.properties as Parcel;
                    return getParcelStyle(parcel);
                  }}
                  onEachFeature={onEachFeature}
                />
              </>
            )}
          </MapContainer>
        )}
      </div>

      {/* ── Right Panel — Selected Parcel ─── */}
      {selectedParcel && (
        <div className="w-[380px] bg-white border-l border-gray-200 overflow-y-auto animate-slide-in">
          {/* Panel Header */}
          <div className="sticky top-0 bg-white border-b border-gray-100 px-5 py-4 flex items-center justify-between z-10">
            <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand-teal-blue" />
              Parcel Details
            </h2>
            <button
              onClick={() => setSelectedParcel(null)}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          <div className="p-5 space-y-5">
            {/* Survey Info */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-bold text-foreground">
                  {selectedParcel.survey_number}
                </h3>
                <Badge variant="risk" level={
                  selectedParcel.risk_score >= 70 ? "HIGH" :
                  selectedParcel.risk_score >= 40 ? "MEDIUM" : "LOW"
                }>
                  Risk: {selectedParcel.risk_score}
                </Badge>
              </div>
              <p className="text-xs text-gray-400 font-mono">
                ID: {selectedParcel.parcel_id}
              </p>
            </div>

            {/* Location */}
            <div className="bg-gray-50 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin className="w-4 h-4 text-gray-400" />
                <span>
                  {selectedParcel.village}, {selectedParcel.district},{" "}
                  {selectedParcel.state}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <User className="w-4 h-4 text-gray-400" />
                <span>Owner: {selectedParcel.owner_name}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Layers className="w-4 h-4 text-gray-400" />
                <span>Area: {selectedParcel.area_ha} HA</span>
              </div>
            </div>

            {/* Current Stage */}
            <div className="bg-brand-teal-blue/5 rounded-xl p-4">
              <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
                Current Stage
              </p>
              <p className="text-sm font-bold text-brand-teal-blue">
                {selectedParcel.current_stage.replace(/_/g, " ")}
              </p>
              <Badge variant="status" level={selectedParcel.status} className="mt-2">
                {selectedParcel.status.replace(/_/g, " ")}
              </Badge>
            </div>

            {/* Days Pending */}
            {selectedParcel.days_pending > 0 && (
              <div className={cn(
                "rounded-xl p-4 flex items-center gap-3",
                selectedParcel.days_pending > 30 ? "bg-red-50" : "bg-amber-50"
              )}>
                <Clock className={cn(
                  "w-5 h-5",
                  selectedParcel.days_pending > 30 ? "text-red-500" : "text-amber-500"
                )} />
                <div>
                  <p className="text-sm font-semibold text-gray-800">
                    {selectedParcel.days_pending} Days Pending
                  </p>
                  {selectedParcel.days_pending > 30 && (
                    <p className="text-xs text-red-600 flex items-center gap-1 mt-0.5">
                      <AlertTriangle className="w-3 h-3" />
                      SLA Breach Warning
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Assigned Officer */}
            {selectedParcel.assigned_officer && (
              <div className="border border-gray-100 rounded-xl p-4">
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
                  Assigned Officer
                </p>
                <p className="text-sm font-medium text-gray-800">
                  {selectedParcel.assigned_officer}
                </p>
              </div>
            )}

            {/* Action Button */}
            <button
              onClick={() => navigate(`/parcels/${selectedParcel.parcel_id}`)}
              className="w-full flex items-center justify-center gap-2 py-3 bg-brand-teal-blue text-white text-sm font-medium rounded-xl hover:bg-[#245d82] transition-colors"
            >
              View Full Details
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
