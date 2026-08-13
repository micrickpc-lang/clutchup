import axios from "axios";
import { retrieveRawInitData } from "@telegram-apps/sdk";
import type { MatchPage, PlayerDetails, Profile, ProfileUpdate, SearchPreferences, Statistics, SwipeResult } from "../types/api";

function initData(): string {
  try { return retrieveRawInitData() ?? ""; } catch { return ""; }
}

export const api = axios.create({ baseURL: "/api", timeout: 15_000 });
api.interceptors.request.use((config) => {
  config.headers.set("X-Telegram-Init-Data", initData());
  return config;
});

export const endpoints = {
  profile: (signal?: AbortSignal) => api.get<Profile | null>("/profile/me", { signal }).then((r) => r.data),
  updateProfile: (data: ProfileUpdate) => api.patch<Profile>("/profile/me", data).then((r) => r.data),
  nextCard: (signal?: AbortSignal) => api.get<PlayerDetails | null>("/cards/next", { signal }).then((r) => r.data),
  swipe: (target_user_id: number, direction: "like" | "dislike") => api.post<SwipeResult>("/swipe", { target_user_id, direction }).then((r) => r.data),
  player: (id: number, signal?: AbortSignal) => api.get<PlayerDetails>(`/players/${id}`, { signal }).then((r) => r.data),
  matches: (page = 1, signal?: AbortSignal) => api.get<MatchPage>("/matches", { params: { page }, signal }).then((r) => r.data),
  preferences: (signal?: AbortSignal) => api.get<SearchPreferences>("/preferences", { signal }).then((r) => r.data),
  updatePreferences: (data: SearchPreferences) => api.put<SearchPreferences>("/preferences", data).then((r) => r.data),
  statistics: (signal?: AbortSignal) => api.get<Statistics>("/statistics/me", { signal }).then((r) => r.data),
  heartbeat: () => api.post("/presence"),
  oauthStart: () => api.post<{ authorization_url: string }>("/faceit/oauth/start").then((r) => r.data),
};

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (error.code === "ERR_CANCELED") return "";
    return error.response ? `Ошибка сервера (${error.response.status})` : "Нет соединения с сервером";
  }
  return "Произошла неизвестная ошибка";
}
