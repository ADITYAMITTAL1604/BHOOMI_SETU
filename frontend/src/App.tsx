import { Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { UnauthorizedPage, NotFoundPage } from "@/pages/ErrorPages";

// Lazy-loaded pages for code splitting
const LoginPage = lazy(() =>
  import("@/pages/LoginPage").then((m) => ({ default: m.default ?? m.LoginPage ?? Object.values(m)[0] }))
);
const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.default ?? m.DashboardPage ?? Object.values(m)[0] }))
);
const ProjectListPage = lazy(() =>
  import("@/pages/ProjectListPage").then((m) => ({ default: m.default ?? m.ProjectListPage ?? Object.values(m)[0] }))
);
const ProjectDetailPage = lazy(() =>
  import("@/pages/ProjectDetailPage").then((m) => ({ default: m.default ?? m.ProjectDetailPage ?? Object.values(m)[0] }))
);
const ParcelDetailPage = lazy(() =>
  import("@/pages/ParcelDetailPage").then((m) => ({ default: m.default ?? m.ParcelDetailPage ?? Object.values(m)[0] }))
);
const GISPage = lazy(() =>
  import("@/pages/GISPage").then((m) => ({ default: m.default ?? m.GISPage ?? Object.values(m)[0] }))
);
const AlertsPage = lazy(() =>
  import("@/pages/AlertsPage").then((m) => ({ default: m.default ?? m.AlertsPage ?? Object.values(m)[0] }))
);
const DocumentsPage = lazy(() =>
  import("@/pages/DocumentsPage").then((m) => ({ default: m.default ?? m.DocumentsPage ?? Object.values(m)[0] }))
);
const IntelligencePage = lazy(() =>
  import("@/pages/IntelligencePage").then((m) => ({ default: m.default ?? m.IntelligencePage ?? Object.values(m)[0] }))
);

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-3 border-brand-teal-blue/30 border-t-brand-teal-blue rounded-full animate-spin" />
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected — wrapped in AuthGuard + AppLayout */}
        <Route
          element={
            <AuthGuard>
              <AppLayout />
            </AuthGuard>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectListPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/parcels/:parcelId" element={<ParcelDetailPage />} />
          <Route path="/gis" element={<GISPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/intelligence" element={<IntelligencePage />} />
        </Route>

        {/* Error routes */}
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        {/* Redirects */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
