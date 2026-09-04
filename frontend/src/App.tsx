import { Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { UnauthorizedPage, NotFoundPage } from "@/pages/ErrorPages";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import LoginPage from "@/pages/LoginPage";

// Lazy-loaded secondary pages for code splitting with named export handling
const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage || (m as any).default }))
);
const ProjectListPage = lazy(() =>
  import("@/pages/ProjectListPage").then((m) => ({ default: m.ProjectListPage || (m as any).default }))
);
const ProjectDetailPage = lazy(() =>
  import("@/pages/ProjectDetailPage").then((m) => ({ default: m.ProjectDetailPage || (m as any).default }))
);
const ParcelDetailPage = lazy(() =>
  import("@/pages/ParcelDetailPage").then((m) => ({ default: m.ParcelDetailPage || (m as any).default }))
);
const GISPage = lazy(() =>
  import("@/pages/GISPage").then((m) => ({ default: m.GISPage || (m as any).default }))
);
const AlertsPage = lazy(() =>
  import("@/pages/AlertsPage").then((m) => ({ default: m.AlertsPage || (m as any).default }))
);
const DocumentsPage = lazy(() =>
  import("@/pages/DocumentsPage").then((m) => ({ default: m.DocumentsPage || (m as any).default }))
);
const IntelligencePage = lazy(() =>
  import("@/pages/IntelligencePage").then((m) => ({ default: m.IntelligencePage || (m as any).default }))
);

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-brand-teal-blue/30 border-t-brand-teal-blue rounded-full animate-spin" />
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
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
            <Route path="/parcels" element={<Navigate to="/projects" replace />} />
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
    </ErrorBoundary>
  );
}
