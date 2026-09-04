import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught runtime error in React component tree:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-brand-linen p-6">
          <div className="max-w-md w-full bg-white rounded-2xl p-8 shadow-sm border border-gray-200 text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 mb-4">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-sm text-gray-600 mb-6">
              {this.state.error?.message || "An unexpected error occurred while rendering the page."}
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => {
                  try {
                    localStorage.removeItem("bhoomisetu-auth");
                  } catch {}
                  window.location.href = "/login";
                }}
                className="px-5 py-2.5 text-sm font-medium bg-brand-teal-blue text-white rounded-xl hover:bg-[#245d82] flex items-center gap-2 shadow-sm transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Reset Session & Reload
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
