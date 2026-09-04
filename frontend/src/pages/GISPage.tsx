import { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import L, { type Layer, type PathOptions } from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  Globe,
  Layers,
  X,
  MapPin,
  Search,
  ExternalLink,
} from "lucide-react";
import { fetchGISParcels } from "@/api/gis";
import { getProjects } from "@/api/projects";
import { cn } from "@/lib/utils";
import type { Parcel } from "@/types/api";

// Color parcels by status and risk
function getParcelStyle(parcel: Parcel): PathOptions {
  const base: PathOptions = { weight: 2, opacity: 0.85, fillOpacity: 0.45 };

  if (parcel.status === "COMPLETED") return { ...base, color: "#73A557", fillColor: "#73A557" };
  if (parcel.status === "BLOCKED") return { ...base, color: "#DC2626", fillColor: "#DC2626", fillOpacity: 0.6 };
  if (Number(parcel.risk_score) >= 70) return { ...base, color: "#EA580C", fillColor: "#EA580C", fillOpacity: 0.55 };
  return { ...base, color: "#D47A22", fillColor: "#D47A22" };
}

// Auto-fit map to GeoJSON bounds
function FitBounds({ geojson }: { geojson: GeoJSON.FeatureCollection }) {
  const map = useMap();
  useEffect(() => {
    if (geojson?.features && geojson.features.length > 0) {
      try {
        const layer = L.geoJSON(geojson);
        const bounds = layer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
        }
      } catch (e) {
        console.error("Failed to fit bounds", e);
      }
    }
  }, [geojson, map]);
  return null;
}

