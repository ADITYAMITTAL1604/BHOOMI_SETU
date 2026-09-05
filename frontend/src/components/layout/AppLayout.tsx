import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { cn } from "@/lib/utils";

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background relative">
      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-xs transition-opacity duration-200"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar (Desktop persistent + Mobile off-canvas drawer) */}
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {/* Main content area — full width on mobile, pushed right on desktop */}
      <div
        className={cn(
          "transition-all duration-300 flex flex-col min-h-screen ml-0",
          collapsed ? "lg:ml-[72px]" : "lg:ml-[270px]"
        )}
      >
        <TopBar onMobileMenuToggle={() => setMobileOpen(!mobileOpen)} />
        <main className="flex-1 p-3.5 sm:p-5 md:p-6 overflow-x-hidden overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
