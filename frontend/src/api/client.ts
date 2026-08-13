import axios from "axios";
import { retrieveRawInitData } from "@telegram-apps/sdk";
import type { GameId, GameProfile, MatchPage, Party, PartyCreate, PartyRequest, PlayerDetails, Profile, ProfileUpdate, SearchPreferences, Statistics, SwipeResult, UserProfile } from "../types/api";

function initData(): string {
  try { return retrieveRawInitData() ?? ""; } catch { return ""; }
}

export const api = axios.create({ baseURL: "/api", timeout: 15_000 });
api.interceptors.request.use((config) => {
  config.headers.set("X-Telegram-Init-Data", initData());
  return config;
});

export const endpoints = {
  me: () => api.get<UserProfile>("/me").then(r=>r.data),
  updateMe: (data: Omit<UserProfile,"id"|"user_id"|"faceit_connected">) => api.patch<UserProfile>("/me",data).then(r=>r.data),
  gameProfiles: () => api.get<GameProfile[]>("/game-profiles").then(r=>r.data),
  putGameProfile: (game:GameId,data:Omit<GameProfile,"id"|"game">) => api.put<GameProfile>(`/game-profiles/${game}`,data).then(r=>r.data),
  discoverParties: (game:GameId, params:Record<string,unknown>) => api.get<{items:Party[]}>("/parties/discover",{params:{game,...params}}).then(r=>r.data.items),
  createParty: (data:PartyCreate) => api.post<Party>("/parties",data).then(r=>r.data),
  myParties: () => api.get<{items:Party[]}>("/parties/mine").then(r=>r.data.items),
  party: (id:number) => api.get<Party>(`/parties/${id}`).then(r=>r.data),
  requestParty: (id:number) => api.post<PartyRequest>(`/parties/${id}/requests`).then(r=>r.data),
  partyRequests: () => api.get<PartyRequest[]>("/party-requests/inbox").then(r=>r.data),
  acceptRequest: (id:number) => api.post(`/party-requests/${id}/accept`).then(r=>r.data),
  rejectRequest: (id:number) => api.post(`/party-requests/${id}/reject`).then(r=>r.data),
  cancelRequest: (id:number) => api.post(`/party-requests/${id}/cancel`).then(r=>r.data),
  closeParty: (id:number) => api.post(`/parties/${id}/close`).then(r=>r.data),
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
