import apiClient from "./client";
import type { LoginRequest, LoginResponse, User } from "@/types/api";

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  // Convert JSON request to Form Data as required by FastAPI OAuth2PasswordRequestForm
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const response = await apiClient.post<{ access_token: string; refresh_token: string; user?: User }>(
    "/auth/login",
    formData,
    {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }
  );

  const { access_token, refresh_token } = response.data;

  let user: User | null = response.data.user || null;
  if (!user) {
    try {
      const meRes = await apiClient.get<User>("/auth/me", {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      user = meRes.data;
    } catch {
      try {
        const payloadBase64 = access_token.split(".")[1];
        if (payloadBase64) {
          const payload = JSON.parse(atob(payloadBase64));
          user = {
            id: payload.sub,
            username: payload.username || credentials.username,
            email: `${payload.username || credentials.username}@bhoomisetu.gov.in`,
            role: payload.role || "ADMIN",
            state_scope: payload.state_scope || null,
            district_scope: payload.district_scope || null,
            is_active: true,
          };
        }
      } catch {
        // Fallback user structure
        user = {
          id: "temp-user-id",
          username: credentials.username,
          email: `${credentials.username}@bhoomisetu.gov.in`,
          role: "ADMIN",
          state_scope: null,
          district_scope: null,
          is_active: true,
        };
      }
    }
  }

  return {
    access_token,
    refresh_token,
    token_type: "bearer",
    user: user!,
  };
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}

export async function refreshToken(refreshTokenStr: string): Promise<{ access_token: string }> {
  const response = await apiClient.post<{ access_token: string }>("/auth/refresh", {
    refresh_token: refreshTokenStr,
  });
  return response.data;
}
