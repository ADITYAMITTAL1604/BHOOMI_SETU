import { useState, useEffect } from "react";
import { useNavigate, useLocation, Navigate } from "react-router-dom";
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

interface DemoPersona {
  user: string;
  roleBadge: string;
  label: string;
  sublabel: string;
  desc: string;
  category: "national" | "state" | "district" | "field";
}

const ALL_DEMO_PERSONAS: DemoPersona[] = [
  {
    user: "admin",
    roleBadge: "ADMIN",
    label: "Administrator",
    sublabel: "National Executive Command",
    desc: "Full portfolio oversight · 12 projects, 2,400 parcels, all 5 states",
    category: "national",
  },
  {
    user: "central_user",
    roleBadge: "CENTRAL",
    label: "Central Authority",
    sublabel: "Ministry of Road Transport & Highways",
    desc: "Statutory approvals, inter-state corridors & DBT budget releases",
    category: "national",
  },
  {
    user: "state_user",
    roleBadge: "STATE OFFICER",
    label: "State Officer (UP)",
    sublabel: "Uttar Pradesh State Headquarters",
    desc: "UP jurisdiction · WDFC, Delhi-Mumbai corridor & state highways",
    category: "state",
  },
  {
    user: "delhi_state",
    roleBadge: "STATE OFFICER",
    label: "State Officer (Delhi)",
    sublabel: "Delhi State Headquarters",
    desc: "Delhi Metro Phase-IV, Delhi-Meerut RRTS corridor jurisdiction",
    category: "state",
  },
  {
    user: "punjab_state",
    roleBadge: "STATE OFFICER",
    label: "State Officer (Punjab)",
    sublabel: "Punjab State Headquarters",
    desc: "Amritsar-Jamnagar Expressway & Punjab Freight Corridor",
    category: "state",
  },
  {
    user: "district_user",
    roleBadge: "DISTRICT",
    label: "Collector / DLAO (Ghaziabad)",
    sublabel: "District Land Acquisition Office",
    desc: "Sec 19 statutory declarations, award calculations & hearings",
    category: "district",
  },
  {
    user: "delhi_district",
    roleBadge: "DISTRICT",
    label: "Collector / DLAO (South Delhi)",
    sublabel: "South Delhi Revenue District",
    desc: "Metro Phase-IV and Urban Extension Road-II acquisitions",
    category: "district",
  },
  {
    user: "punjab_district",
    roleBadge: "DISTRICT",
    label: "Collector / DLAO (Amritsar)",
    sublabel: "Amritsar Revenue District",
    desc: "Expressway land possession, disbursement clearances & awards",
    category: "district",
  },
  {
    user: "agency_user",
    roleBadge: "AGENCY",
    label: "Project Agency (NHAI)",
    sublabel: "National Highways Authority of India",
    desc: "Project proposals, alignment plans & requisition submissions",
    category: "field",
  },
  {
    user: "field_officer",
    roleBadge: "FIELD OFFICER",
    label: "Field Survey Officer",
    sublabel: "Ghaziabad Field Operations Command",
    desc: "On-site parcel mapping, GIS polygon surveys & inspection logs",
    category: "field",
  },
];

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth, isAuthenticated, user, logout } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [selectedUser, setSelectedUser] = useState<string>("admin");

  // If local storage has corrupt state (authenticated but no user), clear it
  useEffect(() => {
    if (isAuthenticated && !user) {
      logout();
    }
  }, [isAuthenticated, user, logout]);

  // Safe redirect if already authenticated with valid user
  if (isAuthenticated && user) {
    return <Navigate to="/dashboard" replace />;
  }

  const from = (location.state as { from?: { pathname: string } })?.from
    ?.pathname || "/dashboard";

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  const handleDemoFill = (username: string, pass: string) => {
    setValue("username", username, { shouldValidate: true });
    setValue("password", pass, { shouldValidate: true });
    setError(null);
  };

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await login(data);
      setAuth(response.user, response.access_token, response.refresh_token);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: { detail?: string | { message?: string } } };
        message?: string;
      };
      const detail = axiosErr?.response?.data?.detail;
      const errorMsg =
        typeof detail === "string"
          ? detail
          : detail?.message ||
            (axiosErr?.message && !axiosErr.message.includes("401") ? axiosErr.message : "Invalid credentials. Please try again.");
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left Panel — Hero ────────────────────── */}
      <div
        className="hidden lg:flex lg:w-[55%] relative overflow-hidden bg-[#D47A22] text-white"
        style={{ backgroundColor: "#D47A22" }}
      >
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
            {/* Large Prominent Emblem Logo Above Text */}
            <div className="mb-8 p-4 bg-white rounded-3xl shadow-2xl border-2 border-white/40 inline-block w-fit max-w-[380px]">
              <img
                src="/logo-bhoomisetu.jpeg"
                alt="BhoomiSetu"
                className="h-28 sm:h-36 w-auto object-contain rounded-2xl drop-shadow-md"
              />
            </div>

            <h2 className="text-4xl xl:text-5xl font-bold leading-tight mb-6 text-white drop-shadow-sm">
              National Land
              <br />
              Acquisition
              <br />
              Command
            </h2>
            <p className="text-lg text-white/90 leading-relaxed font-normal">
              Secure, centralized operational control for critical infrastructure
              and parcel monitoring workflows.
            </p>
          </div>

          <div className="flex items-center gap-3 pt-8 border-t border-white/20">
            <ShieldCheck className="w-5 h-5 text-white/80" />
            <span className="text-xs font-semibold text-white/80 uppercase tracking-widest">
              Gov-Grade Encryption Enabled
            </span>
          </div>
        </div>
      </div>

      {/* ── Right Panel — Login Form ─────────────── */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8 md:p-12 bg-brand-linen min-h-screen overflow-y-auto">
        <div className="w-full max-w-md my-auto">
          {/* Header without duplicate logo above credentials */}
          <div className="mb-6 sm:mb-8 text-center sm:text-left">
            {/* Mobile-only compact logo fallback when left panel is hidden */}
            <div className="lg:hidden mb-4 p-2.5 sm:p-3 bg-white rounded-2xl shadow-md border border-gray-200 inline-block mx-auto">
              <img
                src="/logo-bhoomisetu.jpeg"
                alt="BhoomiSetu"
                className="h-14 sm:h-16 w-auto object-contain"
              />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
              Sign In to Dashboard
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">
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
                    "focus:outline-none focus:ring-2 focus:ring-[#D47A22]/30 focus:border-[#D47A22]",
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
                    "focus:outline-none focus:ring-2 focus:ring-[#D47A22]/30 focus:border-[#D47A22]",
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
                className="text-xs font-semibold text-[#D47A22] hover:text-[#B56315] transition-colors"
              >
                Forgot Password?
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "w-full flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 shadow-md",
                "bg-[#D47A22] hover:bg-[#B56315] active:scale-[0.98]",
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

          {/* Demo Credentials (visible by default for rapid testing; disable with VITE_USE_MOCKS=false) */}
          {import.meta.env.VITE_USE_MOCKS !== "false" && (
            <div className="mt-6 p-4 bg-amber-500/5 border border-amber-500/20 rounded-2xl shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 mb-3">
                <p className="text-[11px] text-[#D47A22] font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Quick Demo Logins (Select Persona)
                </p>
                <span className="text-[10px] font-medium text-gray-500 bg-amber-100/60 px-2 py-0.5 rounded-md self-start sm:self-auto">
                  Password: password123
                </span>
              </div>
              {/* Category Filter Pills (Original Amber/White Theme) */}
              <div className="flex items-center gap-1.5 mb-2.5 overflow-x-auto pb-1">
                {[
                  { key: "all", label: "All Roles (10)" },
                  { key: "national", label: "National (2)" },
                  { key: "state", label: "State (3)" },
                  { key: "district", label: "District (3)" },
                  { key: "field", label: "Field & Agency (2)" },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveCategory(tab.key)}
                    className={cn(
                      "px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer whitespace-nowrap",
                      activeCategory === tab.key
                        ? "bg-[#D47A22] text-white shadow-xs"
                        : "bg-white text-gray-600 hover:text-gray-900 border border-gray-200/80 hover:bg-amber-50/50"
                    )}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Demo Persona Cards */}
              <div className="grid grid-cols-1 gap-2 max-h-[260px] overflow-y-auto pr-1">
                {(activeCategory === "all"
                  ? ALL_DEMO_PERSONAS
                  : ALL_DEMO_PERSONAS.filter((p) => p.category === activeCategory)
                ).map(({ user, roleBadge, label, sublabel, desc }) => (
                  <button
                    key={user}
                    type="button"
                    onClick={() => {
                      setSelectedUser(user);
                      handleDemoFill(user, "password123");
                    }}
                    className={cn(
                      "text-left p-3 rounded-xl border shadow-sm hover:shadow transition-all group relative cursor-pointer",
                      selectedUser === user
                        ? "border-[#D47A22] bg-amber-50/80 ring-1 ring-[#D47A22]"
                        : "border-gray-200/90 bg-white hover:bg-amber-50/60 hover:border-[#D47A22]"
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span
                          className={cn(
                            "font-bold text-xs transition-colors",
                            selectedUser === user
                              ? "text-[#D47A22]"
                              : "text-gray-900 group-hover:text-[#D47A22]"
                          )}
                        >
                          {label}
                        </span>
                        <span className="text-[10px] text-gray-500 hidden sm:inline truncate">
                          — {sublabel}
                        </span>
                      </div>
                      <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded-full bg-amber-100 text-[#B56315] border border-amber-200/80 flex-shrink-0">
                        {roleBadge}
                      </span>
                    </div>
                    <span className="block text-[11px] text-gray-500 mt-1 line-clamp-1">
                      {desc}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
