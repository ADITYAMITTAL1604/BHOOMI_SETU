import apiClient from "./client";
import type { LoginRequest, LoginResponse, User } from "@/types/api";

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  // Convert JSON request to Form Data as required by FastAPI OAuth2PasswordRequestForm
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const response = await apiClient.post<LoginResponse>("/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return response.data;
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
