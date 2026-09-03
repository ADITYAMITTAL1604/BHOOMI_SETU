import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, UserRole } from "@/types/api";

interface AuthState {
  // State
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  // Actions
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  logout: () => void;

  // Role helpers
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (...roles: UserRole[]) => boolean;
  canAccessState: (state: string) => boolean;
  canAccessDistrict: (state: string, district: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setAuth: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),

      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),

      hasRole: (role) => get().user?.role === role,

      hasAnyRole: (...roles) => {
        const userRole = get().user?.role;
        return userRole ? roles.includes(userRole) : false;
      },

      canAccessState: (state) => {
        const user = get().user;
        if (!user) return false;
        // CENTRAL and ADMIN can see everything
        if (user.role === "CENTRAL" || user.role === "ADMIN") return true;
        // Others must match their state scope
        return user.state_scope === state;
      },

      canAccessDistrict: (state, district) => {
        const user = get().user;
        if (!user) return false;
        if (user.role === "CENTRAL" || user.role === "ADMIN") return true;
        if (user.state_scope !== state) return false;
        if (user.role === "STATE") return true; // State-level sees all districts
        return user.district_scope === district;
      },
    }),
    {
      name: "bhoomisetu-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
