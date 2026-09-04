import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import {
  LayoutDashboard,
  FolderKanban,
  Globe,
  Layers,
  Brain,
  FileText,
  Bell,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

interface NavItem {
  path: string;
  label: string;
  icon: React.ElementType;
  /** Roles that can see this item. If undefined, all roles see it. */
  roles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/projects", label: "Projects", icon: FolderKanban },
  { path: "/gis", label: "GIS Monitoring", icon: Globe },
  { path: "/parcels", label: "Parcels", icon: Layers },
  { path: "/intelligence", label: "Intelligence", icon: Brain },
  { path: "/documents", label: "Documents", icon: FileText },
  { path: "/alerts", label: "Alerts", icon: Bell },
  { path: "/reports", label: "Reports", icon: BarChart3 },
];

const BOTTOM_NAV: NavItem[] = [
  {
    path: "/settings",
    label: "Settings",
    icon: Settings,
    roles: ["ADMIN"],
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user } = useAuthStore();
  const location = useLocation();

  const filterByRole = (items: NavItem[]) =>
    items.filter(
      (item) =>
        !item.roles || (user && item.roles.includes(user.role))
    );

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen flex flex-col transition-all duration-300 ease-in-out shadow-2xl",
        "bg-[#D47A22] text-white",
        collapsed ? "w-[72px]" : "w-[248px]"
      )}
      style={{ backgroundColor: "#D47A22" }}
    >
      {/* ── Logo ─────────────────────────────── */}
      <div className="px-3.5 py-4 border-b border-white/20">
        {collapsed ? (
          <div className="w-12 h-12 mx-auto rounded-xl overflow-hidden bg-white p-1 shadow-md border border-white/20 flex items-center justify-center">
            <img
              src="/logo-bhoomisetu.jpeg"
              alt="BhoomiSetu"
              className="w-full h-full object-contain"
            />
          </div>
        ) : (
          <div className="w-full bg-white rounded-xl py-2 px-3 shadow-md border border-white/20 flex items-center justify-center transition-transform hover:scale-[1.01]">
            <img
              src="/logo-bhoomisetu.jpeg"
              alt="BhoomiSetu"
              className="w-full h-14 max-w-[215px] object-contain"
            />
          </div>
        )}
      </div>

      {/* ── Main Navigation ──────────────────── */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        {filterByRole(NAV_ITEMS).map((item) => {
          const Icon = item.icon;
          const isActive =
            location.pathname === item.path ||
            location.pathname.startsWith(item.path + "/");

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-[#A3540C] text-white shadow-sm font-semibold border-l-[3px] border-amber-200 ml-0 pl-[9px]"
                  : "text-orange-100/90 hover:text-white hover:bg-[#BD6815] border-l-[3px] border-transparent"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  "w-[18px] h-[18px] flex-shrink-0",
                  isActive ? "text-amber-200" : "text-orange-200/90"
                )}
              />
              {!collapsed && (
                <span className="animate-fade-in truncate">{item.label}</span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* ── Bottom Navigation ────────────────── */}
      <div className="py-3 px-2 border-t border-white/20">
        {filterByRole(BOTTOM_NAV).map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-[#A3540C] text-white font-semibold border-l-[3px] border-amber-200 pl-[9px]"
                  : "text-orange-100/90 hover:text-white hover:bg-[#BD6815] border-l-[3px] border-transparent"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-[18px] h-[18px] flex-shrink-0 text-orange-200/90" />
              {!collapsed && (
                <span className="animate-fade-in truncate">{item.label}</span>
              )}
            </NavLink>
          );
        })}

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium w-full
                     text-orange-100/90 hover:text-white hover:bg-[#BD6815] transition-all duration-200 mt-1"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="w-[18px] h-[18px] flex-shrink-0" />
          ) : (
            <>
              <ChevronLeft className="w-[18px] h-[18px] flex-shrink-0" />
              <span className="animate-fade-in">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
