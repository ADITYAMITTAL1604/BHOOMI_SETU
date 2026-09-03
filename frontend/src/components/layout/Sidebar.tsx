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
        "fixed left-0 top-0 z-40 h-screen flex flex-col transition-all duration-300 ease-in-out shadow-sidebar",
        "bg-sidebar text-sidebar-text",
        collapsed ? "w-[72px]" : "w-[248px]"
      )}
    >
      {/* ── Logo ─────────────────────────────── */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
        <div className="w-9 h-9 rounded-lg bg-white/15 flex items-center justify-center flex-shrink-0">
          <Globe className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <h1 className="text-base font-bold leading-tight tracking-tight">
              BhoomiSetu
            </h1>
            <p className="text-[10px] font-medium text-sidebar-text-muted uppercase tracking-widest">
              Command Center
            </p>
          </div>
        )}
      </div>

      {/* ── Main Navigation ──────────────────── */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
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
                "hover:bg-sidebar-hover",
                isActive
                  ? "bg-sidebar-active text-white shadow-sm border-l-[3px] border-white ml-0 pl-[9px]"
                  : "text-sidebar-text-muted hover:text-white border-l-[3px] border-transparent"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  "w-[18px] h-[18px] flex-shrink-0",
                  isActive ? "text-white" : "text-sidebar-text-muted"
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
      <div className="py-3 px-2 border-t border-white/10">
        {filterByRole(BOTTOM_NAV).map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                "hover:bg-sidebar-hover",
                isActive
                  ? "bg-sidebar-active text-white"
                  : "text-sidebar-text-muted hover:text-white"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-[18px] h-[18px] flex-shrink-0" />
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
                     text-sidebar-text-muted hover:text-white hover:bg-sidebar-hover transition-all duration-200 mt-1"
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
