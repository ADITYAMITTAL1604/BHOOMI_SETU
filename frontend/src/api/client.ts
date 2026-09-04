import axios from "axios";
import { useAuthStore } from "@/store/authStore";

const rawBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const cleanBase = rawBase.replace(/\/+$/, "");
const API_BASE_URL = cleanBase.endsWith("/api/v1") ? cleanBase : `${cleanBase}/api/v1`;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Attach JWT bearer token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export default apiClient;