export function GISPage() {
  const navigate = useNavigate();
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const { data: projectsData } = useQuery({
    queryKey: ["projects-dropdown"],
    queryFn: () => getProjects(),
  });

  const { data: geojson, isLoading } = useQuery({
    queryKey: ["gis-parcels", selectedProjectId],
    queryFn: () => fetchGISParcels(selectedProjectId),
  });

  const projectsList = (projectsData as any)?.data || (projectsData as any)?.items || [];
  const featuresCount = (geojson as any)?.features?.length || 0;

  // Filter features if search term present
  const displayGeoJSON = useMemo(() => {
    if (!geojson?.features) return geojson;
    if (!searchTerm.trim()) return geojson;
    const term = searchTerm.toLowerCase();
    const filteredFeatures = geojson.features.filter((f: any) => {
      const p = f.properties || {};
      return (
        String(p.survey_number || "").toLowerCase().includes(term) ||
        String(p.owner_name || "").toLowerCase().includes(term) ||
        String(p.village || "").toLowerCase().includes(term)
      );
    });
    return {
      ...geojson,
      features: filteredFeatures,
    };
  }, [geojson, searchTerm]);

  const onEachFeature = (feature: GeoJSON.Feature, layer: Layer) => {
    const parcel = feature.properties as Parcel;
    layer.on({
      click: () => setSelectedParcel(parcel),
      mouseover: (e) => {
        const target = e.target;
        target.setStyle({ fillOpacity: 0.75, weight: 3 });
      },
      mouseout: (e) => {
        const target = e.target;
        target.setStyle(getParcelStyle(parcel));
      },
    });
  };

  const mapKey = `${(geojson as any)?.project_id || selectedProjectId}-${featuresCount}`;

  return (
    <div className="animate-fade-in -m-6 flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* ── Map Viewport ─────────────────────── */}
      <div className="flex-1 relative">
        {/* Floating Top Controls Overlay */}
        <div className="absolute top-4 left-4 z-[1000] flex flex-wrap items-center gap-2 max-w-[calc(100%-2rem)]">
          <div className="bg-white/95 backdrop-blur-md rounded-xl px-4 py-2 shadow-lg border border-gray-200 flex items-center gap-3">
            <h1 className="text-xs font-bold text-foreground flex items-center gap-2 whitespace-nowrap">
              <Globe className="w-4 h-4 text-brand-teal-blue" />
              GIS Command Center
            </h1>

            {/* Project Selector */}
            <select
              value={selectedProjectId}
              onChange={(e) => {
                setSelectedProjectId(e.target.value);
                setSelectedParcel(null);
                setSearchTerm("");
              }}
              className="text-xs bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-gray-800 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30 focus:border-brand-teal-blue"
            >
              <option value="all">All Projects (Portfolio Overview)</option>
              {projectsList.map((p: any) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.name}
                </option>
              ))}
            </select>

            {/* Feature count badge */}
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-teal-blue/10 text-brand-teal-blue border border-brand-teal-blue/20 whitespace-nowrap">
              {featuresCount} Parcels Mapped
            </span>
          </div>

          {/* Quick Search */}
          <div className="bg-white/95 backdrop-blur-md rounded-xl px-3 py-1.5 shadow-lg border border-gray-200 flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
            <input
              type="text"
              placeholder="Find parcel # or owner..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="text-xs bg-transparent outline-none text-gray-800 placeholder:text-gray-400 w-36 sm:w-48"
            />
            {searchTerm && (
              <button onClick={() => setSearchTerm("")} className="text-gray-400 hover:text-gray-600">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 z-[1000] bg-white/90 backdrop-blur-md rounded-xl p-3.5 shadow-lg border border-gray-200">
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            Cadastral Legend
          </p>
          <div className="space-y-1.5">
            {[
              { color: "bg-brand-teal-blue", label: "In Progress" },
              { color: "bg-[#73A557]", label: "Possession Completed" },
              { color: "bg-[#D47A22]", label: "High Risk (Score ≥ 70)" },
              { color: "bg-[#DC2626]", label: "Blocked / Injunction" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div className={cn("w-3 h-3 rounded-sm", item.color)} />
                <span className="text-[11px] font-medium text-gray-700">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="w-full h-full bg-gray-100 flex items-center justify-center">
            <div className="flex flex-col items-center gap-2 text-gray-500">
              <Layers className="w-7 h-7 animate-spin text-brand-teal-blue" />
              <span className="text-sm font-semibold">Loading spatial polygon datasets…</span>
            </div>
          </div>
        ) : (
          <MapContainer
            center={[27.2, 79.8]}
            zoom={7}
            style={{ width: "100%", height: "100%" }}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {displayGeoJSON && (
              <>
                <FitBounds geojson={displayGeoJSON as unknown as GeoJSON.FeatureCollection} />
                <GeoJSON
                  key={mapKey}
                  data={displayGeoJSON as unknown as GeoJSON.FeatureCollection}
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

      {/* ── Right Panel — Selected Parcel Inspector ─── */}
      {selectedParcel && (
        <div className="w-[380px] bg-white border-l border-gray-200 overflow-y-auto animate-slide-in shadow-2xl z-20 flex flex-col justify-between">
          <div>
            {/* Header */}
            <div className="sticky top-0 bg-white/95 backdrop-blur-sm border-b border-gray-100 px-5 py-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-teal-blue" />
                <h2 className="text-sm font-bold text-gray-900">Cadastral Dossier</h2>
              </div>
              <button
                onClick={() => setSelectedParcel(null)}
                className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 space-y-5">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-xl font-bold text-gray-900">
                    Survey #{selectedParcel.survey_number}
                  </h3>
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded-full text-xs font-bold",
                      Number(selectedParcel.risk_score) >= 70
                        ? "bg-red-50 text-red-700 border border-red-200"
                        : Number(selectedParcel.risk_score) >= 40
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    )}
                  >
                    Risk: {Number(selectedParcel.risk_score).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                  <MapPin className="w-3.5 h-3.5 text-gray-400" />
                  <span>{selectedParcel.village}, {selectedParcel.district}, {selectedParcel.state}</span>
                </div>
              </div>

              {/* Status and Stage */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">Status</span>
                  <span className="text-xs font-bold text-gray-900 mt-0.5 block">
                    {selectedParcel.status?.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">Current Stage</span>
                  <span className="text-xs font-bold text-brand-teal-blue mt-0.5 block truncate" title={selectedParcel.current_stage}>
                    {selectedParcel.current_stage?.replace(/_/g, " ")}
                  </span>
                </div>
              </div>

              {/* Area & Owner */}
              <div className="space-y-3 bg-brand-linen/40 rounded-xl p-4 border border-gray-200/60">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500 font-medium">Acquisition Area:</span>
                  <span className="font-bold text-gray-900">{selectedParcel.area_ha} hectares</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500 font-medium">Landowner / Claimant:</span>
                  <span className="font-bold text-gray-900">{selectedParcel.owner_name || "Unassigned"}</span>
                </div>
                {selectedParcel.owner_reference && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 font-medium">UID / Reference:</span>
                    <span className="font-mono text-gray-700">{selectedParcel.owner_reference}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer Action */}
          <div className="p-4 border-t border-gray-100 bg-gray-50/50">
            <button
              onClick={() => navigate(`/parcels/${selectedParcel.parcel_id}`)}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-[#D47A22] text-white rounded-xl text-sm font-semibold hover:bg-[#B56315] shadow-sm transition-colors"
            >
              Open Complete Dossier
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default GISPage;
