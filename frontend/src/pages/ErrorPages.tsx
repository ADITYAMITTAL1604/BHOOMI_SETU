import { Link, useLocation } from "react-router-dom";
import { ShieldAlert, Home } from "lucide-react";

export function UnauthorizedPage() {
  const location = useLocation();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <div className="text-center max-w-md animate-fade-in">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-50 mb-6">
          <ShieldAlert className="w-8 h-8 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-foreground mb-2">
          Access Denied
        </h1>
        <p className="text-sm text-muted-foreground mb-6">
          You do not have permission to access{" "}
          <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono">
            {location.pathname}
          </code>
          . Contact your administrator if you believe this is an error.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-teal-blue text-white text-sm font-medium rounded-xl hover:bg-[#245d82] transition-colors"
        >
          <Home className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <div className="text-center max-w-md animate-fade-in">
        <h1 className="text-7xl font-black text-brand-teal-blue/20 mb-4">
          404
        </h1>
        <h2 className="text-xl font-bold text-foreground mb-2">
          Page Not Found
        </h2>
        <p className="text-sm text-muted-foreground mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-teal-blue text-white text-sm font-medium rounded-xl hover:bg-[#245d82] transition-colors"
        >
          <Home className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
