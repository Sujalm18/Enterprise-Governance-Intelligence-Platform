import axios, { type AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";
import { API_BASE_URL } from "@/lib/config";
import type { ApiErrorPayload } from "@/types/api";

export class ApiError extends Error {
  status?: number;
  payload?: ApiErrorPayload;

  constructor(message: string, status?: number, payload?: ApiErrorPayload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

function getErrorMessage(error: AxiosError<ApiErrorPayload>): string {
  const payload = error.response?.data;
  if (typeof payload?.detail === "string") {
    return payload.detail;
  }
  if (typeof payload?.message === "string") {
    return payload.message;
  }
  if (error.message) {
    return error.message;
  }
  return "API request failed.";
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: normalizeBaseUrl(API_BASE_URL),
  timeout: 60_000,
  headers: {
    Accept: "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorPayload>) => {
    throw new ApiError(
      getErrorMessage(error),
      error.response?.status,
      error.response?.data,
    );
  },
);

export async function request<TResponse>(
  config: AxiosRequestConfig,
): Promise<TResponse> {
  const response = await apiClient.request<TResponse>(config);
  return response.data;
}
