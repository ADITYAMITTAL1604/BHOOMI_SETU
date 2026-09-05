import { Bell, Search, Grid3X3, LogOut, User as UserIcon, Menu } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useNavigate } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface TopBarProps {
  onMobileMenuToggle?: () => void;
}

export function TopBar({ onMobileMenuToggle }: TopBarProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [showSearch, setShowSearch] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      CENTRAL: "Central Officer",
      STATE: "State Officer",
      DISTRICT: "District Officer",
      PROJECT_AGENCY: "Project Agency",
      FIELD_OFFICER: "Field Officer",
      ADMIN: "Administrator",
    };
    return labels[role] || role;
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-3 sm:px-6 bg-white border-b border-gray-200/80">
      {/* ── Left: Hamburger (Mobile) + Search ─────────────────────── */}
      <div className="flex items-center flex-1 max-w-[200px] sm:max-w-xs md:max-w-lg">
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-2 -ml-1 mr-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-none transition-colors flex items-center justify-center flex-shrink-0"
          aria-label="Open navigation sidebar"
          title="Open navigation menu"
        >
          <Menu className="w-5 h-5 text-gray-800" />
        </button>

        <div
          className={cn(
            "flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50/80 transition-all duration-200",
            showSearch ? "w-full px-3 py-2" : "w-auto px-2.5 sm:px-3 py-2 cursor-pointer hover:bg-gray-100"
          )}
          onClick={() => !showSearch && setShowSearch(true)}
        >
          <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
          {showSearch ? (
            <input
              type="text"
              placeholder="Search parcels, projects..."
              className="flex-1 bg-transparent text-xs sm:text-sm outline-none text-gray-700 placeholder:text-gray-400 w-24 sm:w-auto"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onBlur={() => {
                if (!searchQuery) setShowSearch(false);
              }}
              autoFocus
            />
          ) : (
            <span className="text-xs sm:text-sm text-gray-400">Search...</span>
          )}
        </div>
      </div>

      {/* ── Right: Actions ───────────────────── */}
      <div className="flex items-center gap-1 sm:gap-2">
        {/* Notifications */}
        <button
          className="relative p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          title="Notifications"
          onClick={() => navigate("/alerts")}
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
        </button>

        {/* Grid Menu (hidden on small mobile) */}
        <button
          className="hidden sm:flex p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          title="Quick Menu"
        >
          <Grid3X3 className="w-5 h-5" />
        </button>

        {/* User Menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 pl-3 pr-1 py-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-gray-700">
                {user?.username || "User"}
              </p>
              <p className="text-[10px] text-gray-400">
                {user ? getRoleLabel(user.role) : ""}
              </p>
            </div>
            <div className="w-8 h-8 rounded-full bg-[#D47A22] flex items-center justify-center shadow-sm">
              <UserIcon className="w-4 h-4 text-white" />
            </div>
          </button>

          {/* Dropdown */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-100 py-1 animate-fade-in">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="text-sm font-semibold text-gray-900">
                  {user?.username}
                </p>
                <p className="text-xs text-gray-500">{user?.email}</p>
                <span className="inline-block mt-1 px-2 py-0.5 bg-amber-50 text-[#D47A22] border border-amber-200/60 text-[10px] font-semibold rounded-full uppercase">
                  {user ? getRoleLabel(user.role) : ""}
                </span>
              </div>
              {user?.state_scope && (
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="text-[10px] text-gray-400 uppercase tracking-wide">
                    Scope
                  </p>
                  <p className="text-xs text-gray-600">
                    {user.state_scope}
                    {user.district_scope && ` / ${user.district_scope}`}
                  </p>
                </div>
              )}
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
