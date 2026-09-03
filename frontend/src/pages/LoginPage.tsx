import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { login } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";
import {
  User,
  Lock,
  Eye,
  EyeOff,
  LogIn,
  ShieldCheck,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth, isAuthenticated } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already authenticated
  if (isAuthenticated) {
    navigate("/dashboard", { replace: true });
    return null;
  }

  const from = (location.state as { from?: { pathname: string } })?.from
    ?.pathname || "/dashboard";

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await login(data);
      setAuth(response.user, response.access_token, response.refresh_token);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: { detail?: { message?: string } } };
      };
      setError(
        axiosErr?.response?.data?.detail?.message ||
          "Invalid credentials. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left Panel — Hero ────────────────────── */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden bg-brand-teal-blue">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-[0.08]">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `
                radial-gradient(circle at 25% 25%, rgba(255,255,255,0.3) 1px, transparent 1px),
                radial-gradient(circle at 75% 75%, rgba(255,255,255,0.2) 1px, transparent 1px)
              `,
              backgroundSize: "40px 40px",
            }}
          />
        </div>

        {/* Decorative geometric shapes */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] opacity-[0.07]">
          <div className="absolute inset-0 border-[3px] border-white rotate-45 rounded-3xl" />
          <div className="absolute inset-8 border-[3px] border-white rotate-45 rounded-3xl" />
          <div className="absolute inset-16 border-[3px] border-white rotate-45 rounded-3xl" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <div className="flex-1 flex flex-col justify-center max-w-lg">
            <h2 className="text-4xl xl:text-5xl font-bold leading-tight mb-6">
              National Land
              <br />
              Acquisition
              <br />
              Command
            </h2>
            <p className="text-lg text-white/70 leading-relaxed">
              Secure, centralized operational control for critical infrastructure
              and parcel monitoring workflows.
            </p>
          </div>

          <div className="flex items-center gap-3 pt-8 border-t border-white/15">
            <ShieldCheck className="w-5 h-5 text-white/60" />
            <span className="text-xs font-semibold text-white/60 uppercase tracking-widest">
              Gov-Grade Encryption Enabled
            </span>
          </div>
        </div>
      </div>

      {/* ── Right Panel — Login Form ─────────────── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-brand-linen">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-teal-blue/10 mb-4">
              <span className="text-2xl font-black text-brand-teal-blue tracking-tight">
                BS
              </span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Sign In to Dashboard
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Enter your official credentials to access the command center.
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-6 flex items-center gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 animate-fade-in">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Username */}
            <div>
              <label
                htmlFor="login-username"
                className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1.5"
              >
                Username or ID
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  id="login-username"
                  type="text"
                  placeholder="e.g. administrator"
                  className={cn(
                    "w-full pl-10 pr-4 py-3 rounded-xl border bg-white text-sm transition-all duration-200",
                    "focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30 focus:border-brand-teal-blue",
                    errors.username
                      ? "border-red-300 focus:ring-red-200 focus:border-red-400"
                      : "border-gray-200 hover:border-gray-300"
                  )}
                  {...register("username")}
                  autoComplete="username"
                  autoFocus
                />
              </div>
              {errors.username && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.username.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="login-password"
                className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1.5"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className={cn(
                    "w-full pl-10 pr-12 py-3 rounded-xl border bg-white text-sm transition-all duration-200",
                    "focus:outline-none focus:ring-2 focus:ring-brand-teal-blue/30 focus:border-brand-teal-blue",
                    errors.password
                      ? "border-red-300 focus:ring-red-200 focus:border-red-400"
                      : "border-gray-200 hover:border-gray-300"
                  )}
                  {...register("password")}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Forgot Password */}
            <div className="text-right">
              <button
                type="button"
                className="text-xs font-semibold text-brand-teal-blue hover:text-brand-sea-green transition-colors"
              >
                Forgot Password?
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "w-full flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200",
                "bg-brand-teal-blue hover:bg-[#245d82] active:scale-[0.98]",
                "disabled:opacity-60 disabled:cursor-not-allowed disabled:active:scale-100"
              )}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Sign In
                  <LogIn className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-10 text-center">
            <div className="inline-flex items-center gap-1.5 mb-2">
              <div className="w-8 h-px bg-gray-300" />
              <span className="text-[10px] text-gray-400 uppercase tracking-widest font-medium">
                Digital India Initiative
              </span>
              <div className="w-8 h-px bg-gray-300" />
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              Unauthorized access is prohibited. All activity is logged
              and monitored.
            </p>
          </div>

          {/* Demo Credentials (dev only) */}
          {import.meta.env.VITE_USE_MOCKS === "true" && (
            <div className="mt-6 p-4 bg-brand-sea-green/5 border border-brand-sea-green/20 rounded-xl">
              <p className="text-[10px] text-brand-sea-green font-semibold uppercase tracking-wide mb-2">
                Demo Credentials
              </p>
              <div className="space-y-1 text-xs text-gray-600 font-mono">
                <p>admin / Admin@123</p>
                <p>central_officer / Central@123</p>
                <p>up_state_officer / State@123</p>
                <p>gbn_district_officer / District@123</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
